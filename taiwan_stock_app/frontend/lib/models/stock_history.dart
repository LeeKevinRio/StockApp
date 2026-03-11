class StockHistory {
  final DateTime date;
  final double open;
  final double high;
  final double low;
  final double close;
  final int volume;

  /// 前一根 K 棒的收盤價（用於計算日漲跌幅）
  final double? prevClose;

  StockHistory({
    required this.date,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
    this.prevClose,
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

  /// 從 JSON list 建立並自動填入 prevClose
  static List<StockHistory> fromJsonList(List<dynamic> jsonList) {
    final items = jsonList.map((j) => StockHistory.fromJson(j as Map<String, dynamic>)).toList();
    if (items.length <= 1) return items;
    // 為每筆資料補上前一根的收盤價
    final result = <StockHistory>[items.first];
    for (int i = 1; i < items.length; i++) {
      final item = items[i];
      result.add(StockHistory(
        date: item.date,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume,
        prevClose: items[i - 1].close,
      ));
    }
    return result;
  }

  /// Returns true if close >= open (K 棒本體方向)
  bool get isRising => close >= open;

  /// 日漲跌（相較前一日收盤，無前日資料則用開盤）
  double get change => close - (prevClose ?? open);

  /// 日漲跌幅 %（相較前一日收盤）
  double get changePercent {
    final base = prevClose ?? open;
    return base != 0 ? ((close - base) / base) * 100 : 0;
  }

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
