// 圖表設置數據模型
// K線圖表顯示偏好和指標設置

import 'package:flutter/material.dart';

/// 可用的技術指標類型
enum ChartIndicatorType {
  ma5,
  ma10,
  ma20,
  ma60,
  bollinger,
  volume,
  rsi,
  macd,
  kd,
}

/// 圖表時間週期
enum ChartPeriod {
  day('日K', 'day', 60),
  week('週K', 'week', 52),
  month('月K', 'month', 24);

  final String label;
  final String value;
  final int defaultDays;

  const ChartPeriod(this.label, this.value, this.defaultDays);
}

/// 繪圖工具類型
enum DrawingToolType {
  trendLine,
  horizontalLine,
  verticalLine,
  rectangle,
  fibonacci,
  text,
}

/// 單一指標設置
class IndicatorSetting {
  final ChartIndicatorType type;
  final bool isEnabled;
  final Color color;
  final Map<String, dynamic> params;

  const IndicatorSetting({
    required this.type,
    this.isEnabled = true,
    required this.color,
    this.params = const {},
  });

  IndicatorSetting copyWith({
    bool? isEnabled,
    Color? color,
    Map<String, dynamic>? params,
  }) {
    return IndicatorSetting(
      type: type,
      isEnabled: isEnabled ?? this.isEnabled,
      color: color ?? this.color,
      params: params ?? this.params,
    );
  }

  /// 指標名稱
  String get name {
    switch (type) {
      case ChartIndicatorType.ma5:
        return 'MA5';
      case ChartIndicatorType.ma10:
        return 'MA10';
      case ChartIndicatorType.ma20:
        return 'MA20';
      case ChartIndicatorType.ma60:
        return 'MA60';
      case ChartIndicatorType.bollinger:
        return '布林通道';
      case ChartIndicatorType.volume:
        return '成交量';
      case ChartIndicatorType.rsi:
        return 'RSI';
      case ChartIndicatorType.macd:
        return 'MACD';
      case ChartIndicatorType.kd:
        return 'KD';
    }
  }
}

/// 繪圖對象
class DrawingObject {
  final String id;
  final DrawingToolType type;
  final List<Offset> points;
  final Color color;
  final double strokeWidth;
  final String? text;
  final DateTime createdAt;

  DrawingObject({
    required this.id,
    required this.type,
    required this.points,
    this.color = Colors.blue,
    this.strokeWidth = 1.5,
    this.text,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  DrawingObject copyWith({
    List<Offset>? points,
    Color? color,
    double? strokeWidth,
    String? text,
  }) {
    return DrawingObject(
      id: id,
      type: type,
      points: points ?? this.points,
      color: color ?? this.color,
      strokeWidth: strokeWidth ?? this.strokeWidth,
      text: text ?? this.text,
      createdAt: createdAt,
    );
  }

  /// 工具名稱
  String get toolName {
    switch (type) {
      case DrawingToolType.trendLine:
        return '趨勢線';
      case DrawingToolType.horizontalLine:
        return '水平線';
      case DrawingToolType.verticalLine:
        return '垂直線';
      case DrawingToolType.rectangle:
        return '矩形';
      case DrawingToolType.fibonacci:
        return '斐波那契';
      case DrawingToolType.text:
        return '文字';
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type.name,
      'points': points.map((p) => {'x': p.dx, 'y': p.dy}).toList(),
      'color': color.toARGB32(),
      'strokeWidth': strokeWidth,
      'text': text,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  factory DrawingObject.fromJson(Map<String, dynamic> json) {
    return DrawingObject(
      id: json['id'],
      type: DrawingToolType.values.firstWhere(
        (e) => e.name == json['type'],
        orElse: () => DrawingToolType.trendLine,
      ),
      points: (json['points'] as List)
          .map((p) => Offset(p['x'].toDouble(), p['y'].toDouble()))
          .toList(),
      color: Color(json['color']),
      strokeWidth: json['strokeWidth'].toDouble(),
      text: json['text'],
      createdAt: DateTime.parse(json['createdAt']),
    );
  }
}

/// 形態標記
class PatternMarker {
  final String patternType;
  final String signal;
  final double confidence;
  final int startIndex;
  final int endIndex;
  final Map<String, double> keyPrices;
  final double? targetPrice;
  final double? stopLoss;
  final String description;
  final bool isConfirmed;

  const PatternMarker({
    required this.patternType,
    required this.signal,
    required this.confidence,
    required this.startIndex,
    required this.endIndex,
    required this.keyPrices,
    this.targetPrice,
    this.stopLoss,
    required this.description,
    required this.isConfirmed,
  });

  factory PatternMarker.fromJson(Map<String, dynamic> json) {
    return PatternMarker(
      patternType: json['pattern_type'],
      signal: json['signal'],
      confidence: (json['confidence'] as num).toDouble(),
      startIndex: json['start_index'],
      endIndex: json['end_index'],
      keyPrices: Map<String, double>.from(
        (json['key_prices'] as Map).map(
          (k, v) => MapEntry(k, (v as num).toDouble()),
        ),
      ),
      targetPrice: (json['target_price'] as num?)?.toDouble(),
      stopLoss: (json['stop_loss'] as num?)?.toDouble(),
      description: json['description'],
      isConfirmed: json['is_confirmed'] ?? false,
    );
  }

  /// 是否看多
  bool get isBullish => signal == 'bullish';

  /// 是否看空
  bool get isBearish => signal == 'bearish';

  /// 標記顏色
  Color get markerColor {
    if (isBullish) return Colors.green;
    if (isBearish) return Colors.red;
    return Colors.grey;
  }

  /// 形態類型名稱（中文）
  String get typeName {
    const typeNames = {
      'head_shoulders_top': '頭肩頂',
      'head_shoulders_bottom': '頭肩底',
      'double_top': '雙頂',
      'double_bottom': '雙底',
      'triple_top': '三重頂',
      'triple_bottom': '三重底',
      'ascending_triangle': '上升三角形',
      'descending_triangle': '下降三角形',
      'symmetric_triangle': '對稱三角形',
      'rising_wedge': '上升楔形',
      'falling_wedge': '下降楔形',
      'bull_flag': '多頭旗形',
      'bear_flag': '空頭旗形',
      'rectangle': '矩形整理',
      'breakout_up': '向上突破',
      'breakout_down': '向下突破',
    };
    return typeNames[patternType] ?? patternType;
  }
}

/// 圖表設置
class ChartSettings {
  final ChartPeriod period;
  final Map<ChartIndicatorType, IndicatorSetting> indicators;
  final bool showPatterns;
  final bool showVolume;
  final bool enableCrosshair;
  final bool enableZoom;
  final List<DrawingObject> drawings;
  final List<PatternMarker> patterns;

  ChartSettings({
    this.period = ChartPeriod.day,
    Map<ChartIndicatorType, IndicatorSetting>? indicators,
    this.showPatterns = true,
    this.showVolume = true,
    this.enableCrosshair = true,
    this.enableZoom = true,
    this.drawings = const [],
    this.patterns = const [],
  }) : indicators = indicators ?? _defaultIndicators;

  static final Map<ChartIndicatorType, IndicatorSetting> _defaultIndicators = {
    ChartIndicatorType.ma5: const IndicatorSetting(
      type: ChartIndicatorType.ma5,
      isEnabled: true,
      color: Colors.blue,
      params: {'period': 5},
    ),
    ChartIndicatorType.ma10: const IndicatorSetting(
      type: ChartIndicatorType.ma10,
      isEnabled: true,
      color: Colors.orange,
      params: {'period': 10},
    ),
    ChartIndicatorType.ma20: const IndicatorSetting(
      type: ChartIndicatorType.ma20,
      isEnabled: true,
      color: Colors.purple,
      params: {'period': 20},
    ),
    ChartIndicatorType.ma60: const IndicatorSetting(
      type: ChartIndicatorType.ma60,
      isEnabled: false,
      color: Colors.teal,
      params: {'period': 60},
    ),
    ChartIndicatorType.bollinger: const IndicatorSetting(
      type: ChartIndicatorType.bollinger,
      isEnabled: false,
      color: Colors.cyan,
      params: {'period': 20, 'stdDev': 2.0},
    ),
    ChartIndicatorType.volume: const IndicatorSetting(
      type: ChartIndicatorType.volume,
      isEnabled: true,
      color: Colors.grey,
    ),
  };

  ChartSettings copyWith({
    ChartPeriod? period,
    Map<ChartIndicatorType, IndicatorSetting>? indicators,
    bool? showPatterns,
    bool? showVolume,
    bool? enableCrosshair,
    bool? enableZoom,
    List<DrawingObject>? drawings,
    List<PatternMarker>? patterns,
  }) {
    return ChartSettings(
      period: period ?? this.period,
      indicators: indicators ?? this.indicators,
      showPatterns: showPatterns ?? this.showPatterns,
      showVolume: showVolume ?? this.showVolume,
      enableCrosshair: enableCrosshair ?? this.enableCrosshair,
      enableZoom: enableZoom ?? this.enableZoom,
      drawings: drawings ?? this.drawings,
      patterns: patterns ?? this.patterns,
    );
  }

  /// 切換指標顯示
  ChartSettings toggleIndicator(ChartIndicatorType type) {
    final newIndicators = Map<ChartIndicatorType, IndicatorSetting>.from(indicators);
    if (newIndicators.containsKey(type)) {
      newIndicators[type] = newIndicators[type]!.copyWith(
        isEnabled: !newIndicators[type]!.isEnabled,
      );
    }
    return copyWith(indicators: newIndicators);
  }

  /// 獲取啟用的指標
  List<IndicatorSetting> get enabledIndicators {
    return indicators.values.where((i) => i.isEnabled).toList();
  }

  /// 檢查指標是否啟用
  bool isIndicatorEnabled(ChartIndicatorType type) {
    return indicators[type]?.isEnabled ?? false;
  }
}
