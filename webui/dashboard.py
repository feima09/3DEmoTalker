"""
AI数字人后端控制面板

使用Gradio构建的WebUI，用于控制和监控后端进程。
提供启动/停止功能，实时日志显示和系统资源监控。

作者: 光明实验室媒体智能团队
"""

import gradio as gr
from typing import List, Dict

from .process import backend_process
from . import config

# 设置刷新时间间隔(秒)
REFRESH_INTERVAL = 1

log_lines: List[str] = []
max_log_lines = 1000  # 最大保留日志行数


def update_logs() -> str:
    """
    更新并获取最新日志
    
    Returns:
        str: 格式化的日志文本
    """
    global log_lines
    
    # 获取新日志
    new_logs = backend_process.get_logs()
    if new_logs:
        # 处理每条日志，确保为utf-8字符串
        processed_logs = []
        for log in new_logs:
            if isinstance(log, bytes):
                try:
                    log = log.decode("utf-8", errors="replace")
                except Exception:
                    log = str(log)
            else:
                # 强制转为str，防止有非str类型
                log = str(log)
            processed_logs.append(log)
        # 添加到日志列表，并保持最大长度限制
        log_lines.extend(processed_logs)
        if len(log_lines) > max_log_lines:
            log_lines = log_lines[-max_log_lines:]
    
    # 返回格式化的日志文本
    return "\n".join(log_lines)


def start_backend() -> str:
    """
    启动后端服务
    
    Returns:
        str: 操作结果消息
    """
    result = backend_process.start_backend()
    return result


def stop_backend() -> str:
    """
    停止后端服务
    
    Returns:
        str: 操作结果消息
    """
    result = backend_process.stop_backend()
    return result


def get_status() -> Dict[str, str]:
    """
    获取并格式化后端状态信息
    
    Returns:
        Dict[str, str]: 格式化后的状态信息
    """
    status_info = backend_process.get_status()
    
    # 格式化运行时间
    uptime = status_info["uptime"]
    if uptime > 0:
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        seconds = uptime % 60
        uptime_str = f"{hours}小时 {minutes}分钟 {seconds}秒"
    else:
        uptime_str = "0秒"
    
    return {
        "状态": status_info["status"],
        "运行时间": uptime_str,
        "内存使用": f"{status_info['memory_mb']} MB",
        "CPU使用": f"{status_info['cpu_percent']}%",
        "进程ID": str(status_info["pid"] or "无")
    }


def clear_logs() -> str:
    """
    清空日志显示
    
    Returns:
        str: 空字符串，用于清空日志区域
    """
    global log_lines
    log_lines = []
    return ""


def create_ui() -> gr.Blocks:
    """
    创建Gradio用户界面
    
    Returns:
        gr.Blocks: Gradio界面对象
    """
    with gr.Blocks(title="AI数字人控制面板") as dashboard:
        with gr.Tabs():  # 修改为Tabs而不是TabItem，TabItem必须在Tabs内部使用
            with gr.TabItem("控制面板"):
                gr.Markdown("# AI数字人后端控制面板")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        start_btn = gr.Button("启动后端服务", variant="primary")
                        stop_btn = gr.Button("停止后端服务", variant="stop")
                        clear_logs_btn = gr.Button("清空日志")
                        
                        status_label = gr.Markdown("## 系统状态")
                        status_info = gr.JSON(get_status, label="状态信息")
                        
                    with gr.Column(scale=2):
                        logs_label = gr.Markdown("## 后端日志")
                        logs_output = gr.Textbox(
                            label="实时日志输出", 
                            value="等待后端服务启动...",
                            lines=25,
                            max_lines=25,
                            autoscroll=True
                        )
                
                # 设置按钮回调
                start_btn.click(start_backend, outputs=logs_output)
                stop_btn.click(stop_backend, outputs=logs_output)
                clear_logs_btn.click(clear_logs, outputs=logs_output)
                
                # 创建定时器组件并使用tick方法设置定时调用
                log_timer = gr.Timer(value=REFRESH_INTERVAL, active=True)
                log_timer.tick(update_logs, None, logs_output)
                
                status_timer = gr.Timer(value=REFRESH_INTERVAL, active=True)
                status_timer.tick(get_status, None, status_info)
        
            with gr.TabItem("配置面板"):
                config.create_ui()
    
    return dashboard


def check_backend_status():
    """检查后端状态并开始捕获日志"""
    if backend_process.is_running():
        global log_lines
        log_lines.append("检测到后端服务已在运行")
        status_info = backend_process.get_status()
        log_lines.append(f"进程ID: {status_info['pid']}")


dashboard = create_ui()

if __name__ == "__main__":
    check_backend_status()
    
    dashboard.launch(server_name="0.0.0.0", server_port=7860)
