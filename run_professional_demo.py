#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业因子分析系统启动脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入并运行
from quant_factor_system import professional_demo

if __name__ == "__main__":
    professional_demo.main()
