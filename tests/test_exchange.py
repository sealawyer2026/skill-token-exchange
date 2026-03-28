#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token转让市场 - 测试套件
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchange import TokenExchange, OrderType, OrderStatus, TradeStatus, get_exchange


class TestTokenExchange(unittest.TestCase):
    """测试Token转让市场"""
    
    def setUp(self):
        """测试前准备"""
        self.exchange = get_exchange()
    
    def test_register_user(self):
        """测试注册用户"""
        user = self.exchange.register_user("u001", "测试用户")
        
        self.assertEqual(user.id, "u001")
        self.assertEqual(user.name, "测试用户")
        self.assertEqual(user.reputation_score, 100)
    
    def test_create_sell_order(self):
        """测试创建卖单"""
        self.exchange.register_user("u001", "卖家")
        
        order = self.exchange.create_order(
            user_id="u001",
            order_type=OrderType.SELL,
            platform="openai",
            amount=100,
            price=0.9
        )
        
        self.assertEqual(order.type, OrderType.SELL)
        self.assertEqual(order.platform, "openai")
        self.assertEqual(order.amount, 100)
        self.assertEqual(order.status, OrderStatus.OPEN)
    
    def test_get_open_orders(self):
        """测试获取开放订单"""
        self.exchange.register_user("u001", "卖家")
        self.exchange.create_order("u001", OrderType.SELL, "openai", 100, 0.9)
        
        orders = self.exchange.get_open_orders()
        self.assertGreater(len(orders), 0)
    
    def test_accept_order(self):
        """测试接受订单"""
        self.exchange.register_user("u001", "卖家")
        self.exchange.register_user("u002", "买家")
        
        order = self.exchange.create_order("u001", OrderType.SELL, "openai", 100, 0.9)
        trade = self.exchange.accept_order(order.id, "u002")
        
        self.assertIsNotNone(trade)
        self.assertEqual(trade.status, TradeStatus.PENDING)
        self.assertEqual(trade.buyer_id, "u002")
        self.assertEqual(trade.seller_id, "u001")
    
    def test_confirm_payment(self):
        """测试确认付款"""
        self.exchange.register_user("u001", "卖家")
        self.exchange.register_user("u002", "买家")
        
        order = self.exchange.create_order("u001", OrderType.SELL, "openai", 100, 0.9)
        trade = self.exchange.accept_order(order.id, "u002")
        
        trade = self.exchange.confirm_payment(trade.id)
        self.assertEqual(trade.status, TradeStatus.ESCROW)
        self.assertIsNotNone(trade.escrow_release_at)
    
    def test_confirm_delivery(self):
        """测试确认交付"""
        self.exchange.register_user("u001", "卖家")
        self.exchange.register_user("u002", "买家")
        
        order = self.exchange.create_order("u001", OrderType.SELL, "openai", 100, 0.9)
        trade = self.exchange.accept_order(order.id, "u002")
        self.exchange.confirm_payment(trade.id)
        
        trade = self.exchange.confirm_delivery(trade.id)
        self.assertEqual(trade.status, TradeStatus.COMPLETED)
        self.assertIsNotNone(trade.completed_at)
    
    def test_cancel_order(self):
        """测试取消订单"""
        self.exchange.register_user("u001", "卖家")
        order = self.exchange.create_order("u001", OrderType.SELL, "openai", 100, 0.9)
        
        cancelled = self.exchange.cancel_order(order.id)
        self.assertEqual(cancelled.status, OrderStatus.CANCELLED)
    
    def test_get_stats(self):
        """测试获取统计"""
        stats = self.exchange.get_stats()
        
        self.assertIn("total_users", stats)
        self.assertIn("total_orders", stats)
        self.assertIn("total_trades", stats)


if __name__ == '__main__':
    unittest.main(verbosity=2)
