class WatchlistItem {
  final String stockId;
  final String name;
  final double currentPrice;
  final double changePercent;
  final DateTime addedAt;
  final String? notes;

  WatchlistItem({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.changePercent,
    required this.addedAt,
    this.notes,
  });

  factory WatchlistItem.fromJson(Map<String, dynamic> json) {
    return WatchlistItem(
      stockId: json['stock_id'] ?? '',
      name: json['name'] ?? '',
      currentPrice: (json['current_price'] != null)
          ? (json['current_price'] is String
              ? double.tryParse(json['current_price']) ?? 0.0
              : (json['current_price'] as num).toDouble())
          : 0.0,
      changePercent: (json['change_percent'] != null)
          ? (json['change_percent'] is String
              ? double.tryParse(json['change_percent']) ?? 0.0
              : (json['change_percent'] as num).toDouble())
          : 0.0,
      addedAt: DateTime.parse(json['added_at']),
      notes: json['notes'],
    );
  }

  bool get isUp => changePercent > 0;
  bool get isDown => changePercent < 0;
}
