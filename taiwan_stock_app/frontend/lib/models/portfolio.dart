/// 投資組合數據模型
/// 專業級高風險交易分析平台

/// 投資組合
class Portfolio {
  final int id;
  final int userId;
  final String name;
  final String? description;
  final double initialCapital;
  final DateTime createdAt;
  final DateTime updatedAt;
  final double totalValue;
  final double totalCost;
  final double totalPnl;
  final double totalPnlPercent;
  final int positionsCount;

  Portfolio({
    required this.id,
    required this.userId,
    required this.name,
    this.description,
    required this.initialCapital,
    required this.createdAt,
    required this.updatedAt,
    required this.totalValue,
    required this.totalCost,
    required this.totalPnl,
    required this.totalPnlPercent,
    required this.positionsCount,
  });

  factory Portfolio.fromJson(Map<String, dynamic> json) {
    return Portfolio(
      id: json['id'],
      userId: json['user_id'],
      name: json['name'],
      description: json['description'],
      initialCapital: (json['initial_capital'] as num).toDouble(),
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      totalValue: (json['total_value'] as num?)?.toDouble() ?? 0,
      totalCost: (json['total_cost'] as num?)?.toDouble() ?? 0,
      totalPnl: (json['total_pnl'] as num?)?.toDouble() ?? 0,
      totalPnlPercent: (json['total_pnl_percent'] as num?)?.toDouble() ?? 0,
      positionsCount: json['positions_count'] ?? 0,
    );
  }

  /// 是否獲利
  bool get isProfitable => totalPnl > 0;

  /// 是否虧損
  bool get isLosing => totalPnl < 0;

  /// 現金餘額
  double get cashBalance => initialCapital - totalCost;
}

/// 投資組合列表響應
class PortfolioListResponse {
  final List<Portfolio> portfolios;
  final int total;

  PortfolioListResponse({
    required this.portfolios,
    required this.total,
  });

  factory PortfolioListResponse.fromJson(Map<String, dynamic> json) {
    return PortfolioListResponse(
      portfolios: (json['portfolios'] as List)
          .map((e) => Portfolio.fromJson(e))
          .toList(),
      total: json['total'],
    );
  }
}

/// 持倉
class Position {
  final int id;
  final int portfolioId;
  final String stockId;
  final String stockName;
  final int quantity;
  final double avgCost;
  final double currentPrice;
  final double marketValue;
  final double unrealizedPnl;
  final double unrealizedPnlPercent;
  final DateTime lastUpdated;

  Position({
    required this.id,
    required this.portfolioId,
    required this.stockId,
    required this.stockName,
    required this.quantity,
    required this.avgCost,
    required this.currentPrice,
    required this.marketValue,
    required this.unrealizedPnl,
    required this.unrealizedPnlPercent,
    required this.lastUpdated,
  });

  factory Position.fromJson(Map<String, dynamic> json) {
    return Position(
      id: json['id'],
      portfolioId: json['portfolio_id'],
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      quantity: json['quantity'],
      avgCost: (json['avg_cost'] as num).toDouble(),
      currentPrice: (json['current_price'] as num).toDouble(),
      marketValue: (json['market_value'] as num).toDouble(),
      unrealizedPnl: (json['unrealized_pnl'] as num).toDouble(),
      unrealizedPnlPercent: (json['unrealized_pnl_percent'] as num).toDouble(),
      lastUpdated: DateTime.parse(json['last_updated']),
    );
  }

  /// 是否獲利
  bool get isProfitable => unrealizedPnl > 0;

  /// 是否虧損
  bool get isLosing => unrealizedPnl < 0;

  /// 成本總額
  double get totalCost => avgCost * quantity;
}

/// 持倉列表響應
class PositionListResponse {
  final List<Position> positions;
  final int total;

  PositionListResponse({
    required this.positions,
    required this.total,
  });

  factory PositionListResponse.fromJson(Map<String, dynamic> json) {
    return PositionListResponse(
      positions: (json['positions'] as List)
          .map((e) => Position.fromJson(e))
          .toList(),
      total: json['total'],
    );
  }
}

/// 交易類型
enum TransactionType {
  buy,
  sell;

  String get displayName {
    switch (this) {
      case TransactionType.buy:
        return '買入';
      case TransactionType.sell:
        return '賣出';
    }
  }

  String get value {
    switch (this) {
      case TransactionType.buy:
        return 'buy';
      case TransactionType.sell:
        return 'sell';
    }
  }

  static TransactionType fromString(String value) {
    switch (value) {
      case 'buy':
        return TransactionType.buy;
      case 'sell':
        return TransactionType.sell;
      default:
        return TransactionType.buy;
    }
  }
}

/// 交易記錄
class Transaction {
  final int id;
  final int portfolioId;
  final String stockId;
  final String stockName;
  final TransactionType transactionType;
  final int quantity;
  final double price;
  final double fee;
  final double tax;
  final double totalAmount;
  final String? notes;
  final DateTime transactionDate;
  final DateTime createdAt;

  Transaction({
    required this.id,
    required this.portfolioId,
    required this.stockId,
    required this.stockName,
    required this.transactionType,
    required this.quantity,
    required this.price,
    required this.fee,
    required this.tax,
    required this.totalAmount,
    this.notes,
    required this.transactionDate,
    required this.createdAt,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'],
      portfolioId: json['portfolio_id'],
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      transactionType: TransactionType.fromString(json['transaction_type']),
      quantity: json['quantity'],
      price: (json['price'] as num).toDouble(),
      fee: (json['fee'] as num?)?.toDouble() ?? 0,
      tax: (json['tax'] as num?)?.toDouble() ?? 0,
      totalAmount: (json['total_amount'] as num).toDouble(),
      notes: json['notes'],
      transactionDate: DateTime.parse(json['transaction_date']),
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  /// 是否為買入
  bool get isBuy => transactionType == TransactionType.buy;

  /// 是否為賣出
  bool get isSell => transactionType == TransactionType.sell;
}

/// 交易列表響應
class TransactionListResponse {
  final List<Transaction> transactions;
  final int total;

  TransactionListResponse({
    required this.transactions,
    required this.total,
  });

  factory TransactionListResponse.fromJson(Map<String, dynamic> json) {
    return TransactionListResponse(
      transactions: (json['transactions'] as List)
          .map((e) => Transaction.fromJson(e))
          .toList(),
      total: json['total'],
    );
  }
}

/// 投資組合摘要
class PortfolioSummary {
  final double totalValue;
  final double totalCost;
  final double totalPnl;
  final double totalPnlPercent;
  final double cashBalance;
  final int positionsCount;
  final int winningPositions;
  final int losingPositions;
  final String? bestPerformer;
  final String? worstPerformer;

  PortfolioSummary({
    required this.totalValue,
    required this.totalCost,
    required this.totalPnl,
    required this.totalPnlPercent,
    required this.cashBalance,
    required this.positionsCount,
    required this.winningPositions,
    required this.losingPositions,
    this.bestPerformer,
    this.worstPerformer,
  });

  factory PortfolioSummary.fromJson(Map<String, dynamic> json) {
    return PortfolioSummary(
      totalValue: (json['total_value'] as num).toDouble(),
      totalCost: (json['total_cost'] as num).toDouble(),
      totalPnl: (json['total_pnl'] as num).toDouble(),
      totalPnlPercent: (json['total_pnl_percent'] as num).toDouble(),
      cashBalance: (json['cash_balance'] as num).toDouble(),
      positionsCount: json['positions_count'],
      winningPositions: json['winning_positions'] ?? 0,
      losingPositions: json['losing_positions'] ?? 0,
      bestPerformer: json['best_performer'],
      worstPerformer: json['worst_performer'],
    );
  }

  /// 勝率
  double get winRate {
    final total = winningPositions + losingPositions;
    return total > 0 ? winningPositions / total * 100 : 0;
  }
}

/// 持倉配置
class PositionAllocation {
  final String stockId;
  final String stockName;
  final double marketValue;
  final double weight;

  PositionAllocation({
    required this.stockId,
    required this.stockName,
    required this.marketValue,
    required this.weight,
  });

  factory PositionAllocation.fromJson(Map<String, dynamic> json) {
    return PositionAllocation(
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      marketValue: (json['market_value'] as num).toDouble(),
      weight: (json['weight'] as num).toDouble(),
    );
  }
}

/// 創建投資組合請求
class CreatePortfolioRequest {
  final String name;
  final String? description;
  final double initialCapital;

  CreatePortfolioRequest({
    required this.name,
    this.description,
    required this.initialCapital,
  });

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      if (description != null) 'description': description,
      'initial_capital': initialCapital,
    };
  }
}

/// 投資組合詳情（含持股列表）
class PortfolioDetail {
  final int id;
  final String name;
  final String? description;
  final double totalValue;
  final double totalCost;
  final double totalPnl;
  final double totalPnlPercent;
  final List<PortfolioHolding> holdings;

  PortfolioDetail({
    required this.id,
    required this.name,
    this.description,
    required this.totalValue,
    required this.totalCost,
    required this.totalPnl,
    required this.totalPnlPercent,
    required this.holdings,
  });

  factory PortfolioDetail.fromPortfolioAndPositions(
    Portfolio portfolio,
    List<Position> positions,
  ) {
    return PortfolioDetail(
      id: portfolio.id,
      name: portfolio.name,
      description: portfolio.description,
      totalValue: portfolio.totalValue,
      totalCost: portfolio.totalCost,
      totalPnl: portfolio.totalPnl,
      totalPnlPercent: portfolio.totalPnlPercent,
      holdings: positions.map((p) => PortfolioHolding.fromPosition(p)).toList(),
    );
  }
}

/// 投資組合持股
class PortfolioHolding {
  final int id;
  final String stockId;
  final String? stockName;
  final int quantity;
  final double avgCost;
  final double? currentPrice;
  final double? marketValue;
  final double? unrealizedPnl;
  final double? unrealizedPnlPercent;

  PortfolioHolding({
    required this.id,
    required this.stockId,
    this.stockName,
    required this.quantity,
    required this.avgCost,
    this.currentPrice,
    this.marketValue,
    this.unrealizedPnl,
    this.unrealizedPnlPercent,
  });

  factory PortfolioHolding.fromPosition(Position position) {
    return PortfolioHolding(
      id: position.id,
      stockId: position.stockId,
      stockName: position.stockName,
      quantity: position.quantity,
      avgCost: position.avgCost,
      currentPrice: position.currentPrice,
      marketValue: position.marketValue,
      unrealizedPnl: position.unrealizedPnl,
      unrealizedPnlPercent: position.unrealizedPnlPercent,
    );
  }
}

/// 創建交易請求
class CreateTransactionRequest {
  final String stockId;
  final String stockName;
  final TransactionType transactionType;
  final int quantity;
  final double price;
  final double fee;
  final double tax;
  final String? notes;
  final DateTime? transactionDate;

  CreateTransactionRequest({
    required this.stockId,
    required this.stockName,
    required this.transactionType,
    required this.quantity,
    required this.price,
    this.fee = 0,
    this.tax = 0,
    this.notes,
    this.transactionDate,
  });

  Map<String, dynamic> toJson() {
    return {
      'stock_id': stockId,
      'stock_name': stockName,
      'transaction_type': transactionType.value,
      'quantity': quantity,
      'price': price,
      'fee': fee,
      'tax': tax,
      if (notes != null) 'notes': notes,
      if (transactionDate != null)
        'transaction_date': transactionDate!.toIso8601String(),
    };
  }
}
