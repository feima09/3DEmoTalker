"""
配置管理模块

该模块负责从环境变量和配置文件中加载系统配置，
包括日志级别、服务器设置、API端点、认证信息等。
支持从.env文件和JSON配置文件中读取设置。

作者: 光明实验室媒体智能团队
"""

import os
import yaml


home_dir = os.getcwd()

with open(f"{home_dir}/configs/config.yaml", 'r', encoding='utf-8') as file:
    Config = yaml.safe_load(file)

with open(f"{os.getcwd()}/configs/prompt.txt", 'r', encoding='utf-8') as file:
    Prompt = file.read()
    
with open(os.path.join(home_dir, "configs", "rag", "template.txt"), 'r', encoding='utf-8') as file:
    Template = file.read()
