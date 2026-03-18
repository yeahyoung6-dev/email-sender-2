#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
邮件群发工具 - 主程序入口
"""

import sys
import os

# 确保能找到同目录下的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import EmailSenderGUI


def main():
    """主函数"""
    app = EmailSenderGUI()
    app.run()


if __name__ == "__main__":
    main()