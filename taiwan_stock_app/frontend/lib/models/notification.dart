/// 應用通知數據模型

enum NotificationType {
  priceAlert,           // 價格警報
  percentChangeAlert,   // 漲跌幅警報
  volumeAlert,          // 成交量警報
  signalAlert,          // 信號警報
  aiSuggestion,         // AI 建議更新
  patternDetected,      // 形態識別
  news,                 // 重要新聞
  systemMessage,        // 系統消息
}

enum NotificationPriority {
  low,
  normal,
  high,
  urgent,
}

class AppNotification {
  final String id;
  final NotificationType type;
  final String title;
  final String body;
  final Map<String, dynamic>? data;
  final DateTime createdAt;
  final bool isRead;
  final NotificationPriority priority;

  AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    this.data,
    required this.createdAt,
    this.isRead = false,
    this.priority = NotificationPriority.normal,
  });

  /// 獲取導航目標路由
  String? get targetRoute {
    switch (type) {
      case NotificationType.priceAlert:
      case NotificationType.percentChangeAlert:
      case NotificationType.volumeAlert:
      case NotificationType.signalAlert:
      case NotificationType.patternDetected:
        return '/stock-detail';
      case NotificationType.aiSuggestion:
        return '/home'; // AI suggestions tab
      case NotificationType.news:
        return '/news';
      case NotificationType.systemMessage:
        return null;
    }
  }

  /// 獲取導航參數
  Map<String, dynamic>? get targetArguments {
    if (data == null) return null;
    final stockId = data!['stockId'] as String?;
    final market = data!['market'] as String? ?? 'TW';
    if (stockId != null) {
      return {'stockId': stockId, 'market': market};
    }
    return null;
  }

  /// 獲取通知圖標
  String get iconName {
    switch (type) {
      case NotificationType.priceAlert:
        return 'trending_up';
      case NotificationType.percentChangeAlert:
        return 'percent';
      case NotificationType.volumeAlert:
        return 'bar_chart';
      case NotificationType.signalAlert:
        return 'notifications_active';
      case NotificationType.aiSuggestion:
        return 'psychology';
      case NotificationType.patternDetected:
        return 'auto_graph';
      case NotificationType.news:
        return 'article';
      case NotificationType.systemMessage:
        return 'info';
    }
  }

  /// 從 JSON 創建
  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as String,
      type: NotificationType.values.firstWhere(
        (e) => e.name == json['type'],
        orElse: () => NotificationType.systemMessage,
      ),
      title: json['title'] as String,
      body: json['body'] as String,
      data: json['data'] as Map<String, dynamic>?,
      createdAt: DateTime.parse(json['created_at'] as String),
      isRead: json['is_read'] as bool? ?? false,
      priority: NotificationPriority.values.firstWhere(
        (e) => e.name == json['priority'],
        orElse: () => NotificationPriority.normal,
      ),
    );
  }

  /// 轉換為 JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type.name,
      'title': title,
      'body': body,
      'data': data,
      'created_at': createdAt.toIso8601String(),
      'is_read': isRead,
      'priority': priority.name,
    };
  }

  /// 創建已讀副本
  AppNotification copyWithRead() {
    return AppNotification(
      id: id,
      type: type,
      title: title,
      body: body,
      data: data,
      createdAt: createdAt,
      isRead: true,
      priority: priority,
    );
  }

  /// 從警報數據創建通知
  factory AppNotification.fromAlert({
    required String stockId,
    required String stockName,
    required String alertType,
    required double? targetPrice,
    required double? currentPrice,
    required double? changePercent,
    String market = 'TW',
  }) {
    final type = _mapAlertType(alertType);
    final title = _generateAlertTitle(type, stockName);
    final body = _generateAlertBody(
      type: type,
      stockName: stockName,
      targetPrice: targetPrice,
      currentPrice: currentPrice,
      changePercent: changePercent,
    );

    return AppNotification(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: type,
      title: title,
      body: body,
      data: {
        'stockId': stockId,
        'stockName': stockName,
        'market': market,
        'targetPrice': targetPrice,
        'currentPrice': currentPrice,
        'changePercent': changePercent,
      },
      createdAt: DateTime.now(),
      priority: NotificationPriority.high,
    );
  }

  static NotificationType _mapAlertType(String alertType) {
    switch (alertType.toUpperCase()) {
      case 'ABOVE':
      case 'BELOW':
      case 'PRICE_ABOVE':
      case 'PRICE_BELOW':
        return NotificationType.priceAlert;
      case 'PERCENT_UP':
      case 'PERCENT_DOWN':
      case 'CHANGE_PERCENT_ABOVE':
      case 'CHANGE_PERCENT_BELOW':
        return NotificationType.percentChangeAlert;
      case 'VOLUME_ABOVE':
        return NotificationType.volumeAlert;
      case 'SIGNAL_BUY':
      case 'SIGNAL_SELL':
        return NotificationType.signalAlert;
      default:
        return NotificationType.priceAlert;
    }
  }

  static String _generateAlertTitle(NotificationType type, String stockName) {
    switch (type) {
      case NotificationType.priceAlert:
        return '價格警報觸發';
      case NotificationType.percentChangeAlert:
        return '漲跌幅警報觸發';
      case NotificationType.volumeAlert:
        return '成交量警報觸發';
      case NotificationType.signalAlert:
        return '交易信號提醒';
      default:
        return '警報通知';
    }
  }

  static String _generateAlertBody({
    required NotificationType type,
    required String stockName,
    double? targetPrice,
    double? currentPrice,
    double? changePercent,
  }) {
    final priceStr = currentPrice != null ? currentPrice.toStringAsFixed(2) : '-';
    final changeStr = changePercent != null
        ? '${changePercent >= 0 ? '+' : ''}${changePercent.toStringAsFixed(2)}%'
        : '';

    switch (type) {
      case NotificationType.priceAlert:
        return '$stockName 現價 $priceStr，已達到目標價 ${targetPrice?.toStringAsFixed(2) ?? '-'}';
      case NotificationType.percentChangeAlert:
        return '$stockName 現價 $priceStr，漲跌幅 $changeStr';
      case NotificationType.volumeAlert:
        return '$stockName 成交量異常放大';
      case NotificationType.signalAlert:
        return '$stockName 出現交易信號';
      default:
        return '$stockName 警報觸發';
    }
  }
}

/// 通知偏好設置
class NotificationPreferences {
  final bool enablePush;
  final bool enableLocal;
  final bool enableSound;
  final bool enableVibration;
  final bool enableBadge;
  final Map<NotificationType, bool> typeEnabled;
  final TimeOfDay? quietHoursStart;
  final TimeOfDay? quietHoursEnd;

  NotificationPreferences({
    this.enablePush = true,
    this.enableLocal = true,
    this.enableSound = true,
    this.enableVibration = true,
    this.enableBadge = true,
    Map<NotificationType, bool>? typeEnabled,
    this.quietHoursStart,
    this.quietHoursEnd,
  }) : typeEnabled = typeEnabled ?? _defaultTypeEnabled();

  static Map<NotificationType, bool> _defaultTypeEnabled() {
    return {
      for (var type in NotificationType.values) type: true,
    };
  }

  bool isTypeEnabled(NotificationType type) {
    return typeEnabled[type] ?? true;
  }

  bool isInQuietHours() {
    if (quietHoursStart == null || quietHoursEnd == null) return false;

    final now = TimeOfDay.now();
    final nowMinutes = now.hour * 60 + now.minute;
    final startMinutes = quietHoursStart!.hour * 60 + quietHoursStart!.minute;
    final endMinutes = quietHoursEnd!.hour * 60 + quietHoursEnd!.minute;

    if (startMinutes <= endMinutes) {
      return nowMinutes >= startMinutes && nowMinutes <= endMinutes;
    } else {
      // 跨午夜
      return nowMinutes >= startMinutes || nowMinutes <= endMinutes;
    }
  }

  NotificationPreferences copyWith({
    bool? enablePush,
    bool? enableLocal,
    bool? enableSound,
    bool? enableVibration,
    bool? enableBadge,
    Map<NotificationType, bool>? typeEnabled,
    TimeOfDay? quietHoursStart,
    TimeOfDay? quietHoursEnd,
  }) {
    return NotificationPreferences(
      enablePush: enablePush ?? this.enablePush,
      enableLocal: enableLocal ?? this.enableLocal,
      enableSound: enableSound ?? this.enableSound,
      enableVibration: enableVibration ?? this.enableVibration,
      enableBadge: enableBadge ?? this.enableBadge,
      typeEnabled: typeEnabled ?? this.typeEnabled,
      quietHoursStart: quietHoursStart ?? this.quietHoursStart,
      quietHoursEnd: quietHoursEnd ?? this.quietHoursEnd,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'enable_push': enablePush,
      'enable_local': enableLocal,
      'enable_sound': enableSound,
      'enable_vibration': enableVibration,
      'enable_badge': enableBadge,
      'type_enabled': typeEnabled.map((k, v) => MapEntry(k.name, v)),
      'quiet_hours_start': quietHoursStart != null
          ? '${quietHoursStart!.hour.toString().padLeft(2, '0')}:${quietHoursStart!.minute.toString().padLeft(2, '0')}'
          : null,
      'quiet_hours_end': quietHoursEnd != null
          ? '${quietHoursEnd!.hour.toString().padLeft(2, '0')}:${quietHoursEnd!.minute.toString().padLeft(2, '0')}'
          : null,
    };
  }

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    TimeOfDay? parseTime(String? timeStr) {
      if (timeStr == null) return null;
      final parts = timeStr.split(':');
      return TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
    }

    return NotificationPreferences(
      enablePush: json['enable_push'] as bool? ?? true,
      enableLocal: json['enable_local'] as bool? ?? true,
      enableSound: json['enable_sound'] as bool? ?? true,
      enableVibration: json['enable_vibration'] as bool? ?? true,
      enableBadge: json['enable_badge'] as bool? ?? true,
      typeEnabled: (json['type_enabled'] as Map<String, dynamic>?)?.map(
            (k, v) => MapEntry(
              NotificationType.values.firstWhere((e) => e.name == k),
              v as bool,
            ),
          ) ??
          _defaultTypeEnabled(),
      quietHoursStart: parseTime(json['quiet_hours_start'] as String?),
      quietHoursEnd: parseTime(json['quiet_hours_end'] as String?),
    );
  }
}

/// 自定義時間類（用於勿擾時段設置）
/// 避免與 Flutter 的 TimeOfDay 衝突
class QuietHoursTime {
  final int hour;
  final int minute;

  const QuietHoursTime({required this.hour, required this.minute});

  factory QuietHoursTime.now() {
    final now = DateTime.now();
    return QuietHoursTime(hour: now.hour, minute: now.minute);
  }

  @override
  String toString() {
    return '${hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')}';
  }
}

/// TimeOfDay 別名（為了向後兼容）
typedef TimeOfDay = QuietHoursTime;
