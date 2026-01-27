class Stock {
  final String stockId;
  final String name;
  final String? market;
  final String? industry;
  final String marketRegion;  // 'TW' or 'US'
  final String? sector;  // For US stocks
  final String? exchange;  // Exchange name

  Stock({
    required this.stockId,
    required this.name,
    this.market,
    this.industry,
    this.marketRegion = 'TW',
    this.sector,
    this.exchange,
  });

  factory Stock.fromJson(Map<String, dynamic> json) {
    return Stock(
      stockId: json['stock_id'] ?? json['symbol'] ?? '',
      name: json['name'] ?? '',
      market: json['market'],
      industry: json['industry'],
      marketRegion: json['market_region'] ?? 'TW',
      sector: json['sector'],
      exchange: json['exchange'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'stock_id': stockId,
      'name': name,
      'market': market,
      'industry': industry,
      'market_region': marketRegion,
      'sector': sector,
      'exchange': exchange,
    };
  }

  /// Check if this is a US stock
  bool get isUSStock => marketRegion.toUpperCase() == 'US';

  /// Check if this is a Taiwan stock
  bool get isTaiwanStock => marketRegion.toUpperCase() == 'TW';

  /// Get currency symbol
  String get currencySymbol => isUSStock ? '\$' : 'NT\$';

  /// Get currency code
  String get currencyCode => isUSStock ? 'USD' : 'TWD';
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
  final String marketRegion;
  final String currency;

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
    this.marketRegion = 'TW',
    this.currency = 'TWD',
  });

  factory StockPrice.fromJson(Map<String, dynamic> json) {
    return StockPrice(
      stockId: json['stock_id'] ?? '',
      name: json['name'] ?? '',
      currentPrice: (json['current_price'] as num?)?.toDouble() ?? 0.0,
      change: (json['change'] as num?)?.toDouble() ?? 0.0,
      changePercent: (json['change_percent'] as num?)?.toDouble() ?? 0.0,
      open: (json['open'] as num?)?.toDouble() ?? 0.0,
      high: (json['high'] as num?)?.toDouble() ?? 0.0,
      low: (json['low'] as num?)?.toDouble() ?? 0.0,
      volume: json['volume'] ?? 0,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : DateTime.now(),
      marketRegion: json['market_region'] ?? 'TW',
      currency: json['currency'] ?? 'TWD',
    );
  }

  bool get isUp => change > 0;
  bool get isDown => change < 0;
  bool get isUSStock => marketRegion.toUpperCase() == 'US';
  String get currencySymbol => isUSStock ? '\$' : 'NT\$';
}
