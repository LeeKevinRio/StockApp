import 'package:flutter/material.dart';

class AISuggestion {
  final String stockId;
  final String name;
  final String suggestion; // 'BUY', 'SELL', 'HOLD'
  final double confidence;
  final double? targetPrice;
  final double? stopLossPrice;
  final String reasoning;
  final List<KeyFactor> keyFactors;
  final DateTime reportDate;

  AISuggestion({
    required this.stockId,
    required this.name,
    required this.suggestion,
    required this.confidence,
    this.targetPrice,
    this.stopLossPrice,
    required this.reasoning,
    required this.keyFactors,
    required this.reportDate,
  });

  factory AISuggestion.fromJson(Map<String, dynamic> json) {
    return AISuggestion(
      stockId: json['stock_id'],
      name: json['name'],
      suggestion: json['suggestion'],
      confidence: (json['confidence'] as num).toDouble(),
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
