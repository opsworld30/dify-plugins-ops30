from collections.abc import Generator
from typing import Any, Dict, Tuple
import re

import mysql.connector
from mysql.connector import Error

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class MySQLQueryTool(Tool):
    """MySQL Database Query Tool
    
    Provides functionality to query MySQL database, supporting various SQL query statements
    """
    
    def _check_sql_safety(self, query: str) -> Tuple[bool, str]:
        """
        Check the safety and correctness of SQL statements
        
        Args:
            query: SQL query statement
            
        Returns:
            Tuple[bool, str]: (is_safe, safety_message_or_error)
        """
        # Convert to uppercase for keyword checking
        upper_query = query.upper()
        
        # Check basic syntax
        if not any(upper_query.strip().startswith(keyword) for keyword in 
                  ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE', 'DESC', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE']):
            return False, "Invalid SQL syntax: Must start with a valid SQL keyword"
        
        # Check for dangerous operations
        dangerous_operations = []
        
        # Check for DROP or TRUNCATE operations
        if re.search(r'\b(DROP|TRUNCATE)\b', upper_query):
            dangerous_operations.append("Contains DROP or TRUNCATE operations, which may delete tables or databases")
            
        # Check for ALTER operations
        if re.search(r'\bALTER\b', upper_query):
            dangerous_operations.append("Contains ALTER operations, which may modify table structures")
            
        # Check for UPDATE or DELETE without WHERE conditions
        if re.search(r'\b(UPDATE|DELETE)\b', upper_query) and not re.search(r'\bWHERE\b', upper_query):
            dangerous_operations.append("UPDATE or DELETE operations without WHERE conditions, which may affect all rows")
        
        # Check for comments, possible SQL injection attempts
        if re.search(r'(--|#|/\*)', query):
            dangerous_operations.append("Contains SQL comments, possible SQL injection risk")
        
        # Check for multiple statements (usually separated by semicolons)
        if re.search(r';.*\S', query):
            dangerous_operations.append("Contains multiple SQL statements, possible SQL injection risk")
        
        if dangerous_operations:
            warning_message = "SQL statement has the following risks:\n- " + "\n- ".join(dangerous_operations)
            return False, warning_message
        
        return True, "SQL statement check passed, no obvious risks detected"
    
    def _invoke(
            self,
            tool_parameters: Dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Execute MySQL query and return results
        
        Args:
            tool_parameters: Dictionary containing connection info and query statement
        
        Returns:
            Generator yielding query results
        """
        connection = None
        cursor = None
        
        try:
            # Get parameters
            host = tool_parameters.get('host')
            port = tool_parameters.get('port')
            database = tool_parameters.get('database')
            username = tool_parameters.get('username')
            password = tool_parameters.get('password')
            query = tool_parameters.get('query')
            
            # Parameter validation
            if not all([host, port, database, username, password, query]):
                missing_params = [param for param in ['host', 'port', 'database', 'username', 'password', 'query'] 
                                 if not tool_parameters.get(param)]
                yield self.create_text_message(text=f"Missing required parameters: {', '.join(missing_params)}")
                return

            # Check SQL statement safety
            is_safe, safety_message = self._check_sql_safety(query)
            if not is_safe:
                yield self.create_text_message(text=f"SQL safety check failed:\n{safety_message}\n\nPlease modify your SQL statement or confirm the risks before proceeding.")
                return
                
            # Connect to database
            connection = mysql.connector.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )

            if connection.is_connected():
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query)

                # Determine query type and handle results accordingly
                if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'DESC')):
                    # For queries that return data
                    results = cursor.fetchall()
                    rows = len(results)
                else:
                    # For INSERT, UPDATE, DELETE queries
                    connection.commit()
                    rows = cursor.rowcount
                    results = []

                # Construct response
                response = {
                    "rows_affected": rows,
                    "data": results,
                    "status": "success",
                    "query_type": "read" if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'DESC')) else "write"
                }

                yield self.create_json_message(response)
            else:
                yield self.create_text_message(text="Failed to connect to the database")

        except Error as e:
            yield self.create_text_message(text=f"Database error: {str(e)}")
        except KeyError as ke:
            yield self.create_text_message(text=f"Missing required parameter: {ke}")
        except Exception as e:
            yield self.create_text_message(text=f"An error occurred: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
