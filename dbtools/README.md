# Database Tools Plugin for Dify

The Database Tools plugin is a database query tool that supports MySQL and Redis databases. It provides unified query interfaces and result formats, making data retrieval and management simple and efficient.

## Features

- **Multiple Database Support**: One plugin supports both MySQL and Redis databases
- **Unified Interface**: All databases use similar parameter structures and return formats
- **Comprehensive Error Handling**: Provides detailed error information and exception handling
- **Secure Connection**: Supports password encryption storage
- **Internationalization**: Provides interfaces in English, Chinese, Japanese, and Portuguese

## Supported Databases

### 1. MySQL
- Supports standard SQL query statements
- Returns affected rows and query results
- Supports all MySQL data types

### 2. Redis
- Supports all Redis data types:
  - String
  - List
  - Set
  - Sorted Set
  - Hash
- Supports key name pattern matching with wildcards

## Usage

### 1. MySQL Query
```json
{
    "host": "localhost",
    "port": 3306,
    "database": "your_database",
    "username": "your_username",
    "password": "your_password",
    "query": "SELECT * FROM users WHERE age > 18"
}
```

### 2. Redis Query
```json
{
    "host": "localhost",
    "port": 6379,
    "password": "your_password",
    "db": 0,
    "key": "user:*"
}
```

## Result Format

All database queries return results in a unified format:

```json
{
    "rows_affected": 10,
    "data": [...],
    "status": "success"
}
```

## Installation Requirements

- Python 3.8+
- mysql-connector-python
- redis

## Security Considerations

- All database connection information should be properly secured
- It is recommended to use read-only accounts for query operations
- Avoid performing modification or deletion operations in production environments

## License

MIT
