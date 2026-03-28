#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token转让市场 - C2C额度交易平台
Token Exchange - C2C Quota Trading Platform

用户间API额度交易平台
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    """订单类型"""
    SELL = "sell"    # 出售
    BUY = "buy"      # 求购


class OrderStatus(Enum):
    """订单状态"""
    OPEN = "open"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class TradeStatus(Enum):
    """交易状态"""
    PENDING = "pending"
    ESCROW = "escrow"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """挂单"""
    id: str
    user_id: str
    type: OrderType
    platform: str
    amount: float
    price: float
    currency: str
    status: OrderStatus
    created_at: float
    description: str = ""


@dataclass
class Trade:
    """交易"""
    id: str
    buyer_id: str
    seller_id: str
    order_id: str
    platform: str
    amount: float
    price: float
    total: float
    platform_fee: float
    status: TradeStatus
    created_at: float
    escrow_release_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class User:
    """用户"""
    id: str
    name: str
    reputation_score: int
    trades_completed: int
    trades_disputed: int
    joined_at: float


class TokenExchange:
    """Token转让市场"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化"""
        self.config = self._load_config(config_path)
        self.orders: Dict[str, Order] = {}
        self.trades: Dict[str, Trade] = {}
        self.users: Dict[str, User] = {}
        
        self.platform_fee = self.config.get("exchange", {}).get("platform_fee", 0.05)
        self.min_order = self.config.get("exchange", {}).get("min_order_amount", 10)
    
    def _load_config(self, path: str) -> Dict:
        """加载配置"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "exchange": {"platform_fee": 0.05, "min_order_amount": 10}
        }
    
    def get_supported_platforms(self) -> List[Dict]:
        """获取支持的平台"""
        return self.config.get("supported_tokens", [])
    
    def register_user(self, user_id: str, name: str) -> User:
        """
        注册用户
        
        Args:
            user_id: 用户ID
            name: 用户名
        
        Returns:
            User对象
        """
        if user_id in self.users:
            return self.users[user_id]
        
        initial_score = self.config.get("reputation", {}).get("initial_score", 100)
        
        user = User(
            id=user_id,
            name=name,
            reputation_score=initial_score,
            trades_completed=0,
            trades_disputed=0,
            joined_at=time.time()
        )
        
        self.users[user_id] = user
        return user
    
    def create_order(self, user_id: str, order_type: OrderType, platform: str,
                    amount: float, price: float, description: str = "") -> Order:
        """
        创建挂单
        
        Args:
            user_id: 用户ID
            order_type: 订单类型 (sell/buy)
            platform: 平台ID
            amount: 数量
            price: 单价
            description: 描述
        
        Returns:
            Order对象
        """
        if amount < self.min_order:
            raise ValueError(f"最小挂单金额: {self.min_order}")
        
        # 获取平台货币
        platforms = {p["id"]: p for p in self.get_supported_platforms()}
        if platform not in platforms:
            raise ValueError(f"不支持的平台: {platform}")
        
        currency = platforms[platform]["unit"]
        
        order = Order(
            id=f"ORD{int(time.time())}{uuid.uuid4().hex[:6].upper()}",
            user_id=user_id,
            type=order_type,
            platform=platform,
            amount=amount,
            price=price,
            currency=currency,
            status=OrderStatus.OPEN,
            created_at=time.time(),
            description=description
        )
        
        self.orders[order.id] = order
        return order
    
    def get_open_orders(self, platform: Optional[str] = None, 
                       order_type: Optional[OrderType] = None) -> List[Order]:
        """
        获取开放订单
        
        Args:
            platform: 平台筛选
            order_type: 类型筛选
        
        Returns:
            订单列表
        """
        orders = [o for o in self.orders.values() if o.status == OrderStatus.OPEN]
        
        if platform:
            orders = [o for o in orders if o.platform == platform]
        
        if order_type:
            orders = [o for o in orders if o.type == order_type]
        
        # 按价格排序 (卖单低到高，买单高到低)
        orders.sort(key=lambda x: x.price, reverse=(order_type == OrderType.BUY))
        
        return orders
    
    def accept_order(self, order_id: str, counterparty_id: str) -> Trade:
        """
        接受订单
        
        Args:
            order_id: 订单ID
            counterparty_id: 对手方ID
        
        Returns:
            Trade对象
        """
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"订单不存在: {order_id}")
        
        if order.status != OrderStatus.OPEN:
            raise ValueError(f"订单状态不正确: {order.status.value}")
        
        if order.user_id == counterparty_id:
            raise ValueError("不能与自己交易")
        
        # 确定买卖双方
        if order.type == OrderType.SELL:
            buyer_id = counterparty_id
            seller_id = order.user_id
        else:
            buyer_id = order.user_id
            seller_id = counterparty_id
        
        total = order.amount * order.price
        fee = total * self.platform_fee
        
        trade = Trade(
            id=f"TRD{int(time.time())}{uuid.uuid4().hex[:6].upper()}",
            buyer_id=buyer_id,
            seller_id=seller_id,
            order_id=order_id,
            platform=order.platform,
            amount=order.amount,
            price=order.price,
            total=round(total, 2),
            platform_fee=round(fee, 2),
            status=TradeStatus.PENDING,
            created_at=time.time()
        )
        
        self.trades[trade.id] = trade
        order.status = OrderStatus.PENDING
        
        return trade
    
    def confirm_payment(self, trade_id: str) -> Trade:
        """
        确认付款 (买方)
        
        Args:
            trade_id: 交易ID
        
        Returns:
            Trade对象
        """
        trade = self.trades.get(trade_id)
        if not trade:
            raise ValueError(f"交易不存在: {trade_id}")
        
        if trade.status != TradeStatus.PENDING:
            raise ValueError(f"交易状态不正确: {trade.status.value}")
        
        trade.status = TradeStatus.ESCROW
        
        # 设置托管释放时间
        escrow_duration = self.config.get("exchange", {}).get("escrow_duration", 86400)
        trade.escrow_release_at = time.time() + escrow_duration
        
        return trade
    
    def confirm_delivery(self, trade_id: str) -> Trade:
        """
        确认交付 (买方)
        
        Args:
            trade_id: 交易ID
        
        Returns:
            Trade对象
        """
        trade = self.trades.get(trade_id)
        if not trade:
            raise ValueError(f"交易不存在: {trade_id}")
        
        if trade.status != TradeStatus.ESCROW:
            raise ValueError(f"交易状态不正确: {trade.status.value}")
        
        trade.status = TradeStatus.COMPLETED
        trade.completed_at = time.time()
        
        # 更新订单状态
        order = self.orders.get(trade.order_id)
        if order:
            order.status = OrderStatus.COMPLETED
        
        # 更新用户信誉
        self._update_user_reputation(trade.buyer_id, True)
        self._update_user_reputation(trade.seller_id, True)
        
        return trade
    
    def _update_user_reputation(self, user_id: str, success: bool):
        """更新用户信誉"""
        user = self.users.get(user_id)
        if not user:
            return
        
        if success:
            user.trades_completed += 1
            bonus = self.config.get("reputation", {}).get("bonus_per_trade", 1)
            user.reputation_score += bonus
        else:
            user.trades_disputed += 1
            penalty = self.config.get("reputation", {}).get("penalty_dispute", 10)
            user.reputation_score -= penalty
    
    def cancel_order(self, order_id: str) -> Order:
        """
        取消订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            Order对象
        """
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"订单不存在: {order_id}")
        
        if order.status not in [OrderStatus.OPEN, OrderStatus.PENDING]:
            raise ValueError(f"订单状态不可取消: {order.status.value}")
        
        order.status = OrderStatus.CANCELLED
        
        # 如果有进行中的交易，也取消
        for trade in self.trades.values():
            if trade.order_id == order_id and trade.status in [TradeStatus.PENDING, TradeStatus.ESCROW]:
                trade.status = TradeStatus.CANCELLED
        
        return order
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """获取交易详情"""
        return self.trades.get(trade_id)
    
    def get_user_trades(self, user_id: str) -> List[Trade]:
        """获取用户交易历史"""
        return [
            t for t in self.trades.values()
            if t.buyer_id == user_id or t.seller_id == user_id
        ]
    
    def get_market_price(self, platform: str) -> Dict:
        """
        获取市场价格
        
        Args:
            platform: 平台ID
        
        Returns:
            价格信息
        """
        sell_orders = [o for o in self.get_open_orders(platform, OrderType.SELL) if o.price > 0]
        buy_orders = [o for o in self.get_open_orders(platform, OrderType.BUY) if o.price > 0]
        
        sell_avg = sum(o.price for o in sell_orders) / len(sell_orders) if sell_orders else 0
        buy_avg = sum(o.price for o in buy_orders) / len(buy_orders) if buy_orders else 0
        
        return {
            "platform": platform,
            "sell_count": len(sell_orders),
            "buy_count": len(buy_orders),
            "sell_avg_price": round(sell_avg, 4),
            "buy_avg_price": round(buy_avg, 4),
            "lowest_sell": min((o.price for o in sell_orders), default=0),
            "highest_buy": max((o.price for o in buy_orders), default=0)
        }
    
    def get_stats(self) -> Dict:
        """获取市场统计"""
        completed_trades = [t for t in self.trades.values() if t.status == TradeStatus.COMPLETED]
        
        total_volume = sum(t.total for t in completed_trades)
        total_fee = sum(t.platform_fee for t in completed_trades)
        
        return {
            "total_users": len(self.users),
            "total_orders": len(self.orders),
            "open_orders": len([o for o in self.orders.values() if o.status == OrderStatus.OPEN]),
            "total_trades": len(self.trades),
            "completed_trades": len(completed_trades),
            "total_volume": round(total_volume, 2),
            "total_fees": round(total_fee, 2)
        }


def get_exchange(config_path: str = "config.json") -> TokenExchange:
    """获取交易所实例"""
    return TokenExchange(config_path)
