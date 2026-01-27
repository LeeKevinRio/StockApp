/// 價格警示模型

class PriceAlert {
  final int id;
  final String stockId;
  final String? stockName;
  final String alertType; // 'ABOVE', 'BELOW', 'PERCENT_UP', 'PERCENT_DOWN'
  final double? targetPrice;
  final double? percentThreshold;
  final bool isActive;
  final bool isTriggered;
  final DateTime? triggeredAt;
  final double? triggeredPrice;
  final bool notifyPush;
  final bool notifyEmail;
  final String? notes;
  final DateTime createdAt;

  PriceAlert({
    required this.id,
    required this.stockId,
    this.stockName,
    required this.alertType,
    this.targetPrice,
    this.percentThreshold,
    required this.isActive,
    required this.isTriggered,
    this.triggeredAt,
    this.triggeredPrice,
    required this.notifyPush,
    required this.notifyEmail,
    this.notes,
    required this.createdAt,
  });

  factory PriceAlert.fromJson(Map<String, dynamic> json) {
    return PriceAlert(
      id: json['id'],
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      alertType: json['alert_type'],
      targetPrice: json['target_price'] != null
          ? double.parse(json['target_price'].toString())
          : null,
      percentThreshold: json['percent_threshold'] != null
          ? double.parse(json['percent_threshold'].toString())
          : null,
      isActive: json['is_active'] ?? false,
      isTriggered: json['is_triggered'] ?? false,
      triggeredAt: json['triggered_at'] != null
          ? DateTime.parse(json['triggered_at'])
          : null,
      triggeredPrice: json['triggered_price'] != null
          ? double.parse(json['triggered_price'].toString())
          : null,
      notifyPush: json['notify_push'] ?? true,
      notifyEmail: json['notify_email'] ?? false,
      notes: json['notes'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'stock_id': stockId,
      'stock_name': stockName,
      'alert_type': alertType,
      'target_price': targetPrice,
      'percent_threshold': percentThreshold,
      'is_active': isActive,
      'is_triggered': isTriggered,
      'triggered_at': triggeredAt?.toIso8601String(),
      'triggered_price': triggeredPrice,
      'notify_push': notifyPush,
      'notify_email': notifyEmail,
      'notes': notes,
      'created_at': createdAt.toIso8601String(),
    };
  }

  String get alertTypeText {
    switch (alertType) {
      case 'ABOVE':
        return '高於';
      case 'BELOW':
        return '低於';
      case 'PERCENT_UP':
        return '漲幅達';
      case 'PERCENT_DOWN':
        return '跌幅達';
      default:
        return alertType;
    }
  }

  String get displayText {
    if (alertType == 'ABOVE' || alertType == 'BELOW') {
      return '$alertTypeText \$${targetPrice?.toStringAsFixed(2) ?? '0'}';
    } else {
      return '$alertTypeText ${percentThreshold?.toStringAsFixed(2) ?? '0'}%';
    }
  }
}

class PriceAlertCreate {
  final String stockId;
  final String alertType;
  final double? targetPrice;
  final double? percentThreshold;
  final bool notifyPush;
  final bool notifyEmail;
  final String? notes;

  PriceAlertCreate({
    required this.stockId,
    required this.alertType,
    this.targetPrice,
    this.percentThreshold,
    this.notifyPush = true,
    this.notifyEmail = false,
    this.notes,
  });

  Map<String, dynamic> toJson() {
    return {
      'stock_id': stockId,
      'alert_type': alertType,
      if (targetPrice != null) 'target_price': targetPrice,
      if (percentThreshold != null) 'percent_threshold': percentThreshold,
      'notify_push': notifyPush,
      'notify_email': notifyEmail,
      if (notes != null) 'notes': notes,
    };
  }
}
