#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI数字人控制面板入口脚本

启动方法：python dashboard.py
"""

from webui import dashboard

if __name__ == "__main__":
    print("正在启动AI数字人控制面板...")
    dashboard.launch(server_name="0.0.0.0", server_port=7860, share=False, inbrowser=True)
