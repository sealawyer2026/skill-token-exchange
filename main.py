#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token转让市场 - CLI入口
Token Exchange CLI

C2C API额度交易平台
"""

import argparse
import json
import sys
from datetime import datetime

from exchange import TokenExchange, OrderType, OrderStatus, TradeStatus, get_exchange


def print_header():
    """打印标题"""
    print("""
╔══════════════════════════════════════════════╗
║     Token转让市场 v1.0.0                     ║
║     C2C额度交易平台                          ║
╚══════════════════════════════════════════════╝
""")


def cmd_market(args):
    """查看市场行情"""
    exchange = get_exchange(args.config)
    
    print("📈 市场行情")
    print("=" * 60)
    
    for platform in exchange.get_supported_platforms():
        price = exchange.get_market_price(platform["id"])
        
        print(f"\n🏢 {platform['name']} ({platform['unit']})")
        print("-" * 60)
        print(f"   卖单: {price['sell_count']} 个 | 最低: {price['lowest_sell']}")
        print(f"   买单: {price['buy_count']} 个 | 最高: {price['highest_buy']}")
        if price['sell_avg_price']:
            print(f"   平均卖价: {price['sell_avg_price']:.4f}")


def cmd_orders(args):
    """查看挂单"""
    exchange = get_exchange(args.config)
    
    orders = exchange.get_open_orders(args.platform, OrderType(args.type) if args.type else None)
    
    print(f"📋 挂单列表 {'- ' + args.type if args.type else ''}")
    print("=" * 80)
    
    if not orders:
        print("   暂无挂单")
        return
    
    print(f"{'ID':<25} {'类型':<8} {'平台':<12} {'数量':<10} {'单价':<10} {'总价':<10}")
    print("-" * 80)
    
    for o in orders[:20]:
        total = o.amount * o.price
        type_icon = "🔴 卖" if o.type == OrderType.SELL else "🟢 买"
        print(f"{o.id:<25} {type_icon:<8} {o.platform:<12} {o.amount:<10.2f} {o.price:<10.4f} {total:<10.2f}")


def cmd_sell(args):
    """出售"""
    exchange = get_exchange(args.config)
    
    # 注册用户
    exchange.register_user(args.user, args.user)
    
    order = exchange.create_order(
        user_id=args.user,
        order_type=OrderType.SELL,
        platform=args.platform,
        amount=args.amount,
        price=args.price,
        description=args.desc
    )
    
    print(f"✅ 挂单成功")
    print(f"   订单ID: {order.id}")
    print(f"   平台: {order.platform}")
    print(f"   数量: {order.amount}")
    print(f"   单价: {order.price}")
    print(f"   总价: {order.amount * order.price:.2f} {order.currency}")


def cmd_buy(args):
    """求购"""
    exchange = get_exchange(args.config)
    
    # 注册用户
    exchange.register_user(args.user, args.user)
    
    order = exchange.create_order(
        user_id=args.user,
        order_type=OrderType.BUY,
        platform=args.platform,
        amount=args.amount,
        price=args.price,
        description=args.desc
    )
    
    print(f"✅ 求购单创建成功")
    print(f"   订单ID: {order.id}")
    print(f"   平台: {order.platform}")
    print(f"   数量: {order.amount}")
    print(f"   单价: {order.price}")
    print(f"   总价: {order.amount * order.price:.2f} {order.currency}")


def cmd_accept(args):
    """接受订单"""
    exchange = get_exchange(args.config)
    
    exchange.register_user(args.user, args.user)
    
    trade = exchange.accept_order(args.order, args.user)
    
    print(f"✅ 交易创建成功")
    print(f"   交易ID: {trade.id}")
    print(f"   金额: {trade.total:.2f} {exchange.orders[trade.order_id].currency}")
    print(f"   平台手续费: {trade.platform_fee:.2f}")
    print(f"   状态: {trade.status.value}")
    print()
    print("   下一步: 买方付款后使用 confirm-payment 确认")


def cmd_stats(args):
    """查看统计"""
    exchange = get_exchange(args.config)
    
    stats = exchange.get_stats()
    
    print("📊 市场统计")
    print("=" * 60)
    print(f"   注册用户数: {stats['total_users']}")
    print(f"   总挂单数: {stats['total_orders']}")
    print(f"   开放挂单: {stats['open_orders']}")
    print(f"   总交易数: {stats['total_trades']}")
    print(f"   完成交易: {stats['completed_trades']}")
    print(f"   交易总额: {stats['total_volume']}")
    print(f"   平台手续费收入: {stats['total_fees']}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Token转让市场 - C2C额度交易平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看市场行情
  python main.py market
  
  # 查看挂单
  python main.py orders --platform openai --type sell
  
  # 出售额度
  python main.py sell --user u001 --platform openai --amount 100 --price 0.9
  
  # 求购额度
  python main.py buy --user u002 --platform moonshot --amount 50 --price 0.008
  
  # 接受订单
  python main.py accept --order ORD123 --user u002
  
  # 查看统计
  python main.py stats

支持平台:
  - openai: OpenAI API额度 (USD)
  - moonshot: Kimi API额度 (CNY)
  - bytedance: 豆包 API额度 (CNY)

交易流程:
  1. 卖方挂单 (sell)
  2. 买方接受订单 (accept)
  3. 买方付款并确认 (confirm-payment)
  4. 卖方交付API密钥
  5. 买方确认收货 (confirm-delivery)
  6. 平台释放资金给卖方

费率:
  - 平台手续费: 5%
  - 提现手续费: 1%
        """
    )
    
    parser.add_argument('--version', action='version', version='Token转让市场 v1.0.0')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # market 命令
    subparsers.add_parser('market', help='查看市场行情')
    
    # orders 命令
    orders_parser = subparsers.add_parser('orders', help='查看挂单')
    orders_parser.add_argument('--platform', help='平台筛选')
    orders_parser.add_argument('--type', choices=['sell', 'buy'], help='类型筛选')
    
    # sell 命令
    sell_parser = subparsers.add_parser('sell', help='出售额度')
    sell_parser.add_argument('--user', required=True, help='用户ID')
    sell_parser.add_argument('--platform', required=True, help='平台')
    sell_parser.add_argument('--amount', type=float, required=True, help='数量')
    sell_parser.add_argument('--price', type=float, required=True, help='单价')
    sell_parser.add_argument('--desc', default='', help='描述')
    
    # buy 命令
    buy_parser = subparsers.add_parser('buy', help='求购额度')
    buy_parser.add_argument('--user', required=True, help='用户ID')
    buy_parser.add_argument('--platform', required=True, help='平台')
    buy_parser.add_argument('--amount', type=float, required=True, help='数量')
    buy_parser.add_argument('--price', type=float, required=True, help='单价')
    buy_parser.add_argument('--desc', default='', help='描述')
    
    # accept 命令
    accept_parser = subparsers.add_parser('accept', help='接受订单')
    accept_parser.add_argument('--order', required=True, help='订单ID')
    accept_parser.add_argument('--user', required=True, help='用户ID')
    
    # stats 命令
    subparsers.add_parser('stats', help='查看统计')
    
    args = parser.parse_args()
    
    if not args.command:
        print_header()
        parser.print_help()
        sys.exit(0)
    
    try:
        if args.command == 'market':
            cmd_market(args)
        elif args.command == 'orders':
            cmd_orders(args)
        elif args.command == 'sell':
            cmd_sell(args)
        elif args.command == 'buy':
            cmd_buy(args)
        elif args.command == 'accept':
            cmd_accept(args)
        elif args.command == 'stats':
            cmd_stats(args)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
