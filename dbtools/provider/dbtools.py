from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from tools.mysql_query import MySQLQueryTool
from tools.redis_query import RedisQueryTool


class DbtoolsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # Initialize all tool classes to ensure they are available
            MySQLQueryTool()
            RedisQueryTool()
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
