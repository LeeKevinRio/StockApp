/// 模擬交易模型

class VirtualAccount {
  final int id;
  final int userId;
  final double initialBalance;
  final double cashBalance;
  final double totalValue;
  final double totalProfitLoss;
  final double totalProfitLossPercent;
  final DateTime? createdAt;

  VirtualAccount({
    required this.id,
    required this.userId,
    required this.initialBalance,
    required this.cashBalance,
    required this.totalValue,
    required this.totalProfitLoss,
    required this.totalProfitLossPercent,
    this.createdAt,
  });

  factory VirtualAccount.fromJson(Map<String, dynamic> json) {
    return VirtualAccount(
      id: json['id'],
      userId: json['user_id'],
      initialBalance: (json['initial_balance'] ?? 0).toDouble(),
      cashBalance: (json['cash_balance'] ?? 0).toDouble(),
      totalValue: (json['total_value'] ?? 0).toDouble(),
      totalProfitLoss: (json['total_profit_loss'] ?? 0).toDouble(),
      totalProfitLossPercent: (json['total_profit_loss_percent'] ?? 0).toDouble(),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'])
          : null,
    );
  }
}

class VirtualPosition {
  final int id;
  final String stockId;
  final String? stockName;
  final int quantity;
  final double avgCost;
  final double? currentPrice;
  final double? marketValue;
  final double unrealizedPnl;
  final double unrealizedPnlPercent;

  VirtualPosition({
    required this.id,
    required this.stockId,
    this.stockName,
    required this.quantity,
    required this.avgCost,
    this.currentPrice,
    this.marketValue,
    required this.unrealizedPnl,
    required this.unrealizedPnlPercent,
  });

  factory VirtualPosition.fromJson(Map<String, dynamic> json) {
    return VirtualPosition(
      id: json['id'],
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      quantity: json['quantity'] ?? 0,
      avgCost: (json['avg_cost'] ?? 0).toDouble(),
      currentPrice: json['current_price']?.toDouble(),
      marketValue: json['market_value']?.toDouble(),
      unrealizedPnl: (json['unrealized_pnl'] ?? 0).toDouble(),
      unrealizedPnlPercent: (json['unrealized_pnl_percent'] ?? 0).toDouble(),
    );
  }

  bool get isProfit => unrealizedPnl > 0;
  bool get isLoss => unrealizedPnl < 0;
}

class VirtualOrder {
  final int id;
  final String stockId;
  final String? stockName;
  final String orderType;
  final int quantity;
  final double price;
  final int filledQuantity;
  final double? filledPrice;
  final String status;
  final DateTime? createdAt;
  final DateTime? filledAt;

  VirtualOrder({
    required this.id,
    required this.stockId,
    this.stockName,
    required this.orderType,
    required this.quantity,
    required this.price,
    required this.filledQuantity,
    this.filledPrice,
    required this.status,
    this.createdAt,
    this.filledAt,
  });

  factory VirtualOrder.fromJson(Map<String, dynamic> json) {
    return VirtualOrder(
      id: json['id'],
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      orderType: json['order_type'],
      quantity: json['quantity'] ?? 0,
      price: (json['price'] ?? 0).toDouble(),
      filledQuantity: json['filled_quantity'] ?? 0,
      filledPrice: json['filled_price']?.toDouble(),
      status: json['status'] ?? 'PENDING',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'])
          : null,
      filledAt: json['filled_at'] != null
          ? DateTime.tryParse(json['filled_at'])
          : null,
    );
  }

  bool get isBuy => orderType == 'BUY';
  bool get isSell => orderType == 'SELL';
  bool get isFilled => status == 'FILLED';
  bool get isPending => status == 'PENDING';
}

class AccountSummary {
  final VirtualAccount account;
  final List<VirtualPosition> positions;
  final List<VirtualOrder> recentOrders;

  AccountSummary({
    required this.account,
    required this.positions,
    required this.recentOrders,
  });

  factory AccountSummary.fromJson(Map<String, dynamic> json) {
    return AccountSummary(
      account: VirtualAccount.fromJson(json['account']),
      positions: (json['positions'] as List?)
              ?.map((e) => VirtualPosition.fromJson(e))
              .toList() ??
          [],
      recentOrders: (json['recent_orders'] as List?)
              ?.map((e) => VirtualOrder.fromJson(e))
              .toList() ??
          [],
    );
  }
}
