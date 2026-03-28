# Token转让市场

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/sealawyer2026/skill-token-exchange)

> C2C API额度交易平台

## 🎯 简介

Token转让市场是一个C2C交易平台，用户可以出售闲置的API额度或求购所需额度，平台提供托管服务和信誉系统保障交易安全。

## ✨ 功能特性

- 📝 **挂单交易** - 支持出售和求购
- 🔒 **托管服务** - 资金托管保障安全
- ⭐ **信誉系统** - 交易评价机制
- 📈 **市场行情** - 实时价格走势
- 💰 **低手续费** - 仅5%平台费

## 🚀 快速开始

```bash
# 安装
pip install -r requirements.txt

# 查看市场行情
python main.py market

# 出售额度
python main.py sell --user u001 --platform openai --amount 100 --price 0.9

# 求购额度
python main.py buy --user u002 --platform moonshot --amount 50 --price 0.008

# 接受订单
python main.py accept --order ORD123 --user u002
```

## 💡 使用示例

### 查看行情

```bash
$ python main.py market

📈 市场行情
============================================================

🏢 OpenAI API额度 (USD)
------------------------------------------------------------
   卖单: 5 个 | 最低: 0.85
   买单: 3 个 | 最高: 0.92
   平均卖价: 0.88

🏢 Kimi API额度 (CNY)
------------------------------------------------------------
   卖单: 8 个 | 最低: 0.00045
   买单: 5 个 | 最高: 0.00055
   平均卖价: 0.00050
```

### 挂单交易

```bash
$ python main.py sell --user u001 --platform openai --amount 100 --price 0.9

✅ 挂单成功
   订单ID: ORD17431412345678A1B2C3
   平台: openai
   数量: 100
   单价: 0.9
   总价: 90.00 USD

$ python main.py buy --user u002 --platform openai --amount 50 --price 0.92

✅ 求购单创建成功
   订单ID: ORD17431412345679D4E5F6
   平台: openai
   数量: 50
   单价: 0.92
   总价: 46.00 USD
```

### 接受订单

```bash
$ python main.py accept --order ORD17431412345678A1B2C3 --user u002

✅ 交易创建成功
   交易ID: TRD17431412345680G7H8I9
   金额: 90.00 USD
   平台手续费: 4.50
   状态: pending

   下一步: 买方付款后使用 confirm-payment 确认
```

## 📊 支持平台

| 平台 | 名称 | 货币 | 最小交易 |
|------|------|------|----------|
| openai | OpenAI API额度 | USD | 5 |
| moonshot | Kimi API额度 | CNY | 10 |
| bytedance | 豆包 API额度 | CNY | 10 |

## 🔄 交易流程

```
1. 卖方创建挂单 (sell)
   ↓
2. 买方浏览并选择订单
   ↓
3. 买方接受订单 (accept)
   ↓
4. 买方付款并确认 (confirm-payment)
   → 资金进入托管
   ↓
5. 卖方交付API密钥
   ↓
6. 买方确认收货 (confirm-delivery)
   → 托管资金释放给卖方
   ↓
7. 交易完成，双方互评
```

## 💰 费率说明

| 费用 | 比例 | 说明 |
|------|------|------|
| 平台手续费 | 5% | 交易金额 × 5% |
| 提现手续费 | 1% | 提现金额 × 1% |

## ⭐ 信誉系统

- 初始信誉分: 100
- 成功交易: +1分
- 纠纷败诉: -10分
- 信誉分影响交易限额和优先级

## 🔒 安全保障

- **资金托管** - 买方付款后资金由平台托管
- **时间锁定** - 24小时争议期
- **信誉机制** - 交易评价影响用户信誉
- **纠纷处理** - 平台介入处理争议

## 📄 License

MIT License
