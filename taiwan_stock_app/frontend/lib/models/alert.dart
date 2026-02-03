/// 告警數據模型
/// 專業級高風險交易分析平台

/// 價格告警
class PriceAlert {
  final int id;
  final int userId;
  final String stockId;
  final String stockName;
  final String alertType;
  final double targetPrice;
  final double? percentChange;
  final bool isActive;
  final bool isTriggered;
  final DateTime? triggeredAt;
  final String? notes;
  final DateTime createdAt;

  PriceAlert({
    required this.id,
    required this.userId,
    required this.stockId,
    required this.stockName,
    required this.alertType,
    required this.targetPrice,
    this.percentChange,
    required this.isActive,
    required this.isTriggered,
    this.triggeredAt,
    this.notes,
    required this.createdAt,
  });

  factory PriceAlert.fromJson(Map<String, dynamic> json) {
    return PriceAlert(
      id: json['id'],
      userId: json['user_id'],
      stockId: json['stock_id'],
      stockName: json['stock_name'],
      alertType: json['alert_type'],
      targetPrice: (json['target_price'] as num).toDouble(),
      percentChange: (json['percent_change'] as num?)?.toDouble(),
      isActive: json['is_active'] ?? true,
      isTriggered: json['is_triggered'] ?? false,
      triggeredAt: json['triggered_at'] != null
          ? DateTime.parse(json['triggered_at'])
          : null,
      notes: json['notes'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'stock_id': stockId,
      'stock_name': stockName,
      'alert_type': alertType,
      'target_price': targetPrice,
      'percent_change': percentChange,
      'notes': notes,
    };
  }

  /// 告警類型名稱（中文）
  String get alertTypeName {
    const typeNames = {
      'above_price': '高於目標價',
      'below_price': '低於目標價',
      'percent_change_up': '漲幅達標',
      'percent_change_down': '跌幅達標',
    };
    return typeNames[alertType] ?? alertType;
  }

  /// 告警類型圖標
  String get alertTypeIcon {
    if (alertType.contains('above') || alertType.contains('up')) {
      return '▲';
    } else if (alertType.contains('below') || alertType.contains('down')) {
      return '▼';
    }
    return '●';
  }

  /// 是否為漲類告警
  bool get isUpAlert =>
      alertType == 'above_price' || alertType == 'percent_change_up';

  /// 是否為跌類告警
  bool get isDownAlert =>
      alertType == 'below_price' || alertType == 'percent_change_down';
}

/// 告警列表響應
class AlertListResponse {
  final List<PriceAlert> alerts;
  final int total;

  AlertListResponse({
    required this.alerts,
    required this.total,
  });

  factory AlertListResponse.fromJson(Map<String, dynamic> json) {
    return AlertListResponse(
      alerts: (json['alerts'] as List)
          .map((e) => PriceAlert.fromJson(e))
          .toList(),
      total: json['total'],
    );
  }
}

/// 創建告警請求
class CreateAlertRequest {
  final String stockId;
  final String stockName;
  final String alertType;
  final double targetPrice;
  final double? percentChange;
  final String? notes;

  CreateAlertRequest({
    required this.stockId,
    required this.stockName,
    required this.alertType,
    required this.targetPrice,
    this.percentChange,
    this.notes,
  });

  Map<String, dynamic> toJson() {
    return {
      'stock_id': stockId,
      'stock_name': stockName,
      'alert_type': alertType,
      'target_price': targetPrice,
      if (percentChange != null) 'percent_change': percentChange,
      if (notes != null) 'notes': notes,
    };
  }
}

/// 告警統計
class AlertStats {
  final int totalAlerts;
  final int activeAlerts;
  final int triggeredAlerts;

  AlertStats({
    required this.totalAlerts,
    required this.activeAlerts,
    required this.triggeredAlerts,
  });

  factory AlertStats.fromJson(Map<String, dynamic> json) {
    return AlertStats(
      totalAlerts: json['total_alerts'] ?? 0,
      activeAlerts: json['active_alerts'] ?? 0,
      triggeredAlerts: json['triggered_alerts'] ?? 0,
    );
  }
}
