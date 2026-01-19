class Stock {
  final String stockId;
  final String name;
  final String market;
  final String? industry;

  Stock({
    required this.stockId,
    required this.name,
    required this.market,
    this.industry,
  });

  factory Stock.fromJson(Map<String, dynamic> json) {
    return Stock(
      stockId: json['stock_id'],
      name: json['name'],
      market: json['market'],
      industry: json['industry'],
    );
  }
}

class StockPrice {
  final String stockId;
  final String name;
  final double currentPrice;
  final double change;
  final double changePercent;
  final double open;
  final double high;
  final double low;
  final int volume;
  final DateTime updatedAt;

  StockPrice({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.change,
    required this.changePercent,
    required this.open,
    required this.high,
    required this.low,
    required this.volume,
    required this.updatedAt,
  });

  factory StockPrice.fromJson(Map<String, dynamic> json) {
    return StockPrice(
      stockId: json['stock_id'],
      name: json['name'],
      currentPrice: (json['current_price'] as num).toDouble(),
      change: (json['change'] as num).toDouble(),
      changePercent: (json['change_percent'] as num).toDouble(),
      open: (json['open'] as num).toDouble(),
      high: (json['high'] as num).toDouble(),
      low: (json['low'] as num).toDouble(),
      volume: json['volume'],
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  bool get isUp => change > 0;
  bool get isDown => change < 0;
}
