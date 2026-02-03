/// 形態識別數據模型
/// 專業級高風險交易分析平台

/// 單一形態詳情
class PatternDetail {
  final String type;
  final String signal;
  final double confidence;
  final String description;
  final double? targetPrice;
  final double? stopLoss;
  final bool isConfirmed;
  final Map<String, dynamic> keyPrices;

  PatternDetail({
    required this.type,
    required this.signal,
    required this.confidence,
    required this.description,
    this.targetPrice,
    this.stopLoss,
    required this.isConfirmed,
    required this.keyPrices,
  });

  factory PatternDetail.fromJson(Map<String, dynamic> json) {
    return PatternDetail(
      type: json['type'],
      signal: json['signal'],
      confidence: (json['confidence'] as num).toDouble(),
      description: json['description'],
      targetPrice: (json['target_price'] as num?)?.toDouble(),
      stopLoss: (json['stop_loss'] as num?)?.toDouble(),
      isConfirmed: json['is_confirmed'] ?? false,
      keyPrices: json['key_prices'] ?? {},
    );
  }

  /// 是否看多
  bool get isBullish => signal == 'bullish';

  /// 是否看空
  bool get isBearish => signal == 'bearish';

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
    return typeNames[type] ?? type;
  }

  /// 信號顏色
  String get signalColor {
    if (isBullish) return 'green';
    if (isBearish) return 'red';
    return 'grey';
  }
}

/// 形態分析結果
class PatternAnalysis {
  final String stockId;
  final String name;
  final double currentPrice;
  final bool hasPatterns;
  final String dominantSignal;
  final int patternsCount;
  final int bullishCount;
  final int bearishCount;
  final double bullishScore;
  final double bearishScore;
  final String summary;
  final List<PatternDetail> topPatterns;

  PatternAnalysis({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.hasPatterns,
    required this.dominantSignal,
    required this.patternsCount,
    required this.bullishCount,
    required this.bearishCount,
    required this.bullishScore,
    required this.bearishScore,
    required this.summary,
    required this.topPatterns,
  });

  factory PatternAnalysis.fromJson(Map<String, dynamic> json) {
    return PatternAnalysis(
      stockId: json['stock_id'],
      name: json['name'],
      currentPrice: (json['current_price'] as num).toDouble(),
      hasPatterns: json['has_patterns'],
      dominantSignal: json['dominant_signal'],
      patternsCount: json['patterns_count'],
      bullishCount: json['bullish_count'] ?? 0,
      bearishCount: json['bearish_count'] ?? 0,
      bullishScore: (json['bullish_score'] as num?)?.toDouble() ?? 0,
      bearishScore: (json['bearish_score'] as num?)?.toDouble() ?? 0,
      summary: json['summary'],
      topPatterns: (json['top_patterns'] as List)
          .map((e) => PatternDetail.fromJson(e))
          .toList(),
    );
  }

  /// 是否看多為主導
  bool get isBullishDominant => dominantSignal == 'bullish';

  /// 是否看空為主導
  bool get isBearishDominant => dominantSignal == 'bearish';

  /// 主導信號名稱（中文）
  String get signalName {
    if (isBullishDominant) return '看多';
    if (isBearishDominant) return '看空';
    return '觀望';
  }

  /// 第一個形態（最重要的）
  PatternDetail? get primaryPattern {
    return topPatterns.isNotEmpty ? topPatterns.first : null;
  }
}
