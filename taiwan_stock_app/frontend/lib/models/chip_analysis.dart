/// 籌碼分析數據模型
/// 專業級高風險交易分析平台

/// 每日法人買賣超
class DailyFlow {
  final String date;
  final int foreignNet;
  final int trustNet;
  final int dealerNet;
  final int totalNet;

  DailyFlow({
    required this.date,
    required this.foreignNet,
    required this.trustNet,
    required this.dealerNet,
    required this.totalNet,
  });

  factory DailyFlow.fromJson(Map<String, dynamic> json) {
    return DailyFlow(
      date: json['date'],
      foreignNet: json['foreign_net'],
      trustNet: json['trust_net'],
      dealerNet: json['dealer_net'],
      totalNet: json['total_net'],
    );
  }
}

/// 每日融資融券
class DailyMargin {
  final String date;
  final int marginBalance;
  final int marginChange;
  final int shortBalance;

  DailyMargin({
    required this.date,
    required this.marginBalance,
    required this.marginChange,
    required this.shortBalance,
  });

  factory DailyMargin.fromJson(Map<String, dynamic> json) {
    return DailyMargin(
      date: json['date'],
      marginBalance: json['margin_balance'],
      marginChange: json['margin_change'],
      shortBalance: json['short_balance'],
    );
  }
}

/// 法人統計摘要
class InstitutionalSummary {
  final int foreign5dNet;
  final int foreign10dNet;
  final int foreign20dNet;
  final int trust5dNet;
  final int trust10dNet;
  final int dealer5dNet;
  final int total5dNet;
  final int total10dNet;

  InstitutionalSummary({
    required this.foreign5dNet,
    required this.foreign10dNet,
    required this.foreign20dNet,
    required this.trust5dNet,
    required this.trust10dNet,
    required this.dealer5dNet,
    required this.total5dNet,
    required this.total10dNet,
  });

  factory InstitutionalSummary.fromJson(Map<String, dynamic> json) {
    return InstitutionalSummary(
      foreign5dNet: json['foreign_5d_net'],
      foreign10dNet: json['foreign_10d_net'],
      foreign20dNet: json['foreign_20d_net'],
      trust5dNet: json['trust_5d_net'],
      trust10dNet: json['trust_10d_net'],
      dealer5dNet: json['dealer_5d_net'],
      total5dNet: json['total_5d_net'],
      total10dNet: json['total_10d_net'],
    );
  }

  /// 外資是否買超
  bool get isForeignBuying => foreign5dNet > 0;

  /// 投信是否買超
  bool get isTrustBuying => trust5dNet > 0;

  /// 法人是否同步買超
  bool get isInstitutionalBuying => foreign5dNet > 0 && trust5dNet > 0;
}

/// 融資融券摘要
class MarginSummary {
  final int currentBalance;
  final double currentUtilization;
  final int shortBalance;
  final double shortRatio;
  final int margin5dChange;
  final String marginTrend;

  MarginSummary({
    required this.currentBalance,
    required this.currentUtilization,
    required this.shortBalance,
    required this.shortRatio,
    required this.margin5dChange,
    required this.marginTrend,
  });

  factory MarginSummary.fromJson(Map<String, dynamic> json) {
    return MarginSummary(
      currentBalance: json['current_balance'],
      currentUtilization: (json['current_utilization'] as num).toDouble(),
      shortBalance: json['short_balance'],
      shortRatio: (json['short_ratio'] as num).toDouble(),
      margin5dChange: json['margin_5d_change'],
      marginTrend: json['margin_trend'],
    );
  }

  /// 融資使用率是否偏高
  bool get isHighUtilization => currentUtilization > 60;

  /// 融資是否增加
  bool get isMarginIncreasing => margin5dChange > 0;
}

/// 籌碼動能
class ChipMomentum {
  final double momentumScore;
  final String momentumDirection;
  final double foreignMomentum;
  final double trustMomentum;
  final double marginMomentum;
  final List<String> signals;
  final String recommendation;

  ChipMomentum({
    required this.momentumScore,
    required this.momentumDirection,
    required this.foreignMomentum,
    required this.trustMomentum,
    required this.marginMomentum,
    required this.signals,
    required this.recommendation,
  });

  factory ChipMomentum.fromJson(Map<String, dynamic> json) {
    return ChipMomentum(
      momentumScore: (json['momentum_score'] as num).toDouble(),
      momentumDirection: json['momentum_direction'],
      foreignMomentum: (json['foreign_momentum'] as num).toDouble(),
      trustMomentum: (json['trust_momentum'] as num).toDouble(),
      marginMomentum: (json['margin_momentum'] as num).toDouble(),
      signals: List<String>.from(json['signals'] ?? []),
      recommendation: json['recommendation'],
    );
  }

  /// 是否看多
  bool get isBullish => momentumDirection == 'bullish';

  /// 是否看空
  bool get isBearish => momentumDirection == 'bearish';

  /// 動能強度等級
  String get strengthLevel {
    if (momentumScore >= 70) return '強';
    if (momentumScore >= 55) return '中';
    if (momentumScore >= 45) return '弱';
    if (momentumScore >= 30) return '中';
    return '強';
  }
}

/// 籌碼綜合評估
class ChipOverall {
  final double score;
  final String direction;
  final String directionCn;
  final String suggestion;
  final List<String> strengths;
  final List<String> weaknesses;
  final List<String> warnings;

  ChipOverall({
    required this.score,
    required this.direction,
    required this.directionCn,
    required this.suggestion,
    required this.strengths,
    required this.weaknesses,
    required this.warnings,
  });

  factory ChipOverall.fromJson(Map<String, dynamic> json) {
    return ChipOverall(
      score: (json['score'] as num).toDouble(),
      direction: json['direction'],
      directionCn: json['direction_cn'],
      suggestion: json['suggestion'],
      strengths: List<String>.from(json['strengths'] ?? []),
      weaknesses: List<String>.from(json['weaknesses'] ?? []),
      warnings: List<String>.from(json['warnings'] ?? []),
    );
  }
}

/// 完整籌碼分析
class ChipAnalysis {
  final String stockId;
  final String name;
  final double currentPrice;
  final int analysisDays;
  final InstitutionalSummary? institutional;
  final MarginSummary? margin;
  final ChipMomentum momentum;
  final ChipOverall overall;
  final List<DailyFlow> dailyFlows;
  final List<DailyMargin> dailyMargin;

  ChipAnalysis({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.analysisDays,
    this.institutional,
    this.margin,
    required this.momentum,
    required this.overall,
    required this.dailyFlows,
    required this.dailyMargin,
  });

  factory ChipAnalysis.fromJson(Map<String, dynamic> json) {
    return ChipAnalysis(
      stockId: json['stock_id'],
      name: json['name'],
      currentPrice: (json['current_price'] as num).toDouble(),
      analysisDays: json['analysis_days'],
      institutional: json['institutional'] != null
          ? InstitutionalSummary.fromJson(json['institutional'])
          : null,
      margin: json['margin'] != null
          ? MarginSummary.fromJson(json['margin'])
          : null,
      momentum: ChipMomentum.fromJson(json['momentum']),
      overall: ChipOverall.fromJson(json['overall']),
      dailyFlows: (json['daily_flows'] as List)
          .map((e) => DailyFlow.fromJson(e))
          .toList(),
      dailyMargin: (json['daily_margin'] as List)
          .map((e) => DailyMargin.fromJson(e))
          .toList(),
    );
  }
}
