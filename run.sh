#!/bin/bash
# ============================================================
# QuantFactorSystem - 主启动脚本
# ============================================================

# 项目根目录
PROJECT_DIR="/Users/xinzhan/.openclaw/workspace/quant_factor_system"

# Conda环境
CONDA_BASE="/Users/xinzhan/miniconda3"
CONDA_ENV="quantfactor"

echo "============================================================"
echo "📊 QuantFactorSystem v3.0"
echo "============================================================"
echo ""

# 检查conda环境
if [ ! -d "$CONDA_BASE/envs/$CONDA_ENV" ]; then
    echo "❌ Conda环境 '$CONDA_ENV' 不存在"
    exit 1
fi

# 设置Python路径
export PYTHONPATH="/Users/xinzhan/.openclaw/workspace:$PYTHONPATH"

# 使用conda环境中的Python
PYTHON="$CONDA_BASE/envs/$CONDA_ENV/bin/python"

# 检查是否安装为包
$PYTHON -c "import quant_factor_system" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 安装项目包..."
    cd $PROJECT_DIR
    $PYTHON -m pip install -e . -q 2>/dev/null
fi

# 切换到项目目录
cd $PROJECT_DIR

case "${1:-info}" in
    info|version|status|init|data|pipeline|benchmark|clean)
        echo "🚀 运行: python cli.py $1"
        echo ""
        $PYTHON cli.py "$@"
        ;;
    -h|--help|help)
        echo "用法: $0 [命令]"
        echo ""
        echo "可用命令:"
        echo "  info      - 系统信息"
        echo "  version   - 版本信息"
        echo "  status    - 系统状态"
        echo "  init      - 初始化数据库"
        echo "  data      - 数据管理"
        echo "  pipeline  - 运行Pipeline"
        echo "  benchmark - 基准测试"
        echo "  clean     - 清理"
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo "运行: $0 --help"
        exit 1
        ;;
esac
