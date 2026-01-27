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

class AISuggestion {
  final String stockId;
  final String name;
  final String suggestion; // 'BUY', 'SELL', 'HOLD'
  final double confidence;
  final double? bullishProbability; // 看漲機率 (更直覺的指標)
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

  AISuggestion({
    required this.stockId,
    required this.name,
    required this.suggestion,
    required this.confidence,
    this.bullishProbability,
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
