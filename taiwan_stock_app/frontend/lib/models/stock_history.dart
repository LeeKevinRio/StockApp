class StockHistory {
  final DateTime date;
  final double open;
  final double high;
  final double low;
  final double close;
  final int volume;

  StockHistory({
    required this.date,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
  });

  factory StockHistory.fromJson(Map<String, dynamic> json) {
    // Handle volume that might be int or double
    int volumeValue;
    if (json['volume'] is int) {
      volumeValue = json['volume'];
    } else if (json['volume'] is double) {
      volumeValue = (json['volume'] as double).toInt();
    } else {
      volumeValue = int.tryParse(json['volume'].toString()) ?? 0;
    }

    return StockHistory(
      date: DateTime.parse(json['date']),
      open: (json['open'] as num).toDouble(),
      high: (json['high'] as num).toDouble(),
      low: (json['low'] as num).toDouble(),
      close: (json['close'] as num).toDouble(),
      volume: volumeValue,
    );
  }

  /// Returns true if close >= open (rising or flat)
  bool get isRising => close >= open;

  /// Returns the change from open to close
  double get change => close - open;

  /// Returns the change percent from open to close
  double get changePercent => open != 0 ? ((close - open) / open) * 100 : 0;

  Map<String, dynamic> toJson() {
    final dateStr = '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
    return {
      'date': dateStr,
      'open': open,
      'high': high,
      'low': low,
      'close': close,
      'volume': volume,
    };
  }
}
