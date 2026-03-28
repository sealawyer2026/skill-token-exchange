#!/usr/bin/env python3
"""
Token交易平台技能 (Token Exchange)
去中心化Token交易市场
"""

import json
import argparse
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path
import uuid

# 数据存储路径
DATA_DIR = Path.home() / ".token-exchange"
DATA_DIR.mkdir(exist_ok=True)

# 平台配置
PLATFORMS = {
    "openai": {"name": "OpenAI", "base_price": 0.002},  # per 1K tokens
    "anthropic": {"name": "Anthropic", "base_price": 0.003},
    "gemini": {"name": "Google Gemini", "base_price": 0.0005},
    "alibaba": {"name": "阿里云", "base_price": 0.0003},
    "baidu": {"name": "百度", "base_price": 0.0004},
    "moonshot": {"name": "Moonshot", "base_price": 0.0006}
}

@dataclass
class Order:
    id: str
    type: str  # buy or sell
    platform: str
    amount: int
    price: float
    status: str  # open, filled, cancelled
    created_at: str
    filled_at: Optional[str] = None
    counterparty: Optional[str] = None

@dataclass
class Trade:
    id: str
    buy_order_id: str
    sell_order_id: str
    platform: str
    amount: int
    price: float
    timestamp: str

@dataclass
class Rental:
    id: str
    platform: str
    amount: int
    hourly_rate: float
    duration_hours: int
    start_time: str
    end_time: str
    status: str

class TokenExchange:
    def __init__(self):
        self.orders_file = DATA_DIR / "orders.json"
        self.trades_file = DATA_DIR / "trades.json"
        self.rentals_file = DATA_DIR / "rentals.json"
        self.balance_file = DATA_DIR / "balance.json"
        self.load_data()
    
    def load_data(self):
        """加载数据"""
        if self.balance_file.exists():
            with open(self.balance_file, 'r') as f:
                self.balance = json.load(f)
        else:
            self.balance = {p: 0 for p in PLATFORMS.keys()}
            self.balance["USD"] = 10000  # 初始资金
    
    def save_data(self):
        """保存数据"""
        with open(self.balance_file, 'w') as f:
            json.dump(self.balance, f, indent=2)
    
    def load_orders(self) -> List[Order]:
        """加载订单"""
        if not self.orders_file.exists():
            return []
        with open(self.orders_file, 'r') as f:
            data = json.load(f)
            return [Order(**o) for o in data]
    
    def save_orders(self, orders: List[Order]):
        """保存订单"""
        with open(self.orders_file, 'w') as f:
            json.dump([asdict(o) for o in orders], f, indent=2)
    
    def load_trades(self) -> List[Trade]:
        """加载交易记录"""
        if not self.trades_file.exists():
            return []
        with open(self.trades_file, 'r') as f:
            data = json.load(f)
            return [Trade(**t) for t in data]
    
    def save_trades(self, trades: List[Trade]):
        """保存交易记录"""
        with open(self.trades_file, 'w') as f:
            json.dump([asdict(t) for t in trades], f, indent=2)
    
    def get_market_price(self, platform: str) -> Dict:
        """获取市场价格"""
        base = PLATFORMS[platform]["base_price"]
        # 模拟市场波动
        bid = base * (0.9 + random.random() * 0.2)  # 买盘价格
        ask = base * (1.0 + random.random() * 0.2)  # 卖盘价格
        
        return {
            "platform": platform,
            "name": PLATFORMS[platform]["name"],
            "bid": round(bid, 6),
            "ask": round(ask, 6),
            "base_price": base,
            "spread": round((ask - bid) / bid * 100, 2)
        }

def cmd_market(args):
    """查看市场行情"""
    exchange = TokenExchange()
    
    print("📈 Token交易市场行情")
    print(f"=" * 70)
    print(f"{'平台':<15} {'买盘':<12} {'卖盘':<12} {'基准价':<12} {'价差':<10}")
    print("-" * 70)
    
    for platform in PLATFORMS.keys():
        price = exchange.get_market_price(platform)
        print(f"{price['name']:<15} ${price['bid']:<11.6f} ${price['ask']:<11.6f} ${price['base_price']:<11.6f} {price['spread']:.2f}%")
    
    print("")
    print("💡 提示: 使用 buy/sell 命令交易")

def cmd_buy(args):
    """发布买单"""
    exchange = TokenExchange()
    
    platform = args.platform.lower()
    amount = args.amount
    price = args.price
    
    if platform not in PLATFORMS:
        print(f"❌ 不支持的平台: {platform}")
        print(f"支持的平台: {', '.join(PLATFORMS.keys())}")
        return
    
    total_cost = amount * price / 1000  # 转换为实际金额
    
    if exchange.balance["USD"] < total_cost:
        print(f"❌ 余额不足")
        print(f"需要: ${total_cost:.2f}")
        print(f"余额: ${exchange.balance['USD']:.2f}")
        return
    
    # 创建订单
    order = Order(
        id=str(uuid.uuid4())[:8],
        type="buy",
        platform=platform,
        amount=amount,
        price=price,
        status="open",
        created_at=datetime.now().isoformat()
    )
    
    # 冻结资金
    exchange.balance["USD"] -= total_cost
    exchange.save_data()
    
    # 保存订单
    orders = exchange.load_orders()
    orders.append(order)
    exchange.save_orders(orders)
    
    print(f"✅ 买单已发布")
    print(f"=" * 50)
    print(f"订单ID: {order.id}")
    print(f"平台: {PLATFORMS[platform]['name']}")
    print(f"数量: {amount:,} tokens")
    print(f"单价: ${price:.6f}/1K")
    print(f"总价: ${total_cost:.2f}")
    print(f"状态: {order.status}")

def cmd_sell(args):
    """发布卖单"""
    exchange = TokenExchange()
    
    platform = args.platform.lower()
    amount = args.amount
    price = args.price
    
    if platform not in PLATFORMS:
        print(f"❌ 不支持的平台: {platform}")
        return
    
    if exchange.balance[platform] < amount:
        print(f"❌ {PLATFORMS[platform]['name']} Token余额不足")
        print(f"需要: {amount:,}")
        print(f"余额: {exchange.balance[platform]:,}")
        return
    
    # 创建订单
    order = Order(
        id=str(uuid.uuid4())[:8],
        type="sell",
        platform=platform,
        amount=amount,
        price=price,
        status="open",
        created_at=datetime.now().isoformat()
    )
    
    # 冻结Token
    exchange.balance[platform] -= amount
    exchange.save_data()
    
    # 保存订单
    orders = exchange.load_orders()
    orders.append(order)
    exchange.save_orders(orders)
    
    total_value = amount * price / 1000
    
    print(f"✅ 卖单已发布")
    print(f"=" * 50)
    print(f"订单ID: {order.id}")
    print(f"平台: {PLATFORMS[platform]['name']}")
    print(f"数量: {amount:,} tokens")
    print(f"单价: ${price:.6f}/1K")
    print(f"预估收入: ${total_value:.2f}")
    print(f"状态: {order.status}")

def cmd_orders(args):
    """查看我的订单"""
    exchange = TokenExchange()
    orders = exchange.load_orders()
    
    print("📋 我的订单")
    print(f"=" * 70)
    
    if not orders:
        print("暂无订单")
        return
    
    open_orders = [o for o in orders if o.status == "open"]
    filled_orders = [o for o in orders if o.status == "filled"]
    
    if open_orders:
        print(f"未成交订单 ({len(open_orders)}):")
        print(f"{'ID':<10} {'类型':<8} {'平台':<12} {'数量':<12} {'单价':<12} {'时间'}")
        print("-" * 70)
        for o in open_orders:
            platform_name = PLATFORMS[o.platform]['name']
            print(f"{o.id:<10} {o.type:<8} {platform_name:<12} {o.amount:<12,} ${o.price:<11.6f} {o.created_at[:10]}")
    
    if filled_orders:
        print("")
        print(f"已成交订单 ({len(filled_orders)}):")
        for o in filled_orders[:5]:  # 只显示最近5个
            platform_name = PLATFORMS[o.platform]['name']
            print(f"  {o.id} | {o.type} | {platform_name} | {o.amount:,} | ${o.price:.6f}")

def cmd_balance(args):
    """查看余额"""
    exchange = TokenExchange()
    
    print("💰 我的资产")
    print(f"=" * 50)
    print(f"{'资产':<20} {'余额':<15} {'估值'}")
    print("-" * 50)
    
    # USD
    print(f"{'USD (现金)':<20} ${exchange.balance['USD']:<14.2f} -")
    
    # Token
    total_value = exchange.balance["USD"]
    for platform, info in PLATFORMS.items():
        balance = exchange.balance.get(platform, 0)
        if balance > 0:
            value = balance * info["base_price"] / 1000
            total_value += value
            print(f"{info['name']:<20} {balance:<15,} ${value:.2f}")
    
    print("-" * 50)
    print(f"{'总资产':<20} {'':<15} ${total_value:.2f}")

def cmd_deposit(args):
    """托管Token"""
    exchange = TokenExchange()
    
    platform = args.platform.lower()
    amount = args.amount
    
    if platform not in PLATFORMS:
        print(f"❌ 不支持的平台")
        return
    
    # 模拟存入
    exchange.balance[platform] += amount
    exchange.save_data()
    
    print(f"✅ 托管成功")
    print(f"平台: {PLATFORMS[platform]['name']}")
    print(f"数量: {amount:,} tokens")
    print(f"当前余额: {exchange.balance[platform]:,}")

def cmd_rent(args):
    """租赁Token"""
    platform = args.platform.lower()
    amount = args.amount
    duration = args.duration
    
    if platform not in PLATFORMS:
        print(f"❌ 不支持的平台")
        return
    
    # 解析时长
    if duration.endswith('h'):
        hours = int(duration[:-1])
    elif duration.endswith('d'):
        hours = int(duration[:-1]) * 24
    else:
        hours = int(duration)
    
    # 计算租金 (按基准价10%计算)
    base_price = PLATFORMS[platform]["base_price"]
    hourly_rate = base_price * 0.1
    total_rent = amount * hourly_rate * hours / 1000
    
    print(f"📦 Token租赁")
    print(f"=" * 50)
    print(f"平台: {PLATFORMS[platform]['name']}")
    print(f"数量: {amount:,} tokens")
    print(f"时长: {hours}小时")
    print(f"时租: ${hourly_rate:.6f}/1K")
    print(f"总租金: ${total_rent:.2f}")
    print("")
    print("💡 功能说明:")
    print("   租赁功能模拟演示")
    print("   实际部署需接入智能合约")

def cmd_swap(args):
    """兑换Token"""
    from_platform = args.from_platform.lower()
    to_platform = args.to_platform.lower()
    amount = args.amount
    
    if from_platform not in PLATFORMS or to_platform not in PLATFORMS:
        print(f"❌ 不支持的平台")
        return
    
    # 计算汇率
    from_price = PLATFORMS[from_platform]["base_price"]
    to_price = PLATFORMS[to_platform]["base_price"]
    rate = from_price / to_price
    received = int(amount * rate * 0.98)  # 2%手续费
    
    print(f"🔄 Token兑换")
    print(f"=" * 50)
    print(f"从: {PLATFORMS[from_platform]['name']}")
    print(f"到: {PLATFORMS[to_platform]['name']}")
    print(f"数量: {amount:,} {from_platform.upper()}")
    print(f"汇率: 1 {from_platform.upper()} = {rate:.4f} {to_platform.upper()}")
    print(f"手续费: 2%")
    print(f"获得: {received:,} {to_platform.upper()}")
    print("")
    print("💡 兑换功能模拟演示")

def cmd_history(args):
    """查看交易历史"""
    exchange = TokenExchange()
    trades = exchange.load_trades()
    
    print("📜 交易历史")
    print(f"=" * 70)
    
    if not trades:
        print("暂无交易记录")
        return
    
    print(f"{'时间':<20} {'平台':<12} {'数量':<12} {'价格':<12} {'交易额'}")
    print("-" * 70)
    
    for trade in trades[-10:]:  # 最近10笔
        platform_name = PLATFORMS[trade.platform]['name']
        total = trade.amount * trade.price / 1000
        print(f"{trade.timestamp[:16]:<20} {platform_name:<12} {trade.amount:<12,} ${trade.price:<11.6f} ${total:.2f}")

def main():
    parser = argparse.ArgumentParser(
        description="Token交易平台 - 去中心化Token交易市场",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  token-exchange market                    # 查看行情
  token-exchange buy --platform openai --amount 100000 --price 0.002
  token-exchange sell --platform openai --amount 50000 --price 0.0022
  token-exchange orders                    # 查看订单
  token-exchange balance                   # 查看余额
  token-exchange deposit --platform openai --amount 1000000
  token-exchange rent --platform anthropic --amount 100000 --duration 24h
  token-exchange swap --from openai --to anthropic --amount 100000
  token-exchange history                   # 交易历史

Token经济生态:
  - Token Master: Token压缩
  - Compute Market: 算力市场
  - Token Consumer Optimizer: 消费优选
  - Token Auditor: 审计监控
  - Token Exchange: 交易平台 (本工具)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # market命令
    subparsers.add_parser('market', help='查看市场行情')
    
    # buy命令
    buy_parser = subparsers.add_parser('buy', help='发布买单')
    buy_parser.add_argument('--platform', '-p', required=True, help='平台名称')
    buy_parser.add_argument('--amount', '-a', type=int, required=True, help='购买数量(tokens)')
    buy_parser.add_argument('--price', type=float, required=True, help='单价($/1K tokens)')
    
    # sell命令
    sell_parser = subparsers.add_parser('sell', help='发布卖单')
    sell_parser.add_argument('--platform', '-p', required=True, help='平台名称')
    sell_parser.add_argument('--amount', '-a', type=int, required=True, help='出售数量(tokens)')
    sell_parser.add_argument('--price', type=float, required=True, help='单价($/1K tokens)')
    
    # orders命令
    subparsers.add_parser('orders', help='查看我的订单')
    
    # balance命令
    subparsers.add_parser('balance', help='查看余额')
    
    # deposit命令
    deposit_parser = subparsers.add_parser('deposit', help='托管Token')
    deposit_parser.add_argument('--platform', '-p', required=True, help='平台名称')
    deposit_parser.add_argument('--amount', '-a', type=int, required=True, help='数量(tokens)')
    
    # rent命令
    rent_parser = subparsers.add_parser('rent', help='租赁Token')
    rent_parser.add_argument('--platform', '-p', required=True, help='平台名称')
    rent_parser.add_argument('--amount', '-a', type=int, required=True, help='数量(tokens)')
    rent_parser.add_argument('--duration', '-d', required=True, help='时长(如24h, 7d)')
    
    # swap命令
    swap_parser = subparsers.add_parser('swap', help='兑换Token')
    swap_parser.add_argument('--from', dest='from_platform', required=True, help='源平台')
    swap_parser.add_argument('--to', dest='to_platform', required=True, help='目标平台')
    swap_parser.add_argument('--amount', '-a', type=int, required=True, help='数量')
    
    # history命令
    subparsers.add_parser('history', help='查看交易历史')
    
    args = parser.parse_args()
    
    if args.command == 'market':
        cmd_market(args)
    elif args.command == 'buy':
        cmd_buy(args)
    elif args.command == 'sell':
        cmd_sell(args)
    elif args.command == 'orders':
        cmd_orders(args)
    elif args.command == 'balance':
        cmd_balance(args)
    elif args.command == 'deposit':
        cmd_deposit(args)
    elif args.command == 'rent':
        cmd_rent(args)
    elif args.command == 'swap':
        cmd_swap(args)
    elif args.command == 'history':
        cmd_history(args)
    else:
        parser.print_help()
        print("\n💡 Token经济生态 (5/5 完成):")
        print("   ✅ Token Master: Token压缩")
        print("   ✅ Compute Market: 算力市场")
        print("   ✅ Token Consumer Optimizer: 消费优选")
        print("   ✅ Token Auditor: 审计监控")
        print("   ✅ Token Exchange: 交易平台 (本工具)")

if __name__ == '__main__':
    main()
