import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../models/notification.dart';

/// 本地通知服務
/// 處理應用內的本地通知顯示和交互
class LocalNotificationService {
  static final LocalNotificationService _instance = LocalNotificationService._internal();
  factory LocalNotificationService() => _instance;
  LocalNotificationService._internal();

  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  final StreamController<AppNotification> _onTappedController = StreamController<AppNotification>.broadcast();

  bool _isInitialized = false;
  NotificationPreferences _preferences = NotificationPreferences();

  /// 通知點擊事件流
  Stream<AppNotification> get onTapped => _onTappedController.stream;

  /// 初始化本地通知服務
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      // Android 初始化設置
      const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');

      // iOS 初始化設置
      const iosSettings = DarwinInitializationSettings(
        requestAlertPermission: false,
        requestBadgePermission: false,
        requestSoundPermission: false,
      );

      const initSettings = InitializationSettings(
        android: androidSettings,
        iOS: iosSettings,
      );

      final initialized = await _plugin.initialize(
        initSettings,
        onDidReceiveNotificationResponse: _onNotificationResponse,
        onDidReceiveBackgroundNotificationResponse: _onBackgroundNotificationResponse,
      );

      _isInitialized = initialized ?? false;

      if (kDebugMode) {
        print('LocalNotificationService initialized: $_isInitialized');
      }

      return _isInitialized;
    } catch (e) {
      if (kDebugMode) {
        print('LocalNotificationService initialization error: $e');
      }
      return false;
    }
  }

  /// 請求通知權限
  Future<bool> requestPermission() async {
    try {
      // Android 13+ 需要請求權限
      final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>();
      if (androidPlugin != null) {
        final granted = await androidPlugin.requestNotificationsPermission();
        return granted ?? false;
      }

      // iOS 請求權限
      final iosPlugin = _plugin.resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin>();
      if (iosPlugin != null) {
        final granted = await iosPlugin.requestPermissions(
          alert: true,
          badge: true,
          sound: true,
        );
        return granted ?? false;
      }

      return true;
    } catch (e) {
      if (kDebugMode) {
        print('Request permission error: $e');
      }
      return false;
    }
  }

  /// 更新偏好設置
  void updatePreferences(NotificationPreferences preferences) {
    _preferences = preferences;
  }

  /// 顯示通知
  Future<void> show(AppNotification notification) async {
    if (!_isInitialized) {
      await initialize();
    }

    // 檢查偏好設置
    if (!_preferences.enableLocal) return;
    if (!_preferences.isTypeEnabled(notification.type)) return;
    if (_preferences.isInQuietHours()) return;

    try {
      final androidDetails = AndroidNotificationDetails(
        _getChannelId(notification.type),
        _getChannelName(notification.type),
        channelDescription: _getChannelDescription(notification.type),
        importance: _mapImportance(notification.priority),
        priority: _mapPriority(notification.priority),
        enableVibration: _preferences.enableVibration,
        playSound: _preferences.enableSound,
        icon: '@mipmap/ic_launcher',
        largeIcon: const DrawableResourceAndroidBitmap('@mipmap/ic_launcher'),
        styleInformation: BigTextStyleInformation(
          notification.body,
          contentTitle: notification.title,
          summaryText: _getTypeSummary(notification.type),
        ),
      );

      final iosDetails = DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: _preferences.enableBadge,
        presentSound: _preferences.enableSound,
        threadIdentifier: _getChannelId(notification.type),
      );

      final details = NotificationDetails(
        android: androidDetails,
        iOS: iosDetails,
      );

      await _plugin.show(
        notification.hashCode,
        notification.title,
        notification.body,
        details,
        payload: jsonEncode(notification.toJson()),
      );

      if (kDebugMode) {
        print('Notification shown: ${notification.title}');
      }
    } catch (e) {
      if (kDebugMode) {
        print('Show notification error: $e');
      }
    }
  }

  /// 取消指定通知
  Future<void> cancel(int id) async {
    await _plugin.cancel(id);
  }

  /// 取消所有通知
  Future<void> cancelAll() async {
    await _plugin.cancelAll();
  }

  /// 獲取待處理通知
  Future<List<PendingNotificationRequest>> getPendingNotifications() async {
    return await _plugin.pendingNotificationRequests();
  }

  /// 處理通知點擊（前景）
  void _onNotificationResponse(NotificationResponse response) {
    _handleNotificationTap(response.payload);
  }

  /// 處理通知點擊（背景）
  @pragma('vm:entry-point')
  static void _onBackgroundNotificationResponse(NotificationResponse response) {
    // 背景處理邏輯
    // 注意：此方法需要是靜態的且有 @pragma 註解
  }

  /// 處理通知點擊
  void _handleNotificationTap(String? payload) {
    if (payload == null) return;

    try {
      final json = jsonDecode(payload) as Map<String, dynamic>;
      final notification = AppNotification.fromJson(json);
      _onTappedController.add(notification);
    } catch (e) {
      if (kDebugMode) {
        print('Handle notification tap error: $e');
      }
    }
  }

  /// 獲取通知頻道 ID
  String _getChannelId(NotificationType type) {
    switch (type) {
      case NotificationType.priceAlert:
      case NotificationType.percentChangeAlert:
      case NotificationType.volumeAlert:
        return 'price_alerts';
      case NotificationType.signalAlert:
      case NotificationType.patternDetected:
        return 'trading_signals';
      case NotificationType.aiSuggestion:
        return 'ai_suggestions';
      case NotificationType.news:
        return 'news';
      case NotificationType.systemMessage:
        return 'system';
    }
  }

  /// 獲取通知頻道名稱
  String _getChannelName(NotificationType type) {
    switch (type) {
      case NotificationType.priceAlert:
      case NotificationType.percentChangeAlert:
      case NotificationType.volumeAlert:
        return '價格警報';
      case NotificationType.signalAlert:
      case NotificationType.patternDetected:
        return '交易信號';
      case NotificationType.aiSuggestion:
        return 'AI 建議';
      case NotificationType.news:
        return '新聞資訊';
      case NotificationType.systemMessage:
        return '系統消息';
    }
  }

  /// 獲取通知頻道描述
  String _getChannelDescription(NotificationType type) {
    switch (type) {
      case NotificationType.priceAlert:
      case NotificationType.percentChangeAlert:
      case NotificationType.volumeAlert:
        return '股票價格和漲跌幅警報通知';
      case NotificationType.signalAlert:
      case NotificationType.patternDetected:
        return '交易信號和形態識別通知';
      case NotificationType.aiSuggestion:
        return 'AI 投資建議更新通知';
      case NotificationType.news:
        return '重要財經新聞通知';
      case NotificationType.systemMessage:
        return '系統公告和提醒';
    }
  }

  /// 獲取類型摘要文字
  String _getTypeSummary(NotificationType type) {
    switch (type) {
      case NotificationType.priceAlert:
        return '價格警報';
      case NotificationType.percentChangeAlert:
        return '漲跌幅警報';
      case NotificationType.volumeAlert:
        return '成交量警報';
      case NotificationType.signalAlert:
        return '交易信號';
      case NotificationType.patternDetected:
        return '形態識別';
      case NotificationType.aiSuggestion:
        return 'AI 建議';
      case NotificationType.news:
        return '財經新聞';
      case NotificationType.systemMessage:
        return '系統消息';
    }
  }

  /// 映射優先級到 Android Importance
  Importance _mapImportance(NotificationPriority priority) {
    switch (priority) {
      case NotificationPriority.low:
        return Importance.low;
      case NotificationPriority.normal:
        return Importance.defaultImportance;
      case NotificationPriority.high:
        return Importance.high;
      case NotificationPriority.urgent:
        return Importance.max;
    }
  }

  /// 映射優先級到 Android Priority
  Priority _mapPriority(NotificationPriority priority) {
    switch (priority) {
      case NotificationPriority.low:
        return Priority.low;
      case NotificationPriority.normal:
        return Priority.defaultPriority;
      case NotificationPriority.high:
        return Priority.high;
      case NotificationPriority.urgent:
        return Priority.max;
    }
  }

  /// 釋放資源
  void dispose() {
    _onTappedController.close();
  }
}
