import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/notification.dart' hide TimeOfDay;
import '../models/notification.dart' as notif;
import '../services/notification_service.dart';

/// 通知狀態管理 Provider
class NotificationProvider with ChangeNotifier {
  final NotificationService _notificationService = NotificationService();

  List<AppNotification> _notifications = [];
  bool _isInitialized = false;
  bool _hasPermission = false;
  NotificationPreferences _preferences = NotificationPreferences();

  StreamSubscription<List<AppNotification>>? _notificationsSub;
  StreamSubscription<AppNotification>? _newNotificationSub;
  StreamSubscription<AppNotification>? _tappedSub;

  // 導航回調（用於處理通知點擊後的頁面跳轉）
  Function(String route, Map<String, dynamic>? arguments)? onNavigate;

  /// 獲取所有通知
  List<AppNotification> get notifications => _notifications;

  /// 獲取未讀通知數量
  int get unreadCount => _notifications.where((n) => !n.isRead).length;

  /// 是否已初始化
  bool get isInitialized => _isInitialized;

  /// 是否有通知權限
  bool get hasPermission => _hasPermission;

  /// 獲取偏好設置
  NotificationPreferences get preferences => _preferences;

  /// 初始化通知服務
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      // 初始化通知服務
      await _notificationService.initialize();

      // 訂閱通知列表變化
      _notificationsSub = _notificationService.notificationsStream.listen((notifications) {
        _notifications = notifications;
        notifyListeners();
      });

      // 訂閱新通知事件
      _newNotificationSub = _notificationService.onNewNotification.listen(_onNewNotification);

      // 訂閱通知點擊事件
      _tappedSub = _notificationService.onNotificationTapped.listen(_onNotificationTapped);

      _isInitialized = true;
      notifyListeners();

      if (kDebugMode) {
        print('NotificationProvider initialized');
      }
    } catch (e) {
      if (kDebugMode) {
        print('NotificationProvider initialization error: $e');
      }
    }
  }

  /// 請求通知權限
  Future<bool> requestPermission() async {
    _hasPermission = await _notificationService.requestPermission();
    notifyListeners();
    return _hasPermission;
  }

  /// 更新偏好設置
  void updatePreferences(NotificationPreferences preferences) {
    _preferences = preferences;
    _notificationService.updatePreferences(preferences);
    notifyListeners();
  }

  /// 切換推播通知開關
  void togglePushNotification(bool enabled) {
    _preferences = _preferences.copyWith(enablePush: enabled);
    _notificationService.updatePreferences(_preferences);
    notifyListeners();
  }

  /// 切換本地通知開關
  void toggleLocalNotification(bool enabled) {
    _preferences = _preferences.copyWith(enableLocal: enabled);
    _notificationService.updatePreferences(_preferences);
    notifyListeners();
  }

  /// 切換聲音開關
  void toggleSound(bool enabled) {
    _preferences = _preferences.copyWith(enableSound: enabled);
    _notificationService.updatePreferences(_preferences);
    notifyListeners();
  }

  /// 切換震動開關
  void toggleVibration(bool enabled) {
    _preferences = _preferences.copyWith(enableVibration: enabled);
    _notificationService.updatePreferences(_preferences);
    notifyListeners();
  }

  /// 切換特定類型通知開關
  void toggleTypeNotification(NotificationType type, bool enabled) {
    final newTypeEnabled = Map<NotificationType, bool>.from(_preferences.typeEnabled);
    newTypeEnabled[type] = enabled;
    _preferences = _preferences.copyWith(typeEnabled: newTypeEnabled);
    _notificationService.updatePreferences(_preferences);
    notifyListeners();
  }

  /// 設置勿擾時段
  void setQuietHours(notif.QuietHoursTime? start, notif.QuietHoursTime? end) {
    _preferences = _preferences.copyWith(
      quietHoursStart: start,
      quietHoursEnd: end,
    );
    _notificationService.updatePreferences(_preferences);
    notifyListeners();
  }

  /// 發送警報通知
  Future<void> sendAlertNotification({
    required String stockId,
    required String stockName,
    required String alertType,
    double? targetPrice,
    double? currentPrice,
    double? changePercent,
    String market = 'TW',
  }) async {
    await _notificationService.sendAlertNotification(
      stockId: stockId,
      stockName: stockName,
      alertType: alertType,
      targetPrice: targetPrice,
      currentPrice: currentPrice,
      changePercent: changePercent,
      market: market,
    );
  }

  /// 發送 AI 建議通知
  Future<void> sendAISuggestionNotification({
    required String stockId,
    required String stockName,
    required String suggestion,
    required double confidence,
    String market = 'TW',
  }) async {
    await _notificationService.sendAISuggestionNotification(
      stockId: stockId,
      stockName: stockName,
      suggestion: suggestion,
      confidence: confidence,
      market: market,
    );
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
    await _notificationService.sendPatternNotification(
      stockId: stockId,
      stockName: stockName,
      patternName: patternName,
      signal: signal,
      targetPrice: targetPrice,
      market: market,
    );
  }

  /// 發送系統消息
  Future<void> sendSystemMessage({
    required String title,
    required String body,
    NotificationPriority priority = NotificationPriority.normal,
  }) async {
    await _notificationService.sendSystemMessage(
      title: title,
      body: body,
      priority: priority,
    );
  }

  /// 標記通知為已讀
  void markAsRead(String notificationId) {
    _notificationService.markAsRead(notificationId);
  }

  /// 標記所有通知為已讀
  void markAllAsRead() {
    _notificationService.markAllAsRead();
  }

  /// 刪除通知
  void removeNotification(String notificationId) {
    _notificationService.removeNotification(notificationId);
  }

  /// 清除所有通知
  void clearAll() {
    _notificationService.clearAll();
  }

  /// 處理新通知事件
  void _onNewNotification(AppNotification notification) {
    // 可在此添加額外的新通知處理邏輯
    if (kDebugMode) {
      print('New notification received: ${notification.title}');
    }
  }

  /// 處理通知點擊事件
  void _onNotificationTapped(AppNotification notification) {
    // 標記為已讀
    markAsRead(notification.id);

    // 導航到目標頁面
    final route = notification.targetRoute;
    if (route != null && onNavigate != null) {
      onNavigate!(route, notification.targetArguments);
    }
  }

  @override
  void dispose() {
    _notificationsSub?.cancel();
    _newNotificationSub?.cancel();
    _tappedSub?.cancel();
    super.dispose();
  }
}
