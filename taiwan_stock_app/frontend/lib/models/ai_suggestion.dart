import 'package:flutter/material.dart';

class TakeProfitTarget {
  final double price;
  final double probability;
  final String description;

  TakeProfitTarget({
    required this.price,
    required this.probability,
    required this.description,
  });

  factory TakeProfitTarget.fromJson(Map<String, dynamic> json) {
    return TakeProfitTarget(
      price: (json['price'] as num).toDouble(),
      probability: (json['probability'] as num).toDouble(),
      description: json['description'],
    );
  }
}

/// 個股歷史預測準確率（用於信任徽章）
class HistoricalAccuracy {
  final double directionAccuracyPercent; // 方向正確率 0~100
  final double avgErrorPercent; // 平均預測誤差 %
  final double amplitudeRatio; // 預測幅度 / 實際幅度
  final int nRecords; // 樣本數

  HistoricalAccuracy({
    required this.directionAccuracyPercent,
    required this.avgErrorPercent,
    required this.amplitudeRatio,
    required this.nRecords,
  });

  factory HistoricalAccuracy.fromJson(Map<String, dynamic> json) {
    return HistoricalAccuracy(
      directionAccuracyPercent:
          (json['direction_accuracy_percent'] as num?)?.toDouble() ?? 0,
      avgErrorPercent: (json['avg_error_percent'] as num?)?.toDouble() ?? 0,
      amplitudeRatio: (json['amplitude_ratio'] as num?)?.toDouble() ?? 1.0,
      nRecords: (json['n_records'] as num?)?.toInt() ?? 0,
    );
  }
}

/// 隔天漲跌預測
class NextDayPrediction {
  final String direction; // 'UP' or 'DOWN'
  final double probability; // 預測準確度 0.55-0.95
  final double predictedChangePercent; // 預測漲跌幅 %
  final double? priceRangeLow; // 預測最低價
  final double? priceRangeHigh; // 預測最高價
  final String reasoning; // 預測依據
  final String? targetDate; // 預測目標日期 (YYYY-MM-DD)

  NextDayPrediction({
    required this.direction,
    required this.probability,
    required this.predictedChangePercent,
    this.priceRangeLow,
    this.priceRangeHigh,
    required this.reasoning,
    this.targetDate,
  });

  factory NextDayPrediction.fromJson(Map<String, dynamic> json) {
    return NextDayPrediction(
      direction: json['direction'] ?? 'UP',
      probability: (json['probability'] as num?)?.toDouble() ?? 0.5,
      predictedChangePercent: (json['predicted_change_percent'] as num?)?.toDouble() ?? 0.0,
      priceRangeLow: json['price_range_low'] != null
          ? (json['price_range_low'] as num).toDouble()
          : null,
      priceRangeHigh: json['price_range_high'] != null
          ? (json['price_range_high'] as num).toDouble()
          : null,
      reasoning: json['reasoning'] ?? '',
      targetDate: json['target_date'],
    );
  }

  bool get isUp => direction == 'UP';

  Color get directionColor => isUp ? Colors.red : Colors.green;

  String get directionText => isUp ? '預測上漲' : '預測下跌';

  String get probabilityText => '${(probability * 100).toStringAsFixed(0)}%';

  String get changeText {
    final sign = predictedChangePercent >= 0 ? '+' : '';
    return '$sign${predictedChangePercent.toStringAsFixed(2)}%';
  }
}

class AISuggestion {
  final String stockId;
  final String name;
  final String suggestion; // 'BUY', 'SELL', 'HOLD'
  final double confidence;
  final double? bullishProbability; // 看漲機率 (更直覺的指標)
  final double? currentPrice; // 最新收盤價
  final double? targetPrice;
  final double? stopLossPrice;
  final String reasoning;
  final List<KeyFactor> keyFactors;
  final DateTime reportDate;

  // 高風險型經紀人新增欄位
  final double? entryPriceMin;
  final double? entryPriceMax;
  final List<TakeProfitTarget>? takeProfitTargets;
  final String? riskLevel;
  final String? timeHorizon;
  final double? predictedChangePercent;

  // 隔天漲跌預測
  final NextDayPrediction? nextDayPrediction;

  // 個股歷史準確率（信任徽章用，無樣本時為 null）
  final HistoricalAccuracy? historicalAccuracy;

  AISuggestion({
    required this.stockId,
    required this.name,
    required this.suggestion,
    required this.confidence,
    this.bullishProbability,
    this.currentPrice,
    this.targetPrice,
    this.stopLossPrice,
    required this.reasoning,
    required this.keyFactors,
    required this.reportDate,
    this.entryPriceMin,
    this.entryPriceMax,
    this.takeProfitTargets,
    this.riskLevel,
    this.timeHorizon,
    this.predictedChangePercent,
    this.nextDayPrediction,
    this.historicalAccuracy,
  });

  factory AISuggestion.fromJson(Map<String, dynamic> json) {
    return AISuggestion(
      stockId: json['stock_id'],
      name: json['name'],
      suggestion: json['suggestion'],
      confidence: (json['confidence'] as num).toDouble(),
      bullishProbability: json['bullish_probability'] != null
          ? (json['bullish_probability'] as num).toDouble()
          : null,
      currentPrice: json['current_price'] != null
          ? (json['current_price'] as num).toDouble()
          : null,
      targetPrice: json['target_price'] != null
          ? (json['target_price'] as num).toDouble()
          : null,
      stopLossPrice: json['stop_loss_price'] != null
          ? (json['stop_loss_price'] as num).toDouble()
          : null,
      reasoning: json['reasoning'],
      keyFactors: (json['key_factors'] as List)
          .map((e) => KeyFactor.fromJson(e))
          .toList(),
      reportDate: DateTime.parse(json['report_date']),
      entryPriceMin: json['entry_price_min'] != null
          ? (json['entry_price_min'] as num).toDouble()
          : null,
      entryPriceMax: json['entry_price_max'] != null
          ? (json['entry_price_max'] as num).toDouble()
          : null,
      takeProfitTargets: json['take_profit_targets'] != null
          ? (json['take_profit_targets'] as List)
              .map((e) => TakeProfitTarget.fromJson(e))
              .toList()
          : null,
      riskLevel: json['risk_level'],
      timeHorizon: json['time_horizon'],
      predictedChangePercent: json['predicted_change_percent'] != null
          ? (json['predicted_change_percent'] as num).toDouble()
          : null,
      nextDayPrediction: json['next_day_prediction'] != null
          ? NextDayPrediction.fromJson(json['next_day_prediction'])
          : null,
      historicalAccuracy: json['historical_accuracy'] != null
          ? HistoricalAccuracy.fromJson(json['historical_accuracy'])
          : null,
    );
  }

  Color get suggestionColor {
    switch (suggestion) {
      case 'BUY':
        return Colors.red;
      case 'SELL':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  String get suggestionText {
    switch (suggestion) {
      case 'BUY':
        return '建議買進';
      case 'SELL':
        return '建議賣出';
      default:
        return '建議持有';
    }
  }
}

class KeyFactor {
  final String category;
  final String factor;
  final String impact; // 'positive', 'negative', 'neutral'

  KeyFactor({
    required this.category,
    required this.factor,
    required this.impact,
  });

  factory KeyFactor.fromJson(Map<String, dynamic> json) {
    return KeyFactor(
      category: json['category'],
      factor: json['factor'],
      impact: json['impact'],
    );
  }

  Color get impactColor {
    switch (impact) {
      case 'positive':
        return Colors.red;
      case 'negative':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  IconData get impactIcon {
    switch (impact) {
      case 'positive':
        return Icons.arrow_upward;
      case 'negative':
        return Icons.arrow_downward;
      default:
        return Icons.remove;
    }
  }
}
