class Portfolio {
  final int id;
  final int userId;
  final String name;
  final String? description;
  final bool isDefault;
  final DateTime createdAt;
  final DateTime updatedAt;

  Portfolio({
    required this.id,
    required this.userId,
    required this.name,
    this.description,
    required this.isDefault,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Portfolio.fromJson(Map<String, dynamic> json) {
    return Portfolio(
      id: json['id'],
      userId: json['user_id'],
      name: json['name'],
      description: json['description'],
      isDefault: json['is_default'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}

class PortfolioHolding {
  final int id;
  final int portfolioId;
  final String stockId;
  final int quantity;
  final double avgCost;
  final DateTime buyDate;
  final String? notes;
  final String? stockName;
  final double? currentPrice;
  final double? marketValue;
  final double? unrealizedPnl;
  final double? unrealizedPnlPercent;
  final DateTime createdAt;

  PortfolioHolding({
    required this.id,
    required this.portfolioId,
    required this.stockId,
    required this.quantity,
    required this.avgCost,
    required this.buyDate,
    this.notes,
    this.stockName,
    this.currentPrice,
    this.marketValue,
    this.unrealizedPnl,
    this.unrealizedPnlPercent,
    required this.createdAt,
  });

  factory PortfolioHolding.fromJson(Map<String, dynamic> json) {
    return PortfolioHolding(
      id: json['id'],
      portfolioId: json['portfolio_id'],
      stockId: json['stock_id'],
      quantity: json['quantity'],
      avgCost: double.parse(json['avg_cost'].toString()),
      buyDate: DateTime.parse(json['buy_date']),
      notes: json['notes'],
      stockName: json['stock_name'],
      currentPrice: json['current_price'] != null
          ? double.parse(json['current_price'].toString())
          : null,
      marketValue: json['market_value'] != null
          ? double.parse(json['market_value'].toString())
          : null,
      unrealizedPnl: json['unrealized_pnl'] != null
          ? double.parse(json['unrealized_pnl'].toString())
          : null,
      unrealizedPnlPercent: json['unrealized_pnl_percent'] != null
          ? double.parse(json['unrealized_pnl_percent'].toString())
          : null,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  double get totalCost => quantity * avgCost;
}

class PortfolioSummary {
  final int id;
  final String name;
  final double totalCost;
  final double totalValue;
  final double totalPnl;
  final double totalPnlPercent;
  final int holdingsCount;

  PortfolioSummary({
    required this.id,
    required this.name,
    required this.totalCost,
    required this.totalValue,
    required this.totalPnl,
    required this.totalPnlPercent,
    required this.holdingsCount,
  });

  factory PortfolioSummary.fromJson(Map<String, dynamic> json) {
    return PortfolioSummary(
      id: json['id'],
      name: json['name'],
      totalCost: double.parse(json['total_cost'].toString()),
      totalValue: double.parse(json['total_value'].toString()),
      totalPnl: double.parse(json['total_pnl'].toString()),
      totalPnlPercent: double.parse(json['total_pnl_percent'].toString()),
      holdingsCount: json['holdings_count'],
    );
  }
}

class PortfolioDetail {
  final int id;
  final int userId;
  final String name;
  final String? description;
  final bool isDefault;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<PortfolioHolding> holdings;
  final double totalCost;
  final double totalValue;
  final double totalPnl;
  final double totalPnlPercent;

  PortfolioDetail({
    required this.id,
    required this.userId,
    required this.name,
    this.description,
    required this.isDefault,
    required this.createdAt,
    required this.updatedAt,
    required this.holdings,
    required this.totalCost,
    required this.totalValue,
    required this.totalPnl,
    required this.totalPnlPercent,
  });

  factory PortfolioDetail.fromJson(Map<String, dynamic> json) {
    return PortfolioDetail(
      id: json['id'],
      userId: json['user_id'],
      name: json['name'],
      description: json['description'],
      isDefault: json['is_default'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      holdings: (json['holdings'] as List)
          .map((h) => PortfolioHolding.fromJson(h))
          .toList(),
      totalCost: double.parse(json['total_cost'].toString()),
      totalValue: double.parse(json['total_value'].toString()),
      totalPnl: double.parse(json['total_pnl'].toString()),
      totalPnlPercent: double.parse(json['total_pnl_percent'].toString()),
    );
  }
}

class PortfolioSnapshot {
  final DateTime date;
  final double totalValue;
  final double totalCost;
  final double? dailyReturn;
  final double? totalReturn;

  PortfolioSnapshot({
    required this.date,
    required this.totalValue,
    required this.totalCost,
    this.dailyReturn,
    this.totalReturn,
  });

  factory PortfolioSnapshot.fromJson(Map<String, dynamic> json) {
    return PortfolioSnapshot(
      date: DateTime.parse(json['date']),
      totalValue: double.parse(json['total_value'].toString()),
      totalCost: double.parse(json['total_cost'].toString()),
      dailyReturn: json['daily_return'] != null
          ? double.parse(json['daily_return'].toString())
          : null,
      totalReturn: json['total_return'] != null
          ? double.parse(json['total_return'].toString())
          : null,
    );
  }
}

class PortfolioPerformance {
  final int portfolioId;
  final String portfolioName;
  final int periodDays;
  final double startValue;
  final double endValue;
  final double absoluteReturn;
  final double percentReturn;
  final double? benchmarkReturn;
  final double? alpha;
  final List<PortfolioSnapshot> snapshots;

  PortfolioPerformance({
    required this.portfolioId,
    required this.portfolioName,
    required this.periodDays,
    required this.startValue,
    required this.endValue,
    required this.absoluteReturn,
    required this.percentReturn,
    this.benchmarkReturn,
    this.alpha,
    required this.snapshots,
  });

  factory PortfolioPerformance.fromJson(Map<String, dynamic> json) {
    return PortfolioPerformance(
      portfolioId: json['portfolio_id'],
      portfolioName: json['portfolio_name'],
      periodDays: json['period_days'],
      startValue: double.parse(json['start_value'].toString()),
      endValue: double.parse(json['end_value'].toString()),
      absoluteReturn: double.parse(json['absolute_return'].toString()),
      percentReturn: double.parse(json['percent_return'].toString()),
      benchmarkReturn: json['benchmark_return'] != null
          ? double.parse(json['benchmark_return'].toString())
          : null,
      alpha: json['alpha'] != null
          ? double.parse(json['alpha'].toString())
          : null,
      snapshots: (json['snapshots'] as List)
          .map((s) => PortfolioSnapshot.fromJson(s))
          .toList(),
    );
  }
}

class PortfolioAllocation {
  final String stockId;
  final String stockName;
  final double marketValue;
  final double weight;

  PortfolioAllocation({
    required this.stockId,
    required this.stockName,
    required this.marketValue,
    required this.weight,
  });

  factory PortfolioAllocation.fromJson(Map<String, dynamic> json) {
    return PortfolioAllocation(
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      marketValue: double.parse(json['market_value'].toString()),
      weight: double.parse(json['weight'].toString()),
    );
  }
}
