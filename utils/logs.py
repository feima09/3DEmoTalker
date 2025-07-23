"""
日志工具模块

该模块提供了日志系统的配置和管理功能，包括：
- 同时将日志输出到控制台和文件
- 按天进行日志文件轮转，便于管理和查询
- 自动保留最近14天的日志记录
- 日志文件按 YYYY-MM-DD.txt 格式命名存储

使用方法:
    from utils.logs import setup_logger
    logger = setup_logger()
    logger.info("这是一条信息日志")
    logger.error("这是一条错误日志")
"""

import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from utils import Config

app_logger = None

log_level = Config.get("log_level", "INFO")
if log_level == "DEBUG":
    log_level = logging.DEBUG
elif log_level == "WARNING":
    log_level = logging.WARNING
elif log_level == "ERROR":
    log_level = logging.ERROR
else:
    log_level = logging.INFO
    

def namer_function(default_name):
    """自定义日志文件命名函数，将文件命名为 YYYY-MM-DD.txt 格式
    
    Args:
        default_name: 默认的日志文件名称
        
    Returns:
        str: 新的日志文件名称
    """
    # 从当前日期获取日期字符串
    date_str = datetime.now().strftime('%Y-%m-%d')
    # 获取目录路径
    dir_name = os.path.dirname(default_name)
    # 创建新的文件名
    return os.path.join(dir_name, f"{date_str}.txt")


def setup_logger() -> logging.Logger:
    """配置应用日志，同时输出到控制台和文件
    
    - 按天进行日志轮转
    - 保留最近14天的日志文件
    - 日志同时输出到控制台和文件
    - 日志文件按 YYYY-MM-DD.txt 格式命名
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志目录
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 使用当前日期作为日志文件名
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f"{current_date}.txt")
    
    # 创建日志格式
    log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s')
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有处理器（如果有）
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # 添加按天轮转的文件处理器
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',      # 每天午夜轮转
        interval=1,           # 每1天轮转一次
        backupCount=14,       # 保留最近14天的日志
        encoding='utf-8',
        delay=False
    )
    
    # 设置自定义文件命名函数
    file_handler.namer = namer_function
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    global app_logger
    app_logger = logging.getLogger('app')
    return app_logger


def get_logger() -> logging.Logger:
    """获取已配置的应用日志记录器
    
    Returns:
        logging.Logger: 应用全局日志记录器
    """
    global app_logger
    if app_logger is None:
        return setup_logger()
    return app_logger
