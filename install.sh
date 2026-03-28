#!/bin/bash
# Token交易平台技能安装脚本

set -e

echo "🚀 安装 Token交易平台技能..."
echo ""

# 创建安装目录
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# 创建数据目录
DATA_DIR="$HOME/.token-exchange"
mkdir -p "$DATA_DIR"

# 复制可执行文件
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/exchange.py" "$INSTALL_DIR/token-exchange"
chmod +x "$INSTALL_DIR/token-exchange"

echo "✅ 安装完成!"
echo ""
echo "使用方法:"
echo "  token-exchange market                     # 查看行情"
echo "  token-exchange buy --platform openai --amount 100000 --price 0.002"
echo "  token-exchange sell --platform openai --amount 50000 --price 0.0022"
echo "  token-exchange orders                     # 查看订单"
echo "  token-exchange balance                    # 查看余额"
echo "  token-exchange rent --platform anthropic --amount 100000 --duration 24h"
echo "  token-exchange swap --from openai --to anthropic --amount 100000"
echo ""
echo "数据存储: $DATA_DIR"
echo ""
echo "💡 访问完整平台: http://token-master.cn/shop/"
echo ""

# 检查PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "⚠️  请将 $INSTALL_DIR 添加到PATH:"
    echo "   echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
    echo "   source ~/.bashrc"
fi

echo ""
echo "🎉 Token经济生态 5/5 技能全部完成!"
