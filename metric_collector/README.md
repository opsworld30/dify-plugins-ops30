# SSH Metrics Collector Plugin

SSH Metrics Collector is a powerful plugin designed to collect and monitor system metrics from remote servers via SSH connections.

## Features

- Real-time monitoring of server CPU, memory, disk, and network usage
- Process monitoring with top CPU and memory consumers
- Support for both text and JSON output formats
- Zero-dependency on target servers - requires only SSH access

## Supported Metrics

- **CPU**: Usage percentage, core count, model information, and load averages
- **Memory**: Total, used, free, shared, cached, and available memory with usage percentage
- **Disk**: Filesystem usage statistics and I/O performance metrics
- **Network**: Interface statistics including received/transmitted bytes, packets, errors, and connection count
- **Process**: Total process count and detailed information about top CPU/memory consuming processes

## Requirements

- SSH access to the target server
- Basic Linux commands available on the target server (top, ps, free, df, etc.)

## Usage

Simply provide the SSH connection details (host, port, username, password) and select the metrics you want to collect.



