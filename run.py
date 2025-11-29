#!/usr/bin/env python3
"""
快速启动脚本
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == '__main__':
    print("=" * 60)
    print("LIS Extractor - 医院检验数据抽取工具")
    print("=" * 60)
    print()
    
    main()

