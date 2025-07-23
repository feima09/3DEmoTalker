"""
后端进程管理模块

该模块负责管理AI数字人后端服务进程的启动、停止和监控。
提供实时日志捕获功能，便于WebUI显示运行状态和输出信息。
"""

import os
import sys
import time
import subprocess
import threading
import psutil
from queue import Queue, Empty
from typing import Optional, List, Dict, Any

# 获取项目根目录
ROOT_PATH = os.getcwd()


class ProcessManager:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.log_queue = Queue()
        self.error_queue = Queue()
        self.should_stop = False
        self.stdout_thread: Optional[threading.Thread] = None
        self.stderr_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.status = "未启动"
        self.start_time = 0
        self.memory_usage = 0
        self.cpu_usage = 0
    
    
    def _enqueue_output(self, pipe, queue):
        """将进程输出放入队列"""
        for line in iter(pipe.readline, b''):
            if self.should_stop:
                break
            if line:
                try:
                    decoded_line = line.decode('utf-8', errors='replace').rstrip()
                    queue.put(decoded_line)
                except Exception as e:
                    queue.put(f"[日志解码错误]: {str(e)}")
        pipe.close()
    
    
    def _monitor_process(self):
        """监控进程资源使用情况"""
        while self.process and not self.should_stop:
            try:
                if self.process.poll() is not None:
                    self.status = "已停止"
                    break
                
                # 获取进程资源使用情况
                proc = psutil.Process(self.process.pid)
                self.memory_usage = proc.memory_info().rss / (1024 * 1024)  # MB
                self.cpu_usage = proc.cpu_percent(interval=1)
            except (psutil.NoSuchProcess, ProcessLookupError):
                self.status = "已停止"
                break
            except Exception as e:
                self.log_queue.put(f"[监控错误]: {str(e)}")
            
            time.sleep(2)
    
    
    def start_backend(self) -> str:
        """
        启动后端服务进程
        
        Returns:
            str: 启动结果信息
        """
        if self.process and self.process.poll() is None:
            return "后端服务已在运行中"
        
        # 重置状态
        self.should_stop = False
        self.log_queue = Queue()
        self.error_queue = Queue()
        
        try:
            # 设置启动命令
            cmd = [sys.executable, os.path.join(ROOT_PATH, "app.py")]
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                cwd=ROOT_PATH,
                bufsize=1,
                universal_newlines=False
            )
            
            # 启动输出捕获线程
            self.stdout_thread = threading.Thread(
                target=self._enqueue_output, 
                args=(self.process.stdout, self.log_queue),
                daemon=True
            )
            self.stdout_thread.start()
            
            self.stderr_thread = threading.Thread(
                target=self._enqueue_output, 
                args=(self.process.stderr, self.error_queue),
                daemon=True
            )
            self.stderr_thread.start()
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )
            self.monitor_thread.start()
            
            self.status = "运行中"
            self.start_time = time.time()
            
            return f"后端服务已启动，PID: {self.process.pid}"
        
        except Exception as e:
            self.status = "启动失败"
            return f"启动后端服务失败: {str(e)}"
    
    
    def stop_backend(self) -> str:
        """
        停止后端服务进程
        
        Returns:
            str: 停止结果信息
        """
        if not self.process:
            return "后端服务未运行"
        
        try:
            self.should_stop = True
            
            if self.process.poll() is None:
                pid = self.process.pid
                
                # 在Windows上避免使用CTRL_C_EVENT (会影响整个进程组)
                if os.name == 'nt':
                    # 查找并记录子进程
                    child_pids = []
                    try:
                        parent = psutil.Process(pid)
                        for child in parent.children(recursive=True):
                            child_pids.append(child.pid)
                    except:
                        pass
                    
                    # 使用taskkill命令直接终止目标进程，避免使用信号
                    try:
                        # 先尝试优雅终止
                        os.system(f"taskkill /PID {pid}")
                        time.sleep(2)
                        
                        # 如果进程还在，强制终止
                        if self.process.poll() is None:
                            os.system(f"taskkill /F /PID {pid}")
                        
                        # 确保所有子进程都被终止
                        for child_pid in child_pids:
                            try:
                                os.system(f"taskkill /F /PID {child_pid}")
                            except:
                                pass
                    except:
                        # 如果taskkill失败，回退到terminate/kill
                        self.process.terminate()
                        time.sleep(1)
                        if self.process.poll() is None:
                            self.process.kill()
                else:
                    # 在Linux/Mac上，应该是安全的，但也避免使用信号
                    try:
                        # 尝试终止整个进程组的更安全方法
                        parent = psutil.Process(pid)
                        children = parent.children(recursive=True)
                        for child in children:
                            child.terminate()
                        gone, alive = psutil.wait_procs(children, timeout=3)
                        for p in alive:
                            p.kill()
                        
                        # 终止主进程
                        self.process.terminate()
                        time.sleep(1)
                        if self.process.poll() is None:
                            self.process.kill()
                    except:
                        # 最后手段
                        self.process.terminate()
                        time.sleep(1)
                        if self.process.poll() is None:
                            self.process.kill()
            
            self.status = "已停止"
            self.process = None
            
            # 使用更安全的方式查找和终止残留的app.py进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.cmdline()
                    if len(cmdline) >= 2 and 'python' in cmdline[0].lower() and 'app.py' in cmdline[1]:
                        if os.name == 'nt':
                            os.system(f"taskkill /F /PID {proc.pid}")
                        else:
                            proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            return "后端服务已停止"
        
        except Exception as e:
            return f"停止后端服务失败: {str(e)}"
    
    
    def get_logs(self, max_lines: int = 100) -> List[str]:
        """
        获取最新的日志行
        
        Args:
            max_lines: 最大返回行数
            
        Returns:
            List[str]: 日志行列表
        """
        logs = []
        
        # 收集标准输出
        for _ in range(max_lines):
            try:
                line = self.log_queue.get_nowait()
                logs.append(line)
            except Empty:
                break
        
        # 收集标准错误
        for _ in range(max_lines):
            try:
                line = self.error_queue.get_nowait()
                logs.append(line)
            except Empty:
                break
        
        return logs
    
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取后端进程状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        uptime = 0
        if self.start_time > 0 and self.status == "运行中":
            uptime = int(time.time() - self.start_time)
        
        return {
            "status": self.status,
            "uptime": uptime,
            "memory_mb": round(self.memory_usage, 1),
            "cpu_percent": round(self.cpu_usage, 1),
            "pid": self.process.pid if self.process else None
        }
    
    
    def is_running(self) -> bool:
        """
        检查后端服务是否正在运行
        
        Returns:
            bool: 进程是否在运行
        """
        return self.process is not None and self.process.poll() is None


backend_process = ProcessManager()
