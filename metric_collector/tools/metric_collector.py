import paramiko
import time
from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class MetricCollectorTool(Tool):
    # 而不是 MetricTermTool
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        host = tool_parameters.get('host')
        port = int(tool_parameters.get('port', 22))
        username = tool_parameters.get('username')
        password = tool_parameters.get('password')
        metric_type = tool_parameters.get('metric_type', 'all')
        output_format = tool_parameters.get('output_format', 'text')

        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=5,  
                banner_timeout=5  
            )

            metrics = self.collect_metrics(ssh_client, metric_type)

            ssh_client.close()

            if output_format == 'json':
                yield self.create_json_message(metrics)
            else:
                formatted_text = self.format_metrics_text(metrics, metric_type)
                yield self.create_text_message(formatted_text)

        except Exception as e:
            error_message = f"Error connecting or collecting metrics: {str(e)}"
            yield self.create_text_message(error_message)

    def run_command(self, ssh_client, command):
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=5) 
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        if error:
            return f"Error: {error}"
        return output

    def get_cpu_metrics(self, ssh_client):
        command = "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'"
        cpu_usage = self.run_command(ssh_client, command).strip()

        cpu_cores_command = "nproc"
        cpu_cores = self.run_command(ssh_client, cpu_cores_command).strip()

        cpu_model_command = "grep 'model name' /proc/cpuinfo | head -1 | sed 's/model name[[:space:]]*: //'"
        cpu_model = self.run_command(ssh_client, cpu_model_command).strip()

        load_avg_command = "cat /proc/loadavg"
        load_avg = self.run_command(ssh_client, load_avg_command).strip().split()[:3]

        try:
            usage_percent = float(cpu_usage) if cpu_usage and not cpu_usage.startswith("Error:") else 0.0
        except ValueError:
            usage_percent = 0.0

        return {
            "usage_percent": usage_percent,
            "cores": int(cpu_cores) if cpu_cores.isdigit() else 0,
            "model": cpu_model,
            "load_avg": {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            }
        }

    def get_memory_metrics(self, ssh_client):
        command = "free -m | grep 'Mem:'"
        mem_output = self.run_command(ssh_client, command)

        mem_values = mem_output.split()
        if len(mem_values) >= 7:
            total = int(mem_values[1])
            used = int(mem_values[2])
            free = int(mem_values[3])
            shared = int(mem_values[4])
            cache = int(mem_values[5])
            available = int(mem_values[6])

            usage_percent = (used / total) * 100 if total > 0 else 0

            return {
                "total": f"{total} MB",
                "used": f"{used} MB",
                "free": f"{free} MB",
                "shared": f"{shared} MB",
                "cache": f"{cache} MB",
                "available": f"{available} MB",
                "usage_percent": f"{round(usage_percent, 2)}%"
            }
        return {"error": "Failed to parse memory information"}

    def get_disk_metrics(self, ssh_client):
        command = "df -h | grep -v 'tmpfs\\|udev'"
        disk_output = self.run_command(ssh_client, command)

        filesystems = []
        for line in disk_output.strip().split('\n'):
            if line.startswith('Filesystem'):
                continue
            parts = line.split()
            if len(parts) >= 6:
                filesystems.append({
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use_percent": parts[4],
                    "mounted_on": parts[5]
                })

        io_stats = []
        io_command = "iostat -d -x | grep -v 'Linux\\|Device\\|^$'"
        io_output = self.run_command(ssh_client, io_command)

        for line in io_output.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 6:
                io_stats.append({
                    "device": parts[0],
                    "r/s": parts[3],
                    "w/s": parts[4],
                    "util": parts[-1]
                })

        return {
            "filesystems": filesystems,
            "io_stats": io_stats
        }

    def get_network_metrics(self, ssh_client):
        command = "cat /proc/net/dev | grep -v 'Inter\\|face\\|lo:'"
        net_output = self.run_command(ssh_client, command)

        interfaces = []
        for line in net_output.strip().split('\n'):
            parts = line.split(':')
            if len(parts) >= 2:
                interface = parts[0].strip()
                stats = parts[1].strip().split()
                if len(stats) >= 16:
                    rx_bytes = int(stats[0])
                    tx_bytes = int(stats[8])
                    interfaces.append({
                        "interface": interface,
                        "rx": {
                            "bytes": rx_bytes,
                            "bytes_human": f"{rx_bytes / 1024 / 1024:.2f} MB",
                            "packets": int(stats[1]),
                            "errors": int(stats[2]),
                            "dropped": int(stats[3])
                        },
                        "tx": {
                            "bytes": tx_bytes,
                            "bytes_human": f"{tx_bytes / 1024 / 1024:.2f} MB",
                            "packets": int(stats[9]),
                            "errors": int(stats[10]),
                            "dropped": int(stats[11])
                        }
                    })

        conn_command = "netstat -ant | wc -l"
        conn_count = self.run_command(ssh_client, conn_command).strip()

        return {
            "interfaces": interfaces,
            "connection_count": int(conn_count) if conn_count.isdigit() else 0
        }

    def get_process_metrics(self, ssh_client):
        process_count_command = "ps aux | wc -l"
        process_count = self.run_command(ssh_client, process_count_command).strip()
        top_cpu_command = (
            "ps aux --sort=-%cpu | head -6 | tail -n 5 | "
            "awk '{printf \"%s\\t%s\\t%s\\t%s\\t%s\\t%s\\n\", $1,$2,$3,$4,$6,$11}'"
        )
        top_cpu_output = self.run_command(ssh_client, top_cpu_command)

        top_mem_command = (
            "ps aux --sort=-%mem | head -6 | tail -n 5 | "
            "awk '{printf \"%s\\t%s\\t%s\\t%s\\t%s\\t%s\\n\", $1,$2,$3,$4,$6,$11}'"
        )
        top_mem_output = self.run_command(ssh_client, top_mem_command)

        def parse_process_line(line):
            if not line.strip():
                return None
            parts = line.strip().split('\t')
            if len(parts) >= 6:
                return {
                    "user": parts[0],
                    "pid": int(parts[1]),
                    "cpu_percent": float(parts[2]),
                    "mem_percent": float(parts[3]),
                    "rss": int(parts[4]),
                    "command": parts[5]
                }
            return None

        top_cpu_processes = []
        for line in top_cpu_output.strip().split('\n'):
            process = parse_process_line(line)
            if process:
                top_cpu_processes.append(process)

        top_memory_processes = []
        for line in top_mem_output.strip().split('\n'):
            process = parse_process_line(line)
            if process:
                top_memory_processes.append(process)

        return {
            "total_processes": int(process_count) - 1 if process_count.isdigit() else 0,
            "top_cpu_processes": top_cpu_processes,
            "top_memory_processes": top_memory_processes
        }

    def collect_metrics(self, ssh_client, metric_type):
        metrics = {
            "timestamp": time.time(),
        }

        if metric_type == "all" or metric_type == "cpu":
            metrics["cpu"] = self.get_cpu_metrics(ssh_client)

        if metric_type == "all" or metric_type == "memory":
            metrics["memory"] = self.get_memory_metrics(ssh_client)

        if metric_type == "all" or metric_type == "disk":
            metrics["disk"] = self.get_disk_metrics(ssh_client)

        if metric_type == "all" or metric_type == "network":
            metrics["network"] = self.get_network_metrics(ssh_client)

        if metric_type == "all" or metric_type == "process":
            metrics["process"] = self.get_process_metrics(ssh_client)

        return metrics

    def format_metrics_text(self, metrics, metric_type):
        output = []

        if metric_type == "all" or metric_type == "cpu":
            if "cpu" in metrics:
                cpu = metrics['cpu']
                output.append("=== CPU 指标 ===")
                output.append(f"CPU 使用率: {cpu['usage_percent']:.1f}%")
                output.append(f"CPU 核心数: {cpu['cores']}")
                output.append(f"CPU 型号: {cpu['model']}")
                output.append(
                    f"负载平均值: {cpu['load_avg']['1min']} {cpu['load_avg']['5min']} {cpu['load_avg']['15min']}")
                output.append("")

        if metric_type == "all" or metric_type == "memory":
            if "memory" in metrics:
                mem = metrics['memory']
                output.append("=== 内存指标 ===")
                output.append(f"总内存: {mem['total']}")
                output.append(f"已用内存: {mem['used']} ({mem['usage_percent']})")
                output.append(f"可用内存: {mem['available']}")
                output.append("")

        if metric_type == "all" or metric_type == "disk":
            if "disk" in metrics:
                output.append("=== 磁盘指标 ===")
                for fs in metrics['disk']['filesystems']:
                    output.append(f"文件系统: {fs['filesystem']}")
                    mount_point = fs['mounted_on']
                    if len(mount_point) > 50:
                        mount_point = mount_point[:47] + "..."
                    output.append(f"  挂载点: {mount_point}")
                    output.append(f"  总大小: {fs['size']}")
                    output.append(f"  已使用: {fs['used']} ({fs['use_percent']})")
                    output.append(f"  可用: {fs['available']}")
                    output.append("")

        if metric_type == "all" or metric_type == "network":
            if "network" in metrics:
                output.append("=== 网络指标 ===")
                output.append(f"活动连接数: {metrics['network']['connection_count']}")
                for iface in metrics['network']['interfaces']:
                    output.append(f"接口: {iface['interface']}")
                    output.append(f"  接收: {iface['rx']['bytes_human']} ({iface['rx']['packets']} 包)")
                    output.append(f"  发送: {iface['tx']['bytes_human']} ({iface['tx']['packets']} 包)")
                    output.append("")

        if metric_type == "all" or metric_type == "process":
            if "process" in metrics:
                output.append("=== 进程指标 ===")
                output.append(f"总进程数: {metrics['process']['total_processes']}")

                if "top_cpu_processes" in metrics['process'] and metrics['process']['top_cpu_processes']:
                    output.append("\nCPU占用最高的进程:")
                    output.append("USER         PID %CPU %MEM   RSS COMMAND")
                    for proc in metrics['process']['top_cpu_processes']:
                        output.append(
                            f"{proc['user']:<12} {proc['pid']:<5} {proc['cpu_percent']:<4} {proc['mem_percent']:<4} {proc['rss']:<6} {proc['command']}")

                if "top_memory_processes" in metrics['process'] and metrics['process']['top_memory_processes']:
                    output.append("\n内存占用最高的进程:")
                    output.append("USER         PID %CPU %MEM   RSS COMMAND")
                    for proc in metrics['process']['top_memory_processes']:
                        output.append(
                            f"{proc['user']:<12} {proc['pid']:<5} {proc['cpu_percent']:<4} {proc['mem_percent']:<4} {proc['rss']:<6} {proc['command']}")

        return "\n".join(output)
