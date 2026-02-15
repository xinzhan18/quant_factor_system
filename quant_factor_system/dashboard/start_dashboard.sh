#!/bin/bash
# QuantFactor Dashboard 启动脚本
# 确保在 conda 环境中运行

set -e

echo "=========================================="
echo "📊 QuantFactor Dashboard"
echo "=========================================="

# 检查 conda 环境
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️  未检测到 conda 环境"
    echo "请运行: conda activate quantfactor"
    exit 1
fi

echo "✅ 环境: $CONDA_DEFAULT_ENV"

# 检查 Python
PYTHON=$(which python)
echo "✅ Python: $PYTHON"

# 设置路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 创建符号链接（如果不存在）
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
LINK_TARGET="$SITE_PACKAGES/quant_factor_system"

if [ ! -L "$LINK_TARGET" ]; then
    echo "🔗 创建符号链接..."
    ln -sf "$SCRIPT_DIR" "$LINK_TARGET"
    echo "✅ 符号链接创建完成"
else
    echo "✅ 符号链接已存在"
fi

echo ""
echo "🌐 启动 Dashboard..."
echo "访问: http://localhost:8501"
echo "按 Ctrl+C 停止"
echo "=========================================="

# 启动 Streamlit
exec python -m streamlit run Home.py
