from collections.abc import Generator
from typing import Any, Dict, Tuple
import re

import redis

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class RedisQueryTool(Tool):
    """Redis Database Query Tool
    
    Provides functionality to query Redis database, supporting various data types and pattern matching
    """
    
    def _check_key_pattern_safety(self, key_pattern: str) -> Tuple[bool, str]:
        """
        Check the safety and correctness of Redis key patterns
        
        Args:
            key_pattern: Redis key pattern
            
        Returns:
            Tuple[bool, str]: (is_safe, safety_message_or_error)
        """
        # Check for dangerous operations
        dangerous_operations = []
        
        # Check for global wildcard usage, which may match a large number of keys
        if key_pattern == '*':
            dangerous_operations.append("Using global wildcard '*' will match all keys, potentially causing performance issues or returning large amounts of data")
        
        # Check for system key prefixes
        if key_pattern.startswith(('__', 'system:', 'redis:')):
            dangerous_operations.append("Query may involve system keys, which could affect Redis internal structures")
        
        # Check for overly broad patterns (such as a single character plus wildcard)
        if len(key_pattern.replace('*', '')) <= 1 and '*' in key_pattern:
            dangerous_operations.append("Key pattern is too broad, may match a large number of keys")
        
        # Check for invalid wildcard usage
        if '**' in key_pattern or '?' in key_pattern:
            dangerous_operations.append("Key pattern contains invalid wildcard usage, Redis only supports single '*' as wildcard")
        
        if dangerous_operations:
            warning_message = "Redis key pattern has the following risks:\n- " + "\n- ".join(dangerous_operations)
            return False, warning_message
        
        return True, "Redis key pattern check passed, no obvious risks detected"
    
    def _invoke(
            self,
            tool_parameters: Dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Execute Redis query and return results
        
        Args:
            tool_parameters: Dictionary containing connection info and query parameters
        
        Returns:
            Generator yielding query results
        """
        client = None
        
        try:
            # Get parameters
            host = tool_parameters.get('host')
            port = tool_parameters.get('port')
            password = tool_parameters.get('password')  # Optional parameter
            db = tool_parameters.get('db', 0)  # Default to database 0
            key = tool_parameters.get('key')
            
            # Parameter validation
            if not all([host, port, key]):
                missing_params = [param for param in ['host', 'port', 'key'] 
                                 if not tool_parameters.get(param)]
                yield self.create_text_message(text=f"Missing required parameters: {', '.join(missing_params)}")
                return

            # Check key pattern safety
            is_safe, safety_message = self._check_key_pattern_safety(key)
            if not is_safe:
                yield self.create_text_message(text=f"Redis key pattern safety check failed:\n{safety_message}\n\nPlease modify the key pattern and try again, or confirm the risks and continue.")
                return
                
            # Connect to Redis
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=True  # Automatically decode responses to strings
            )

            # Check if key contains wildcards
            if '*' in key:
                # Use scan_iter to get matching keys
                matched_keys = list(client.scan_iter(match=key))
                results = []
                for matched_key in matched_keys:
                    key_type = client.type(matched_key)
                    value = self._get_value_by_type(client, matched_key, key_type)
                    results.append({
                        "key": matched_key,
                        "type": key_type,
                        "value": value
                    })
                rows = len(results)
            else:
                # Get value for a single key
                if not client.exists(key):
                    yield self.create_text_message(text=f"Key not found: {key}")
                    return

                key_type = client.type(key)
                value = self._get_value_by_type(client, key, key_type)
                results = [{
                    "key": key,
                    "type": key_type,
                    "value": value
                }]
                rows = 1

            # Construct response
            response = {
                "rows_affected": rows,
                "data": results,
                "status": "success"
            }

            yield self.create_json_message(response)

        except redis.RedisError as e:
            yield self.create_text_message(text=f"Redis error: {str(e)}")
        except KeyError as ke:
            yield self.create_text_message(text=f"Missing required parameter: {ke}")
        except Exception as e:
            yield self.create_text_message(text=f"An error occurred: {str(e)}")
        finally:
            if client:
                client.close()

    def _get_value_by_type(self, client: redis.Redis, key: str, key_type: str) -> Any:
        """
        Get value based on Redis key type
        
        Args:
            client: Redis client instance
            key: Redis key
            key_type: Type of the Redis key
            
        Returns:
            Value corresponding to the key and its type
        """
        if key_type == 'string':
            return client.get(key)
        elif key_type == 'list':
            return client.lrange(key, 0, -1)
        elif key_type == 'set':
            return list(client.smembers(key))
        elif key_type == 'zset':
            return client.zrange(key, 0, -1, withscores=True)
        elif key_type == 'hash':
            return client.hgetall(key)
        else:
            return None
