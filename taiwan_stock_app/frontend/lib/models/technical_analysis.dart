/// 技術分析數據模型
/// 專業級高風險交易分析平台

class TechnicalAnalysis {
  final String stockId;
  final String name;
  final double currentPrice;
  final DateTime timestamp;
  final BasicIndicators indicators;
  final SupportResistance supportResistance;
  final TrendStrength trendStrength;
  final IchimokuSignal ichimokuSignal;
  final Divergence divergence;
  final EntryExit entryExit;
  final double overallScore;
  final String scoreDescription;
  final String? signalSummary;

  TechnicalAnalysis({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.timestamp,
    required this.indicators,
    required this.supportResistance,
    required this.trendStrength,
    required this.ichimokuSignal,
    required this.divergence,
    required this.entryExit,
    required this.overallScore,
    required this.scoreDescription,
    this.signalSummary,
  });

  factory TechnicalAnalysis.fromJson(Map<String, dynamic> json) {
    return TechnicalAnalysis(
      stockId: json['stock_id'],
      name: json['name'],
      currentPrice: (json['current_price'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp']),
      indicators: BasicIndicators.fromJson(json['indicators']),
      supportResistance: SupportResistance.fromJson(json['support_resistance']),
      trendStrength: TrendStrength.fromJson(json['trend_strength']),
      ichimokuSignal: IchimokuSignal.fromJson(json['ichimoku_signal']),
      divergence: Divergence.fromJson(json['divergence']),
      entryExit: EntryExit.fromJson(json['entry_exit']),
      overallScore: (json['overall_score'] as num).toDouble(),
      scoreDescription: json['score_description'],
      signalSummary: json['signal_summary'],
    );
  }
}

class BasicIndicators {
  final double? ma5;
  final double? ma10;
  final double? ma20;
  final double? ma60;
  final double? rsi;
  final double? macd;
  final double? macdSignal;
  final double? macdHistogram;
  final double? bbUpper;
  final double? bbMiddle;
  final double? bbLower;
  final double? k;
  final double? d;
  final double? williamsR;
  final double? obv;
  final double? atr;
  final double? adx;
  final double? diPlus;
  final double? diMinus;
  final double? cci;

  BasicIndicators({
    this.ma5,
    this.ma10,
    this.ma20,
    this.ma60,
    this.rsi,
    this.macd,
    this.macdSignal,
    this.macdHistogram,
    this.bbUpper,
    this.bbMiddle,
    this.bbLower,
    this.k,
    this.d,
    this.williamsR,
    this.obv,
    this.atr,
    this.adx,
    this.diPlus,
    this.diMinus,
    this.cci,
  });

  factory BasicIndicators.fromJson(Map<String, dynamic> json) {
    return BasicIndicators(
      ma5: (json['ma5'] as num?)?.toDouble(),
      ma10: (json['ma10'] as num?)?.toDouble(),
      ma20: (json['ma20'] as num?)?.toDouble(),
      ma60: (json['ma60'] as num?)?.toDouble(),
      rsi: (json['rsi'] as num?)?.toDouble(),
      macd: (json['macd'] as num?)?.toDouble(),
      macdSignal: (json['macd_signal'] as num?)?.toDouble(),
      macdHistogram: (json['macd_histogram'] as num?)?.toDouble(),
      bbUpper: (json['bb_upper'] as num?)?.toDouble(),
      bbMiddle: (json['bb_middle'] as num?)?.toDouble(),
      bbLower: (json['bb_lower'] as num?)?.toDouble(),
      k: (json['k'] as num?)?.toDouble(),
      d: (json['d'] as num?)?.toDouble(),
      williamsR: (json['williams_r'] as num?)?.toDouble(),
      obv: (json['obv'] as num?)?.toDouble(),
      atr: (json['atr'] as num?)?.toDouble(),
      adx: (json['adx'] as num?)?.toDouble(),
      diPlus: (json['di_plus'] as num?)?.toDouble(),
      diMinus: (json['di_minus'] as num?)?.toDouble(),
      cci: (json['cci'] as num?)?.toDouble(),
    );
  }
}

class SupportResistance {
  final double pivot;
  final double r1;
  final double r2;
  final double r3;
  final double s1;
  final double s2;
  final double s3;
  final List<double> recentHighs;
  final List<double> recentLows;
  final String currentPosition;
  final double currentPrice;

  SupportResistance({
    required this.pivot,
    required this.r1,
    required this.r2,
    required this.r3,
    required this.s1,
    required this.s2,
    required this.s3,
    required this.recentHighs,
    required this.recentLows,
    required this.currentPosition,
    required this.currentPrice,
  });

  factory SupportResistance.fromJson(Map<String, dynamic> json) {
    return SupportResistance(
      pivot: (json['pivot'] as num).toDouble(),
      r1: (json['r1'] as num).toDouble(),
      r2: (json['r2'] as num).toDouble(),
      r3: (json['r3'] as num).toDouble(),
      s1: (json['s1'] as num).toDouble(),
      s2: (json['s2'] as num).toDouble(),
      s3: (json['s3'] as num).toDouble(),
      recentHighs: (json['recent_highs'] as List)
          .map((e) => (e as num).toDouble())
          .toList(),
      recentLows: (json['recent_lows'] as List)
          .map((e) => (e as num).toDouble())
          .toList(),
      currentPosition: json['current_position'],
      currentPrice: (json['current_price'] as num).toDouble(),
    );
  }
}

class TrendStrength {
  final double strength;
  final String direction;
  final String maAlignment;
  final double adx;
  final double diPlus;
  final double diMinus;
  final String recommendation;

  TrendStrength({
    required this.strength,
    required this.direction,
    required this.maAlignment,
    required this.adx,
    required this.diPlus,
    required this.diMinus,
    required this.recommendation,
  });

  factory TrendStrength.fromJson(Map<String, dynamic> json) {
    return TrendStrength(
      strength: (json['strength'] as num).toDouble(),
      direction: json['direction'],
      maAlignment: json['ma_alignment'],
      adx: (json['adx'] as num).toDouble(),
      diPlus: (json['di_plus'] as num).toDouble(),
      diMinus: (json['di_minus'] as num).toDouble(),
      recommendation: json['recommendation'],
    );
  }

  bool get isBullish => direction == 'bullish';
  bool get isBearish => direction == 'bearish';
  bool get isStrong => strength > 60;
}

class IchimokuSignal {
  final String trend;
  final String signal;
  final String cloudStatus;
  final int strength;
  final double tenkan;
  final double kijun;
  final double cloudTop;
  final double cloudBottom;

  IchimokuSignal({
    required this.trend,
    required this.signal,
    required this.cloudStatus,
    required this.strength,
    required this.tenkan,
    required this.kijun,
    required this.cloudTop,
    required this.cloudBottom,
  });

  factory IchimokuSignal.fromJson(Map<String, dynamic> json) {
    return IchimokuSignal(
      trend: json['trend'],
      signal: json['signal'],
      cloudStatus: json['cloud_status'],
      strength: json['strength'],
      tenkan: (json['tenkan'] as num).toDouble(),
      kijun: (json['kijun'] as num).toDouble(),
      cloudTop: (json['cloud_top'] as num).toDouble(),
      cloudBottom: (json['cloud_bottom'] as num).toDouble(),
    );
  }

  bool get isBuySignal => signal.contains('buy');
  bool get isSellSignal => signal.contains('sell');
}

class Divergence {
  final String type;
  final double strength;
  final String description;

  Divergence({
    required this.type,
    required this.strength,
    required this.description,
  });

  factory Divergence.fromJson(Map<String, dynamic> json) {
    return Divergence(
      type: json['type'],
      strength: (json['strength'] as num).toDouble(),
      description: json['description'],
    );
  }

  bool get hasDivergence => type != 'none';
  bool get isBullish => type.contains('bullish');
  bool get isBearish => type.contains('bearish');
}

class EntryExit {
  final double entryPriceMin;
  final double entryPriceMax;
  final double stopLoss;
  final double takeProfit1;
  final double takeProfit2;
  final double takeProfit3;
  final double riskRewardRatio;
  final double atr;

  EntryExit({
    required this.entryPriceMin,
    required this.entryPriceMax,
    required this.stopLoss,
    required this.takeProfit1,
    required this.takeProfit2,
    required this.takeProfit3,
    required this.riskRewardRatio,
    required this.atr,
  });

  factory EntryExit.fromJson(Map<String, dynamic> json) {
    return EntryExit(
      entryPriceMin: (json['entry_price_min'] as num).toDouble(),
      entryPriceMax: (json['entry_price_max'] as num).toDouble(),
      stopLoss: (json['stop_loss'] as num).toDouble(),
      takeProfit1: (json['take_profit_1'] as num).toDouble(),
      takeProfit2: (json['take_profit_2'] as num).toDouble(),
      takeProfit3: (json['take_profit_3'] as num).toDouble(),
      riskRewardRatio: (json['risk_reward_ratio'] as num).toDouble(),
      atr: (json['atr'] as num).toDouble(),
    );
  }
}

/// 快速信號（列表顯示用）
class QuickSignal {
  final String stockId;
  final String name;
  final double currentPrice;
  final double changePercent;
  final String signal;
  final double confidence;
  final String trendDirection;
  final double trendStrength;
  final bool hasDivergence;
  final String? divergenceType;

  QuickSignal({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.changePercent,
    required this.signal,
    required this.confidence,
    required this.trendDirection,
    required this.trendStrength,
    required this.hasDivergence,
    this.divergenceType,
  });

  factory QuickSignal.fromJson(Map<String, dynamic> json) {
    return QuickSignal(
      stockId: json['stock_id'],
      name: json['name'],
      currentPrice: (json['current_price'] as num).toDouble(),
      changePercent: (json['change_percent'] as num).toDouble(),
      signal: json['signal'],
      confidence: (json['confidence'] as num).toDouble(),
      trendDirection: json['trend_direction'],
      trendStrength: (json['trend_strength'] as num).toDouble(),
      hasDivergence: json['has_divergence'],
      divergenceType: json['divergence_type'],
    );
  }

  bool get isBuySignal => signal == 'BUY';
  bool get isSellSignal => signal == 'SELL';
  bool get isUp => changePercent > 0;
}
