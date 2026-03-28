# Token交易平台技能 (Token Exchange)

去中心化Token交易市场，支持Token额度买卖、租赁、托管和兑换。

## 核心功能

### 1. Token额度交易
- 买卖AI平台Token额度
- 支持OpenAI、Anthropic、Google等主流平台
- 实时价格发现

### 2. Token租赁
- 短期租赁Token额度
- 按小时/天计费
- 到期自动回收

### 3. Token托管
- 第三方托管服务
- 安全存储Token
- 按需分发

### 4. Token兑换
- 不同平台Token互换
- 汇率自动计算
- 即时到账

### 5. 订单簿
- 挂单买卖
- 市价成交
- 交易历史

## 交易对

| 交易对 | 说明 |
|--------|------|
| OPENAI/USD | OpenAI Token额度 |
| ANTHROPIC/USD | Anthropic Token额度 |
| GEMINI/USD | Google Gemini Token额度 |
| ALIBABA/USD | 阿里云Token额度 |
| BAIDU/USD | 百度Token额度 |

## 使用示例

```bash
# 查看市场行情
token-exchange market

# 发布卖单
token-exchange sell --platform openai --amount 1000000 --price 0.002

# 发布买单
token-exchange buy --platform openai --amount 500000 --price 0.0018

# 租赁Token
token-exchange rent --platform anthropic --amount 100000 --duration 24h

# 托管Token
token-exchange deposit --platform openai --amount 1000000

# 兑换Token
token-exchange swap --from openai --to anthropic --amount 100000

# 查看我的订单
token-exchange orders

# 查看交易历史
token-exchange history
```

## Token经济生态

- **Token Master**: Token压缩优化
- **Compute Market**: 算力交易市场
- **Token Consumer Optimizer**: 消费优选决策
- **Token Auditor**: 审计监控
- **Token Exchange**: Token交易平台 (本技能)

**Version:** 1.0.0
