# Dify Plugins Collection by OpsWorld30

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)

A collection of useful plugins for [Dify](https://dify.ai), designed to enhance your AI applications with database connectivity, notification capabilities, and system monitoring.

## 🚀 Plugins

### 📊 Database Tools (dbtools)

A database query tool that supports MySQL and Redis databases. It provides unified query interfaces and result formats.

**Features:**
- MySQL database querying with SQL
- Redis command execution
- Structured result formatting
- Secure connection handling

### 📱 Lark Notify (lark_notify)

A plugin for sending notification messages to Lark (Feishu) group chats. It supports sending text messages and card messages, allowing you to communicate with your team in a more flexible and visually appealing way.

**Features:**
- Plain text message sending
- Rich interactive card messages
- Customizable message templates
- Error handling and retry mechanisms

### 📈 Metric Collector (metric_collector)

Collect and monitor system metrics from remote servers via SSH connections.

**Features:**
- CPU, memory, disk, and network usage monitoring
- Real-time data collection
- Multiple output formats
- Secure SSH connections

## 📋 Requirements

- Python 3.12+
- Dify AI platform
- Required Python packages (specified in each plugin's requirements.txt)

## 🔧 Installation

These plugins can be installed directly from the Dify plugin marketplace or manually:

1. Clone this repository:
```bash
git clone https://github.com/opsworld30/dify-plugins-ops30.git
```

2. Install the required dependencies for each plugin:
```bash
cd dify-plugins-ops30/dbtools
pip install -r requirements.txt
```

3. Follow the Dify documentation to register and use these plugins in your Dify instance.

## 📖 Usage
Each plugin comes with its own documentation and examples. Please refer to the individual plugin directories for detailed usage instructions.

### Database Tools Example
```yaml
# MySQL Query Example
mysql_query:
    host: "localhost"
    port: "3306"
    database: "mydb"
    username: "user"
    password: "password"
    query: "SELECT * FROM users LIMIT 10"

# Redis Query Example
redis_query:
    host: "localhost"
    port: "6379"
    password: "your_password"  # Optional
    command: "user:1001"
```

### Lark Notify Example
```python
# Text Message Example
lark_text:
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token"
    message: "Server alert: High CPU usage detected"

# Card Message Example
lark_card:
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token"
    title: "System Alert"
    card_content: "CPU usage has exceeded 90%"
    card_type: "warning"  # Available types: info/warning/success/error
```

### Metric Collector Example
```yaml
metric_term:
    host: "192.168.1.100"
    port: 22
    username: "admin"
    password: "secure_password"
    metric_type: "cpu"  # Available types: cpu/memory/disk/network/all
    output_format: "json"  # Available formats: text/json
```

## 🤝 Contributing
Contributions are welcome! If you'd like to add features, fix bugs, or improve documentation:

1. Fork the repository
2. Create your feature branch ( git checkout -b feature/amazing-feature )
3. Commit your changes ( git commit -m 'Add some amazing feature' )
4. Push to the branch ( git push origin feature/amazing-feature )
5. Open a Pull Request
## 📜 License
This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 📞 Contact
OpsWorld30 - GitHub Profile

Project Link: https://github.com/opsworld30/dify-plugins-ops30

## 🙏 Acknowledgements
- Dify.AI for the amazing AI application development platform
- All contributors who have helped shape this project