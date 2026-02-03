/// 技術指標數據模型

class IndicatorDataPoint {
  final DateTime date;
  final double? value;

  IndicatorDataPoint({required this.date, this.value});

  factory IndicatorDataPoint.fromJson(Map<String, dynamic> json) {
    return IndicatorDataPoint(
      date: DateTime.parse(json['date']),
      value: json['value'] != null
          ? double.parse(json['value'].toString())
          : null,
    );
  }
}

class MACDDataPoint {
  final DateTime date;
  final double? macd;
  final double? signal;
  final double? histogram;

  MACDDataPoint({
    required this.date,
    this.macd,
    this.signal,
    this.histogram,
  });

  factory MACDDataPoint.fromJson(Map<String, dynamic> json) {
    return MACDDataPoint(
      date: DateTime.parse(json['date']),
      macd: json['macd'] != null
          ? double.parse(json['macd'].toString())
          : null,
      signal: json['signal'] != null
          ? double.parse(json['signal'].toString())
          : null,
      histogram: json['histogram'] != null
          ? double.parse(json['histogram'].toString())
          : null,
    );
  }
}

class BollingerDataPoint {
  final DateTime date;
  final double? upper;
  final double? middle;
  final double? lower;
  final double? close;

  BollingerDataPoint({
    required this.date,
    this.upper,
    this.middle,
    this.lower,
    this.close,
  });

  factory BollingerDataPoint.fromJson(Map<String, dynamic> json) {
    return BollingerDataPoint(
      date: DateTime.parse(json['date']),
      upper: json['upper'] != null
          ? double.parse(json['upper'].toString())
          : null,
      middle: json['middle'] != null
          ? double.parse(json['middle'].toString())
          : null,
      lower: json['lower'] != null
          ? double.parse(json['lower'].toString())
          : null,
      close: json['close'] != null
          ? double.parse(json['close'].toString())
          : null,
    );
  }
}

class KDDataPoint {
  final DateTime date;
  final double? k;
  final double? d;

  KDDataPoint({required this.date, this.k, this.d});

  factory KDDataPoint.fromJson(Map<String, dynamic> json) {
    return KDDataPoint(
      date: DateTime.parse(json['date']),
      k: json['k'] != null ? double.parse(json['k'].toString()) : null,
      d: json['d'] != null ? double.parse(json['d'].toString()) : null,
    );
  }
}

class AllIndicatorsData {
  final String stockId;
  final Map<String, dynamic> latest;
  final List<IndicatorDataPoint> rsi;
  final List<MACDDataPoint> macd;
  final List<BollingerDataPoint> bollinger;
  final List<KDDataPoint> kd;

  AllIndicatorsData({
    required this.stockId,
    required this.latest,
    required this.rsi,
    required this.macd,
    required this.bollinger,
    required this.kd,
  });

  factory AllIndicatorsData.fromJson(Map<String, dynamic> json) {
    return AllIndicatorsData(
      stockId: json['stock_id'],
      latest: Map<String, dynamic>.from(json['latest'] ?? {}),
      rsi: (json['rsi'] as List)
          .map((e) => IndicatorDataPoint.fromJson(e))
          .toList(),
      macd: (json['macd'] as List)
          .map((e) => MACDDataPoint.fromJson(e))
          .toList(),
      bollinger: (json['bollinger'] as List)
          .map((e) => BollingerDataPoint.fromJson(e))
          .toList(),
      kd: (json['kd'] as List).map((e) => KDDataPoint.fromJson(e)).toList(),
    );
  }
}
