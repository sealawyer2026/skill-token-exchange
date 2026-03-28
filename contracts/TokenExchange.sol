// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title TokenExchange
 * @dev Token额度去中心化交易平台
 * 
 * 功能:
 * 1. 挂单交易 (买单/卖单)
 * 2. 原子化结算
 * 3. 托管与释放
 * 4. 交易历史记录
 */

contract TokenExchange {
    // 订单结构
    struct Order {
        address trader;
        bool isBuy;          // true=买单, false=卖单
        string platform;     // "openai", "anthropic"等
        uint256 amount;      // Token数量
        uint256 price;       // 单价 (wei per token)
        uint256 timestamp;
        bool active;
    }
    
    // 交易记录
    struct Trade {
        uint256 orderId;
        address buyer;
        address seller;
        string platform;
        uint256 amount;
        uint256 price;
        uint256 total;
        uint256 timestamp;
    }
    
    // 状态变量
    mapping(uint256 => Order) public orders;
    mapping(address => uint256) public balances;  // ETH余额
    mapping(address => mapping(string => uint256)) public tokenBalances;  // Token余额
    mapping(address => Trade[]) public tradeHistory;
    
    uint256 public nextOrderId = 1;
    uint256 public platformFee = 100;  // 1% = 100 basis points
    address public owner;
    
    // 事件
    event OrderCreated(uint256 indexed orderId, address indexed trader, bool isBuy, string platform, uint256 amount, uint256 price);
    event TradeExecuted(uint256 indexed orderId, address indexed buyer, address indexed seller, string platform, uint256 amount, uint256 total);
    event OrderCancelled(uint256 indexed orderId);
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    
    constructor() {
        owner = msg.sender;
    }
    
    // 充值ETH
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
    
    // 提现ETH
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
        emit Withdrawal(msg.sender, amount);
    }
    
    // 充值Token (由平台方调用)
    function depositTokens(string calldata platform, uint256 amount) external {
        // 实际实现需要ERC20合约地址
        tokenBalances[msg.sender][platform] += amount;
    }
    
    // 创建买单
    function createBuyOrder(string calldata platform, uint256 amount, uint256 price) external returns (uint256) {
        uint256 totalCost = amount * price;
        require(balances[msg.sender] >= totalCost, "Insufficient ETH balance");
        
        // 锁定资金
        balances[msg.sender] -= totalCost;
        
        uint256 orderId = nextOrderId++;
        orders[orderId] = Order({
            trader: msg.sender,
            isBuy: true,
            platform: platform,
            amount: amount,
            price: price,
            timestamp: block.timestamp,
            active: true
        });
        
        emit OrderCreated(orderId, msg.sender, true, platform, amount, price);
        return orderId;
    }
    
    // 创建卖单
    function createSellOrder(string calldata platform, uint256 amount, uint256 price) external returns (uint256) {
        require(tokenBalances[msg.sender][platform] >= amount, "Insufficient token balance");
        
        // 锁定Token
        tokenBalances[msg.sender][platform] -= amount;
        
        uint256 orderId = nextOrderId++;
        orders[orderId] = Order({
            trader: msg.sender,
            isBuy: false,
            platform: platform,
            amount: amount,
            price: price,
            timestamp: block.timestamp,
            active: true
        });
        
        emit OrderCreated(orderId, msg.sender, false, platform, amount, price);
        return orderId;
    }
    
    // 执行交易 (原子化结算)
    function executeTrade(uint256 orderId, uint256 tradeAmount) external {
        Order storage order = orders[orderId];
        require(order.active, "Order not active");
        require(tradeAmount <= order.amount, "Trade amount exceeds order");
        require(tradeAmount > 0, "Invalid trade amount");
        
        uint256 totalCost = tradeAmount * order.price;
        uint256 fee = (totalCost * platformFee) / 10000;
        
        if (order.isBuy) {
            // 买单: 卖方需要提供Token, 买方已经锁定ETH
            require(tokenBalances[msg.sender][order.platform] >= tradeAmount, "Insufficient tokens");
            
            // 原子交换
            tokenBalances[msg.sender][order.platform] -= tradeAmount;
            tokenBalances[order.trader][order.platform] += tradeAmount;
            
            // 释放ETH给卖方
            balances[msg.sender] += totalCost - fee;
            
        } else {
            // 卖单: 买方需要提供ETH, 卖方已经锁定Token
            require(balances[msg.sender] >= totalCost, "Insufficient ETH");
            
            // 原子交换
            balances[msg.sender] -= totalCost;
            balances[order.trader] += totalCost - fee;
            
            // 释放Token给买方
            tokenBalances[msg.sender][order.platform] += tradeAmount;
        }
        
        // 更新订单
        order.amount -= tradeAmount;
        if (order.amount == 0) {
            order.active = false;
        }
        
        // 记录交易
        Trade memory trade = Trade({
            orderId: orderId,
            buyer: order.isBuy ? order.trader : msg.sender,
            seller: order.isBuy ? msg.sender : order.trader,
            platform: order.platform,
            amount: tradeAmount,
            price: order.price,
            total: totalCost,
            timestamp: block.timestamp
        });
        
        tradeHistory[order.trader].push(trade);
        tradeHistory[msg.sender].push(trade);
        
        emit TradeExecuted(orderId, trade.buyer, trade.seller, order.platform, tradeAmount, totalCost);
    }
    
    // 取消订单
    function cancelOrder(uint256 orderId) external {
        Order storage order = orders[orderId];
        require(order.trader == msg.sender, "Not order owner");
        require(order.active, "Order not active");
        
        order.active = false;
        
        // 释放锁定资产
        if (order.isBuy) {
            uint256 refund = order.amount * order.price;
            balances[msg.sender] += refund;
        } else {
            tokenBalances[msg.sender][order.platform] += order.amount;
        }
        
        emit OrderCancelled(orderId);
    }
    
    // 获取订单簿
    function getOrderBook(string calldata platform, bool isBuy) external view returns (uint256[] memory) {
        // 简化实现，实际应该返回排序后的订单ID列表
        uint256 count = 0;
        for (uint256 i = 1; i < nextOrderId; i++) {
            if (orders[i].active && 
                keccak256(bytes(orders[i].platform)) == keccak256(bytes(platform)) &&
                orders[i].isBuy == isBuy) {
                count++;
            }
        }
        
        uint256[] memory result = new uint256[](count);
        uint256 idx = 0;
        for (uint256 i = 1; i < nextOrderId; i++) {
            if (orders[i].active && 
                keccak256(bytes(orders[i].platform)) == keccak256(bytes(platform)) &&
                orders[i].isBuy == isBuy) {
                result[idx] = i;
                idx++;
            }
        }
        
        return result;
    }
    
    // 设置平台费率
    function setPlatformFee(uint256 newFee) external {
        require(msg.sender == owner, "Only owner");
        require(newFee <= 500, "Fee too high");  // 最大5%
        platformFee = newFee;
    }
    
    // 提取平台手续费
    function withdrawFees() external {
        require(msg.sender == owner, "Only owner");
        // 实际实现需要跟踪手续费余额
    }
}
