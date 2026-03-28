#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日常巡检脚本
功能：
1. 系统状态检查
2. 磁盘空间检查
3. 内存使用检查
4. CPU使用检查
5. 网络连接检查
6. 服务状态检查
7. 日志检查
8. 安全检查
"""

import os
import sys
import platform
import psutil
import socket
import datetime
import subprocess
import re

class DailyInspection:
    def __init__(self):
        self.results = []
        self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def log(self, message, level="INFO"):
        """记录日志"""
        log_entry = f"[{self.timestamp}] [{level}] {message}"
        self.results.append(log_entry)
        print(log_entry)
    
    def check_system_status(self):
        """检查系统状态"""
        self.log("=== 系统状态检查 ===")
        
        # 系统信息
        os_info = platform.uname()
        self.log(f"系统: {os_info.system} {os_info.release} {os_info.version}")
        self.log(f"主机名: {os_info.node}")
        self.log(f"架构: {os_info.machine}")
        
        # 启动时间
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        self.log(f"启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"运行时间: {uptime.days}天 {uptime.seconds//3600}小时 {(uptime.seconds%3600)//60}分钟")
    
    def check_disk_space(self):
        """检查磁盘空间"""
        self.log("=== 磁盘空间检查 ===")
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                percent = usage.percent
                status = "正常" if percent < 80 else "警告" if percent < 90 else "危险"
                self.log(f"分区: {partition.mountpoint} 总空间: {usage.total//(1024*1024*1024)}GB "
                       f"已用: {usage.used//(1024*1024*1024)}GB 可用: {usage.free//(1024*1024*1024)}GB "
                       f"使用率: {percent}% 状态: {status}")
            except Exception as e:
                self.log(f"检查分区 {partition.mountpoint} 时出错: {e}", "ERROR")
    
    def check_memory_usage(self):
        """检查内存使用"""
        self.log("=== 内存使用检查 ===")
        
        memory = psutil.virtual_memory()
        percent = memory.percent
        status = "正常" if percent < 80 else "警告" if percent < 90 else "危险"
        self.log(f"总内存: {memory.total//(1024*1024*1024)}GB "
               f"已用: {memory.used//(1024*1024*1024)}GB "
               f"可用: {memory.available//(1024*1024*1024)}GB "
               f"使用率: {percent}% 状态: {status}")
        
        # 交换空间
        swap = psutil.swap_memory()
        self.log(f"交换空间: 总大小 {swap.total//(1024*1024*1024)}GB "
               f"已用 {swap.used//(1024*1024*1024)}GB "
               f"可用 {swap.free//(1024*1024*1024)}GB "
               f"使用率: {swap.percent}%")
    
    def check_cpu_usage(self):
        """检查CPU使用"""
        self.log("=== CPU使用检查 ===")
        
        cpu_count = psutil.cpu_count(logical=True)
        cpu_percent = psutil.cpu_percent(interval=1)
        status = "正常" if cpu_percent < 80 else "警告" if cpu_percent < 90 else "危险"
        self.log(f"CPU核心数: {cpu_count}")
        self.log(f"CPU使用率: {cpu_percent}% 状态: {status}")
        
        # CPU温度（如果支持）
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                for name, entries in temps.items():
                    for entry in entries:
                        self.log(f"{name}温度: {entry.current}°C (高: {entry.high}°C, 临界: {entry.critical}°C)")
        except Exception as e:
            self.log(f"获取CPU温度时出错: {e}", "INFO")
    
    def check_network(self):
        """检查网络连接"""
        self.log("=== 网络连接检查 ===")
        
        # 网络接口
        net_io = psutil.net_io_counters()
        self.log(f"网络发送: {net_io.bytes_sent//(1024*1024)}MB 接收: {net_io.bytes_recv//(1024*1024)}MB")
        self.log(f"数据包发送: {net_io.packets_sent} 接收: {net_io.packets_recv}")
        self.log(f"错误发送: {net_io.errout} 接收: {net_io.errin}")
        self.log(f"丢包发送: {net_io.dropout} 接收: {net_io.dropin}")
        
        # 网络接口信息
        net_if_addrs = psutil.net_if_addrs()
        for interface, addrs in net_if_addrs.items():
            self.log(f"接口: {interface}")
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    self.log(f"  IPv4: {addr.address} 子网掩码: {addr.netmask}")
                elif addr.family == socket.AF_INET6:
                    self.log(f"  IPv6: {addr.address}")
        
        # 网络连接数
        connections = psutil.net_connections()
        tcp_connections = [c for c in connections if c.status == 'ESTABLISHED']
        self.log(f"活跃TCP连接数: {len(tcp_connections)}")
    
    def check_services(self):
        """检查服务状态"""
        self.log("=== 服务状态检查 ===")
        
        if platform.system() == "Windows":
            # Windows服务检查
            try:
                services = psutil.win_service_iter()
                for service in services:
                    try:
                        service_info = service.as_dict()
                        if service_info['status'] == 'running':
                            self.log(f"服务: {service_info['display_name']} 状态: {service_info['status']}")
                    except Exception as e:
                        pass
            except Exception as e:
                self.log(f"检查Windows服务时出错: {e}", "ERROR")
        else:
            # Linux服务检查
            try:
                output = subprocess.check_output(["systemctl", "list-units", "--type=service", "--state=running"], 
                                              universal_newlines=True)
                lines = output.strip().split('\n')[1:-1]  # 跳过表头和脚注
                for line in lines:
                    if line:
                        parts = line.split()
                        if len(parts) > 0:
                            self.log(f"服务: {parts[0]} 状态: 运行中")
            except Exception as e:
                self.log(f"检查Linux服务时出错: {e}", "ERROR")
    
    def check_logs(self):
        """检查日志"""
        self.log("=== 日志检查 ===")
        
        if platform.system() == "Windows":
            # Windows事件日志
            try:
                import win32evtlog
                import win32evtlogutil
                
                server = 'localhost'
                logtype = 'System'
                hand = win32evtlog.OpenEventLog(server, logtype)
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                
                events = []
                while True:
                    events_batch = win32evtlog.ReadEventLog(hand, flags, 0)
                    if not events_batch:
                        break
                    events.extend(events_batch)
                
                # 查找错误和警告
                error_events = [e for e in events if e.EventType in [1, 2]]  # 1=错误, 2=警告
                if error_events:
                    self.log(f"发现 {len(error_events)} 个错误/警告事件")
                    for e in error_events[:5]:  # 只显示最近5个
                        try:
                            msg = win32evtlogutil.SafeFormatMessage(e, logtype)
                            self.log(f"事件ID: {e.EventID} 来源: {e.SourceName} 时间: {e.TimeGenerated}")
                        except:
                            pass
                else:
                    self.log("未发现错误/警告事件")
                    
                win32evtlog.CloseEventLog(hand)
            except Exception as e:
                self.log(f"检查Windows事件日志时出错: {e}", "ERROR")
        else:
            # Linux系统日志
            log_files = ["/var/log/syslog", "/var/log/messages"]
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()[-100:]  # 读取最后100行
                            
                        error_lines = [line for line in lines if 'error' in line.lower() or 'warn' in line.lower()]
                        if error_lines:
                            self.log(f"在 {log_file} 中发现 {len(error_lines)} 个错误/警告")
                            for line in error_lines[-5:]:  # 只显示最近5个
                                self.log(f"  {line.strip()}")
                        else:
                            self.log(f"{log_file} 中未发现错误/警告")
                    except Exception as e:
                        self.log(f"读取 {log_file} 时出错: {e}", "ERROR")
    
    def check_security(self):
        """检查安全状态"""
        self.log("=== 安全检查 ===")
        
        # 检查用户登录
        try:
            if platform.system() == "Windows":
                # Windows登录检查
                output = subprocess.check_output(["net", "user"], universal_newlines=True)
                users = re.findall(r'([a-zA-Z0-9_]+)\s+', output)
                self.log(f"系统用户数: {len(users)}")
                for user in users[:10]:  # 只显示前10个用户
                    self.log(f"用户: {user}")
            else:
                # Linux登录检查
                with open("/etc/passwd", 'r') as f:
                    users = [line.split(':')[0] for line in f if not line.startswith('#')]
                self.log(f"系统用户数: {len(users)}")
                for user in users[:10]:  # 只显示前10个用户
                    self.log(f"用户: {user}")
        except Exception as e:
            self.log(f"检查用户时出错: {e}", "ERROR")
        
        # 检查开放端口
        self.log("开放端口检查:")
        try:
            connections = psutil.net_connections()
            open_ports = set()
            for conn in connections:
                if conn.status == 'LISTEN' and conn.laddr:
                    open_ports.add(conn.laddr[1])
            
            if open_ports:
                self.log(f"开放端口: {sorted(open_ports)}")
            else:
                self.log("未发现开放端口")
        except Exception as e:
            self.log(f"检查开放端口时出错: {e}", "ERROR")
    
    def run_all_checks(self):
        """运行所有检查"""
        self.log("开始日常巡检", "INFO")
        
        try:
            self.check_system_status()
            self.check_disk_space()
            self.check_memory_usage()
            self.check_cpu_usage()
            self.check_network()
            self.check_services()
            self.check_logs()
            self.check_security()
        except Exception as e:
            self.log(f"巡检过程中出错: {e}", "ERROR")
        
        self.log("日常巡检完成", "INFO")
        
        # 保存报告
        self.save_report()
    
    def save_report(self):
        """保存巡检报告"""
        report_filename = f"inspection_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("====================================\n")
                f.write("         日常巡检报告\n")
                f.write("====================================\n")
                f.write(f"巡检时间: {self.timestamp}\n")
                f.write("====================================\n\n")
                
                for line in self.results:
                    f.write(line + "\n")
                
                f.write("\n====================================\n")
                f.write("         报告结束\n")
                f.write("====================================\n")
            
            self.log(f"巡检报告已保存至: {report_filename}")
        except Exception as e:
            self.log(f"保存报告时出错: {e}", "ERROR")

if __name__ == "__main__":
    # 检查依赖
    try:
        import psutil
    except ImportError:
        print("错误: 缺少 psutil 模块，请运行 'pip install psutil' 安装")
        sys.exit(1)
    
    if platform.system() == "Windows":
        try:
            import win32evtlog
            import win32evtlogutil
        except ImportError:
            print("警告: 缺少 pywin32 模块，Windows事件日志检查将被跳过")
    
    # 运行巡检
    inspector = DailyInspection()
    inspector.run_all_checks()
