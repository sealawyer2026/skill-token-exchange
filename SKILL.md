---
name: token-exchange
description: Token Exchange - C2C API quota trading platform. Users can buy and sell unused API quotas with escrow and reputation system.
---

# Token转让市场

C2C API额度交易平台

## 功能

- ✅ 挂单出售/求购
- ✅ 托管交易
- ✅ 信誉系统
- ✅ 市场行情
- ✅ 多平台支持

## 使用

```bash
# 查看行情
python main.py market

# 出售额度
python main.py sell --user u001 --platform openai --amount 100 --price 0.9

# 求购额度
python main.py buy --user u002 --platform moonshot --amount 50 --price 0.008

# 接受订单
python main.py accept --order ORD123 --user u002

# 查看统计
python main.py stats
```

## 支持平台

| 平台 | 货币 | 最小交易 |
|------|------|----------|
| OpenAI | USD | 5 |
| Moonshot | CNY | 10 |
| ByteDance | CNY | 10 |

## 交易流程

1. 卖方挂单 (sell)
2. 买方接受订单 (accept)
3. 买方付款并确认
4. 卖方交付API密钥
5. 买方确认收货
6. 平台释放资金

## 费率

- 平台手续费: 5%
- 提现手续费: 1%
