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
      stockId: json['stock_id'],
      name: json['name'],
      currentPrice: (json['current_price'] as num).toDouble(),
      changePercent: (json['change_percent'] as num).toDouble(),
      addedAt: DateTime.parse(json['added_at']),
      notes: json['notes'],
    );
  }

  bool get isUp => changePercent > 0;
  bool get isDown => changePercent < 0;
}
