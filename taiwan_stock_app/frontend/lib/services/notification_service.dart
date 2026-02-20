import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/notification.dart';
import 'local_notification_service.dart';

/// 統一通知服務
/// 整合本地通知和未來的 FCM 推播通知
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final LocalNotificationService _localService = LocalNotificationService();

  // 通知歷史記錄（內存存儲，可擴展為持久化存儲）
  final List<AppNotification> _notifications = [];
  final StreamController<List<AppNotification>> _notificationsController =
      StreamController<List<AppNotification>>.broadcast();
  final StreamController<AppNotification> _newNotificationController =
      StreamController<AppNotification>.broadcast();

  bool _isInitialized = false;
  NotificationPreferences _preferences = NotificationPreferences();
  StreamSubscription<AppNotification>? _tappedSubscription;

  /// 通知列表流
  Stream<List<AppNotification>> get notificationsStream => _notificationsController.stream;

  /// 新通知事件流
  Stream<AppNotification> get onNewNotification => _newNotificationController.stream;

  /// 通知點擊事件流
  Stream<AppNotification> get onNotificationTapped => _localService.onTapped;

  /// 獲取所有通知
  List<AppNotification> get notifications => List.unmodifiable(_notifications);

  /// 獲取未讀通知數量
  int get unreadCount => _notifications.where((n) => !n.isRead).length;

  /// 初始化通知服務
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      // 初始化本地通知
      final localInitialized = await _localService.initialize();

      // 監聽通知點擊事件（儲存訂閱以便後續取消）
      _tappedSubscription?.cancel();
      _tappedSubscription = _localService.onTapped.listen(_handleNotificationTapped);

      _isInitialized = localInitialized;

      if (kDebugMode) {
        print('NotificationService initialized: $_isInitialized');
      }

      return _isInitialized;
    } catch (e) {
      if (kDebugMode) {
        print('NotificationService initialization error: $e');
      }
      return false;
    }
  }

  /// 請求通知權限
  Future<bool> requestPermission() async {
    return await _localService.requestPermission();
  }

  /// 更新偏好設置
  void updatePreferences(NotificationPreferences preferences) {
    _preferences = preferences;
    _localService.updatePreferences(preferences);
  }

  /// 獲取當前偏好設置
  NotificationPreferences get preferences => _preferences;

  /// 發送通知（顯示本地通知並添加到歷史記錄）
  Future<void> sendNotification(AppNotification notification) async {
    if (!_isInitialized) {
      await initialize();
    }

    // 添加到歷史記錄
    _notifications.insert(0, notification);
    _notificationsController.add(_notifications);
    _newNotificationController.add(notification);

    // 顯示本地通知
    await _localService.show(notification);

    if (kDebugMode) {
      print('Notification sent: ${notification.title}');
    }
  }

  /// 從警報觸發創建並發送通知
  Future<void> sendAlertNotification({
    required String stockId,
    required String stockName,
    required String alertType,
    double? targetPrice,
    double? currentPrice,
    double? changePercent,
    String market = 'TW',
  }) async {
    final notification = AppNotification.fromAlert(
      stockId: stockId,
      stockName: stockName,
      alertType: alertType,
      targetPrice: targetPrice,
      currentPrice: currentPrice,
      changePercent: changePercent,
      market: market,
    );

    await sendNotification(notification);
  }

  /// 發送 AI 建議通知
  Future<void> sendAISuggestionNotification({
    required String stockId,
    required String stockName,
    required String suggestion,
    required double confidence,
    String market = 'TW',
  }) async {
    final suggestionText = _getSuggestionText(suggestion);
    final notification = AppNotification(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: NotificationType.aiSuggestion,
      title: 'AI 投資建議更新',
      body: '$stockName: $suggestionText (信心度 ${(confidence * 100).toInt()}%)',
      data: {
        'stockId': stockId,
        'stockName': stockName,
        'suggestion': suggestion,
        'confidence': confidence,
        'market': market,
      },
      createdAt: DateTime.now(),
      priority: NotificationPriority.normal,
    );

    await sendNotification(notification);
  }

  /// 發送形態識別通知
  Future<void> sendPatternNotification({
    required String stockId,
    required String stockName,
    required String patternName,
    required String signal,
    double? targetPrice,
    String market = 'TW',
  }) async {
    final signalText = signal == 'bullish' ? '看漲' : '看跌';
    final notification = AppNotification(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: NotificationType.patternDetected,
      title: '形態識別提醒',
      body: '$stockName 出現 $patternName 形態 ($signalText)${targetPrice != null ? '，目標價 $targetPrice' : ''}',
      data: {
        'stockId': stockId,
        'stockName': stockName,
        'patternName': patternName,
        'signal': signal,
        'targetPrice': targetPrice,
        'market': market,
      },
      createdAt: DateTime.now(),
      priority: NotificationPriority.high,
    );

    await sendNotification(notification);
  }

  /// 發送系統消息
  Future<void> sendSystemMessage({
    required String title,
    required String body,
    NotificationPriority priority = NotificationPriority.normal,
  }) async {
    final notification = AppNotification(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: NotificationType.systemMessage,
      title: title,
      body: body,
      createdAt: DateTime.now(),
      priority: priority,
    );

    await sendNotification(notification);
  }

  /// 標記通知為已讀
  void markAsRead(String notificationId) {
    final index = _notifications.indexWhere((n) => n.id == notificationId);
    if (index != -1) {
      _notifications[index] = _notifications[index].copyWithRead();
      _notificationsController.add(_notifications);
    }
  }

  /// 標記所有通知為已讀
  void markAllAsRead() {
    for (var i = 0; i < _notifications.length; i++) {
      if (!_notifications[i].isRead) {
        _notifications[i] = _notifications[i].copyWithRead();
      }
    }
    _notificationsController.add(_notifications);
  }

  /// 刪除通知
  void removeNotification(String notificationId) {
    _notifications.removeWhere((n) => n.id == notificationId);
    _notificationsController.add(_notifications);
  }

  /// 清除所有通知
  void clearAll() {
    _notifications.clear();
    _notificationsController.add(_notifications);
    _localService.cancelAll();
  }

  /// 處理通知點擊
  void _handleNotificationTapped(AppNotification notification) {
    markAsRead(notification.id);
  }

  String _getSuggestionText(String suggestion) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return '建議買入';
      case 'SELL':
        return '建議賣出';
      case 'HOLD':
        return '建議持有';
      default:
        return suggestion;
    }
  }

  /// 釋放資源
  void dispose() {
    _tappedSubscription?.cancel();
    _tappedSubscription = null;
    _notificationsController.close();
    _newNotificationController.close();
    _localService.dispose();
    _isInitialized = false;
  }
}
