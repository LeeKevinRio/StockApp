class WatchlistItem {
  final String stockId;
  final String name;
  final String? market;
  final String? industry;
  final double? currentPrice;
  final double? change;
  final double? changePercent;
  final int? volume;
  final DateTime? addedAt;
  final String? notes;
  final String marketRegion;  // 'TW' or 'US'
  final String currency;  // 'TWD' or 'USD'

  WatchlistItem({
    required this.stockId,
    required this.name,
    this.market,
    this.industry,
    this.currentPrice,
    this.change,
    this.changePercent,
    this.volume,
    this.addedAt,
    this.notes,
    this.marketRegion = 'TW',
    this.currency = 'TWD',
  });

  factory WatchlistItem.fromJson(Map<String, dynamic> json) {
    return WatchlistItem(
      stockId: json['stock_id'] ?? '',
      name: json['name'] ?? '',
      market: json['market'],
      industry: json['industry'],
      currentPrice: (json['current_price'] != null)
          ? (json['current_price'] is String
              ? double.tryParse(json['current_price']) ?? 0.0
              : (json['current_price'] as num).toDouble())
          : null,
      change: (json['change'] != null)
          ? (json['change'] is String
              ? double.tryParse(json['change']) ?? 0.0
              : (json['change'] as num).toDouble())
          : null,
      changePercent: (json['change_percent'] != null)
          ? (json['change_percent'] is String
              ? double.tryParse(json['change_percent']) ?? 0.0
              : (json['change_percent'] as num).toDouble())
          : null,
      volume: json['volume'],
      addedAt: json['added_at'] != null ? DateTime.parse(json['added_at']) : null,
      notes: json['notes'],
      marketRegion: json['market_region'] ?? 'TW',
      currency: json['currency'] ?? 'TWD',
    );
  }

  bool get isUp => (changePercent ?? 0) > 0;
  bool get isDown => (changePercent ?? 0) < 0;
  bool get isUSStock => marketRegion.toUpperCase() == 'US';
  String get currencySymbol => isUSStock ? '\$' : 'NT\$';
}
