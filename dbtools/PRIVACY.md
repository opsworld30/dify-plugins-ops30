# Database Tools Plugin Privacy Policy

The Database Tools plugin respects user privacy and handles data with care. Here's what you need to know about data collection and usage:

## Data Collection

1. **Database Connection Information**
   - Host address
   - Port number
   - Database name
   - Username
   - Password

2. **Query Information**
   - SQL queries (MySQL)
   - Redis key patterns

## Data Usage

1. **Database Connection Information**
   - Used solely for establishing connections to specified databases
   - Used for authentication purposes only
   - Not stored or logged anywhere

2. **Query Information**
   - Used only for executing database queries
   - Used to retrieve and return query results
   - Not stored or cached

## Data Security

1. No connection information or queries are stored by the plugin
2. All data transmission occurs within your local network
3. Query results are returned only to the user and not shared with any third parties
4. All sensitive information is handled in memory only and cleared after use

## Third-party Services

This plugin uses the following official database drivers:

1. MySQL: mysql-connector-python
   - Privacy Policy: https://www.mysql.com/about/legal/

2. Redis: redis-py
   - Privacy Policy: https://redis.com/privacy/

These drivers are used solely for database connectivity and query execution. They do not collect or transmit any additional user data.

## Security Measures

- All database connections are properly closed after use
- Error messages are sanitized to prevent sensitive information leakage
- Input validation is performed on all parameters
- Resource cleanup is guaranteed through proper exception handling

For any privacy concerns or questions, please contact the plugin author or raise an issue on the GitHub repository.