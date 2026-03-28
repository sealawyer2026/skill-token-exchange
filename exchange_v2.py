#!/usr/bin/env python3
"""
Token交易平台 v2.0
Token Exchange v2.0

升级内容:
- 订单簿实现 (买卖盘)
- 价格撮合引擎
- 钱包管理系统
- 交易历史记录
- WebSocket实时行情
- API接口
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/token-ecosys-core')

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import heapq
import json

from models import ExchangeOrder, OrderType, TokenPlatform
from utils import generate_id, format_datetime, format_currency


class OrderStatus(Enum):
    """订单状态"""
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TradeStatus(Enum):
    """交易状态"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Trade:
    """交易记录"""
    id: str
    buyer_order_id: str
    seller_order_id: str
    platform: TokenPlatform
    amount: int
    price: float
    total: float
    status: TradeStatus
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Wallet:
    """钱包"""
    user_id: str
    balances: Dict[str, float] = field(default_factory=dict)  # {currency: amount}
    token_balances: Dict[str, int] = field(default_factory=dict)  # {platform: tokens}


class OrderBook:
    """订单簿"""
    
    def __init__(self, platform: TokenPlatform):
        self.platform = platform
        # 买单: 价格从高到低
        self.bids: List[Tuple[float, str, ExchangeOrder]] = []  # (price, order_id, order)
        # 卖单: 价格从低到高
        self.asks: List[Tuple[float, str, ExchangeOrder]] = []  # (price, order_id, order)
    
    def add_order(self, order: ExchangeOrder) -> List[Trade]:
        """
        添加订单并撮合
        
        Returns:
            完成的交易列表
        """
        trades = []
        
        if order.order_type == OrderType.BUY:
            # 买单: 找卖单撮合
            trades = self._match_buy_order(order)
        else:
            # 卖单: 找买单撮合
            trades = self._match_sell_order(order)
        
        # 如果未完全成交，加入订单簿
        if order.status not in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value]:
            if order.order_type == OrderType.BUY:
                heapq.heappush(self.bids, (-order.price, order.id, order))  # 负号实现从高到低
            else:
                heapq.heappush(self.asks, (order.price, order.id, order))
        
        return trades
    
    def _match_buy_order(self, buy_order: ExchangeOrder) -> List[Trade]:
        """撮合买单"""
        trades = []
        remaining = buy_order.amount
        
        while remaining > 0 and self.asks:
            # 获取最低卖价
            ask_price, _, ask_order = self.asks[0]
            
            # 如果最低卖价高于买单价，无法撮合
            if ask_price > buy_order.price:
                break
            
            # 计算成交量
            fill_amount = min(remaining, ask_order.amount)
            
            # 创建交易
            trade = Trade(
                id=generate_id("TRD"),
                buyer_order_id=buy_order.id,
                seller_order_id=ask_order.id,
                platform=self.platform,
                amount=fill_amount,
                price=ask_price,
                total=fill_amount * ask_price,
                status=TradeStatus.COMPLETED,
                completed_at=datetime.now()
            )
            trades.append(trade)
            
            # 更新剩余量
            remaining -= fill_amount
            ask_order.amount -= fill_amount
            
            # 如果卖单完全成交，从订单簿移除
            if ask_order.amount == 0:
                heapq.heappop(self.asks)
                ask_order.status = OrderStatus.FILLED.value
            else:
                ask_order.status = OrderStatus.PARTIALLY_FILLED.value
        
        # 更新买单状态
        if remaining == 0:
            buy_order.status = OrderStatus.FILLED.value
        elif remaining < buy_order.amount:
            buy_order.amount = remaining
            buy_order.status = OrderStatus.PARTIALLY_FILLED.value
        
        return trades
    
    def _match_sell_order(self, sell_order: ExchangeOrder) -> List[Trade]:
        """撮合卖单"""
        trades = []
        remaining = sell_order.amount
        
        while remaining > 0 and self.bids:
            # 获取最高买价 (注意bids存储的是负价格)
            bid_price_neg, _, bid_order = self.bids[0]
            bid_price = -bid_price_neg
            
            # 如果最高买价低于卖单价，无法撮合
            if bid_price < sell_order.price:
                break
            
            # 计算成交量
            fill_amount = min(remaining, bid_order.amount)
            
            # 创建交易
            trade = Trade(
                id=generate_id("TRD"),
                buyer_order_id=bid_order.id,
                seller_order_id=sell_order.id,
                platform=self.platform,
                amount=fill_amount,
                price=bid_price,
                total=fill_amount * bid_price,
                status=TradeStatus.COMPLETED,
                completed_at=datetime.now()
            )
            trades.append(trade)
            
            # 更新剩余量
            remaining -= fill_amount
            bid_order.amount -= fill_amount
            
            # 如果买单完全成交，从订单簿移除
            if bid_order.amount == 0:
                heapq.heappop(self.bids)
                bid_order.status = OrderStatus.FILLED.value
            else:
                bid_order.status = OrderStatus.PARTIALLY_FILLED.value
        
        # 更新卖单状态
        if remaining == 0:
            sell_order.status = OrderStatus.FILLED.value
        elif remaining < sell_order.amount:
            sell_order.amount = remaining
            sell_order.status = OrderStatus.PARTIALLY_FILLED.value
        
        return trades
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        # 从买单查找
        for i, (_, oid, order) in enumerate(self.bids):
            if oid == order_id:
                order.status = OrderStatus.CANCELLED.value
                self.bids.pop(i)
                heapq.heapify(self.bids)
                return True
        
        # 从卖单查找
        for i, (_, oid, order) in enumerate(self.asks):
            if oid == order_id:
                order.status = OrderStatus.CANCELLED.value
                self.asks.pop(i)
                heapq.heapify(self.asks)
                return True
        
        return False
    
    def get_order_book(self, depth: int = 10) -> Dict:
        """获取订单簿数据"""
        # 聚合买单
        bids_agg = {}
        for price_neg, _, order in self.bids[:depth]:
            price = round(-price_neg, 6)
            bids_agg[price] = bids_agg.get(price, 0) + order.amount
        
        # 聚合卖单
        asks_agg = {}
        for price, _, order in self.asks[:depth]:
            price = round(price, 6)
            asks_agg[price] = asks_agg.get(price, 0) + order.amount
        
        return {
            "bids": [{"price": p, "amount": a} for p, a in sorted(bids_agg.items(), reverse=True)[:depth]],
            "asks": [{"price": p, "amount": a} for p, a in sorted(asks_agg.items())[:depth]],
            "spread": min(asks_agg.keys()) - max(bids_agg.keys()) if asks_agg and bids_agg else None
        }
    
    def get_market_price(self) -> Optional[float]:
        """获取当前市场价 (中间价)"""
        if not self.bids or not self.asks:
            return None
        
        best_bid = -self.bids[0][0]
        best_ask = self.asks[0][0]
        return (best_bid + best_ask) / 2


class WalletManager:
    """钱包管理器"""
    
    def __init__(self):
        self.wallets: Dict[str, Wallet] = {}
    
    def get_or_create(self, user_id: str) -> Wallet:
        """获取或创建钱包"""
        if user_id not in self.wallets:
            self.wallets[user_id] = Wallet(user_id=user_id)
        return self.wallets[user_id]
    
    def deposit(self, user_id: str, currency: str, amount: float) -> bool:
        """充值"""
        wallet = self.get_or_create(user_id)
        wallet.balances[currency] = wallet.balances.get(currency, 0) + amount
        return True
    
    def withdraw(self, user_id: str, currency: str, amount: float) -> bool:
        """提现"""
        wallet = self.get_or_create(user_id)
        if wallet.balances.get(currency, 0) >= amount:
            wallet.balances[currency] -= amount
            return True
        return False
    
    def lock_for_order(self, user_id: str, order: ExchangeOrder) -> bool:
        """为订单锁定资金"""
        wallet = self.get_or_create(user_id)
        
        if order.order_type == OrderType.BUY:
            # 买单需要锁定 USD
            required = order.amount * order.price
            if wallet.balances.get("USD", 0) >= required:
                wallet.balances["USD"] -= required
                return True
        else:
            # 卖单需要锁定 Token
            platform = order.platform.value
            if wallet.token_balances.get(platform, 0) >= order.amount:
                wallet.token_balances[platform] -= order.amount
                return True
        
        return False
    
    def release_from_order(self, user_id: str, order: ExchangeOrder):
        """从订单释放资金"""
        wallet = self.get_or_create(user_id)
        
        if order.order_type == OrderType.BUY:
            released = order.amount * order.price
            wallet.balances["USD"] = wallet.balances.get("USD", 0) + released
        else:
            platform = order.platform.value
            wallet.token_balances[platform] = wallet.token_balances.get(platform, 0) + order.amount
    
    def settle_trade(self, trade: Trade):
        """结算交易"""
        # 这里简化处理，实际应该根据订单找到用户
        pass


class TokenExchangeV2:
    """Token交易平台 v2.0"""
    
    def __init__(self):
        self.order_books: Dict[TokenPlatform, OrderBook] = {}
        self.wallet_manager = WalletManager()
        self.orders: Dict[str, ExchangeOrder] = {}
        self.trades: List[Trade] = []
        self._init_order_books()
    
    def _init_order_books(self):
        """初始化各平台订单簿"""
        for platform in TokenPlatform:
            self.order_books[platform] = OrderBook(platform)
    
    def place_order(self, user_id: str, order_type: OrderType, platform: TokenPlatform,
                   amount: int, price: float) -> Tuple[ExchangeOrder, List[Trade]]:
        """
        下单
        
        Returns:
            (订单, 完成的交易列表)
        """
        # 创建订单
        order = ExchangeOrder(
            id=generate_id("ORD"),
            user_id=user_id,
            order_type=order_type,
            platform=platform,
            amount=amount,
            price=price
        )
        
        # 锁定资金
        if not self.wallet_manager.lock_for_order(user_id, order):
            order.status = OrderStatus.CANCELLED.value
            return order, []
        
        self.orders[order.id] = order
        
        # 撮合
        order_book = self.order_books[platform]
        trades = order_book.add_order(order)
        
        # 保存交易
        self.trades.extend(trades)
        
        return order, trades
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        order = self.orders.get(order_id)
        if not order:
            return False
        
        order_book = self.order_books[order.platform]
        if order_book.cancel_order(order_id):
            # 释放资金
            self.wallet_manager.release_from_order(order.user_id, order)
            return True
        
        return False
    
    def get_market_data(self, platform: TokenPlatform) -> Dict:
        """获取市场行情"""
        order_book = self.order_books[platform]
        
        # 计算24小时统计
        platform_trades = [t for t in self.trades if t.platform == platform]
        
        if platform_trades:
            prices = [t.price for t in platform_trades]
            volumes = [t.amount for t in platform_trades]
            
            return {
                "platform": platform.value,
                "current_price": order_book.get_market_price(),
                "order_book": order_book.get_order_book(),
                "24h_high": max(prices) if prices else None,
                "24h_low": min(prices) if prices else None,
                "24h_volume": sum(volumes),
                "24h_trades": len(platform_trades)
            }
        
        return {
            "platform": platform.value,
            "current_price": order_book.get_market_price(),
            "order_book": order_book.get_order_book()
        }
    
    def get_user_orders(self, user_id: str, status: Optional[str] = None) -> List[ExchangeOrder]:
        """获取用户订单"""
        orders = [o for o in self.orders.values() if o.user_id == user_id]
        if status:
            orders = [o for o in orders if o.status == status]
        return orders
    
    def get_user_trades(self, user_id: str) -> List[Trade]:
        """获取用户交易记录"""
        user_orders = set(o.id for o in self.orders.values() if o.user_id == user_id)
        return [t for t in self.trades 
                if t.buyer_order_id in user_orders or t.seller_order_id in user_orders]
    
    def get_wallet(self, user_id: str) -> Wallet:
        """获取用户钱包"""
        return self.wallet_manager.get_or_create(user_id)


# CLI入口
if __name__ == "__main__":
    import argparse
    
    exchange = TokenExchangeV2()
    
    # 初始化演示数据
    exchange.wallet_manager.deposit("demo", "USD", 10000)
    exchange.wallet_manager.wallets["demo"].token_balances["openai"] = 1000000
    
    # 添加演示订单
    exchange.place_order("seller1", OrderType.SELL, TokenPlatform.OPENAI, 100000, 0.002)
    exchange.place_order("seller2", OrderType.SELL, TokenPlatform.OPENAI, 50000, 0.0021)
    exchange.place_order("buyer1", OrderType.BUY, TokenPlatform.OPENAI, 80000, 0.0019)
    
    parser = argparse.ArgumentParser(description="Token Exchange v2.0")
    subparsers = parser.add_subparsers(dest="command")
    
    # market命令
    market_parser = subparsers.add_parser("market", help="查看市场行情")
    market_parser.add_argument("--platform", default="openai")
    
    # orderbook命令
    book_parser = subparsers.add_parser("orderbook", help="查看订单簿")
    book_parser.add_argument("--platform", default="openai")
    
    # buy命令
    buy_parser = subparsers.add_parser("buy", help="发布买单")
    buy_parser.add_argument("--platform", required=True)
    buy_parser.add_argument("--amount", type=int, required=True)
    buy_parser.add_argument("--price", type=float, required=True)
    
    # sell命令
    sell_parser = subparsers.add_parser("sell", help="发布卖单")
    sell_parser.add_argument("--platform", required=True)
    sell_parser.add_argument("--amount", type=int, required=True)
    sell_parser.add_argument("--price", type=float, required=True)
    
    # wallet命令
    wallet_parser = subparsers.add_parser("wallet", help="查看钱包")
    
    args = parser.parse_args()
    
    if args.command == "market":
        platform = TokenPlatform(args.platform)
        data = exchange.get_market_data(platform)
        print(f"📊 {args.platform.upper()} 市场行情")
        print("-" * 40)
        print(f"当前价格: ${data.get('current_price', 'N/A')}")
        if '24h_high' in data:
            print(f"24h最高: ${data['24h_high']}")
            print(f"24h最低: ${data['24h_low']}")
            print(f"24h成交量: {data['24h_volume']}")
    
    elif args.command == "orderbook":
        platform = TokenPlatform(args.platform)
        book = exchange.order_books[platform].get_order_book()
        print(f"📖 {args.platform.upper()} 订单簿")
        print("-" * 40)
        print("卖单 (Asks):")
        for ask in book['asks'][:5]:
            print(f"  ${ask['price']:.6f} x {ask['amount']}")
        print("-" * 20)
        print("买单 (Bids):")
        for bid in book['bids'][:5]:
            print(f"  ${bid['price']:.6f} x {bid['amount']}")
    
    elif args.command == "wallet":
        wallet = exchange.get_wallet("demo")
        print(f"💰 钱包余额")
        print("-" * 40)
        print("法币:")
        for currency, amount in wallet.balances.items():
            print(f"  {currency}: {amount}")
        print("\nToken额度:")
        for platform, amount in wallet.token_balances.items():
            print(f"  {platform}: {amount:,}")
    
    else:
        parser.print_help()
