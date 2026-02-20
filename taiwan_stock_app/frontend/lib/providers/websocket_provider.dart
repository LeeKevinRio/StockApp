import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../services/api_service.dart';

/// 股票即時更新數據
class StockUpdate {
  final String stockId;
  final String name;
  final double currentPrice;
  final double change;
  final double changePercent;
  final int volume;
  final DateTime timestamp;

  StockUpdate({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.change,
    required this.changePercent,
    required this.volume,
    required this.timestamp,
  });

  factory StockUpdate.fromJson(Map<String, dynamic> json) {
    return StockUpdate(
      stockId: json['stock_id'] ?? '',
      name: json['name'] ?? '',
      currentPrice: (json['current_price'] as num?)?.toDouble() ?? 0,
      change: (json['change'] as num?)?.toDouble() ?? 0,
      changePercent: (json['change_percent'] as num?)?.toDouble() ?? 0,
      volume: json['volume'] ?? 0,
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'])
          : DateTime.now(),
    );
  }

  bool get isUp => change > 0;
  bool get isDown => change < 0;
}

/// WebSocket 連接狀態
enum WebSocketState {
  disconnected,
  connecting,
  connected,
  reconnecting,
  /// 已達最大重連次數，停止嘗試
  failed,
}

class WebSocketProvider with ChangeNotifier {
  final ApiService _apiService;
  WebSocketChannel? _channel;
  WebSocketState _state = WebSocketState.disconnected;
  final Map<String, StockUpdate> _latestUpdates = {};
  final Set<String> _subscribedStocks = {};
  StreamSubscription? _subscription;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 5;

  WebSocketProvider(this._apiService);

  // Getters
  WebSocketState get state => _state;
  bool get isConnected => _state == WebSocketState.connected;
  bool get hasFailed => _state == WebSocketState.failed;
  int get reconnectAttempts => _reconnectAttempts;
  int get maxReconnectAttempts => _maxReconnectAttempts;
  Map<String, StockUpdate> get latestUpdates => _latestUpdates;
  Set<String> get subscribedStocks => _subscribedStocks;

  /// 獲取特定股票的最新更新
  StockUpdate? getUpdate(String stockId) => _latestUpdates[stockId];

  /// 連接 WebSocket
  Future<void> connect() async {
    if (_state == WebSocketState.connected ||
        _state == WebSocketState.connecting) {
      return;
    }

    _state = WebSocketState.connecting;
    notifyListeners();

    try {
      _channel = _apiService.connectWebSocket();

      _subscription = _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );

      _state = WebSocketState.connected;
      _reconnectAttempts = 0;
      notifyListeners();

      // 重新訂閱之前的股票
      for (final stockId in _subscribedStocks) {
        _sendSubscribe(stockId);
      }
    } catch (e) {
      _state = WebSocketState.disconnected;
      notifyListeners();
      _scheduleReconnect();
    }
  }

  /// 斷開連接
  void disconnect() {
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _channel = null;
    _reconnectAttempts = 0;
    _state = WebSocketState.disconnected;
    notifyListeners();
  }

  /// 訂閱股票
  void subscribeStock(String stockId) {
    _subscribedStocks.add(stockId);
    if (isConnected) {
      _sendSubscribe(stockId);
    }
  }

  /// 取消訂閱股票
  void unsubscribeStock(String stockId) {
    _subscribedStocks.remove(stockId);
    _latestUpdates.remove(stockId);
    if (isConnected) {
      _sendUnsubscribe(stockId);
    }
    notifyListeners();
  }

  /// 發送訂閱消息
  void _sendSubscribe(String stockId) {
    _channel?.sink.add(jsonEncode({
      'action': 'subscribe',
      'stock_id': stockId,
    }));
  }

  /// 發送取消訂閱消息
  void _sendUnsubscribe(String stockId) {
    _channel?.sink.add(jsonEncode({
      'action': 'unsubscribe',
      'stock_id': stockId,
    }));
  }

  /// 處理收到的消息
  void _onMessage(dynamic message) {
    try {
      final data = jsonDecode(message as String);

      if (data['type'] == 'price_update') {
        final update = StockUpdate.fromJson(data['data']);
        _latestUpdates[update.stockId] = update;
        notifyListeners();
      } else if (data['type'] == 'alert_triggered') {
        // 處理告警觸發通知
        // 可以通過回調或事件來通知 UI
      }
    } catch (e) {
      debugPrint('WebSocket message parse error: $e');
    }
  }

  /// 處理錯誤
  void _onError(dynamic error) {
    debugPrint('WebSocket error: $error');
    _state = WebSocketState.disconnected;
    notifyListeners();
    _scheduleReconnect();
  }

  /// 處理連接關閉
  void _onDone() {
    _state = WebSocketState.disconnected;
    notifyListeners();
    _scheduleReconnect();
  }

  /// 排程重連
  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      _state = WebSocketState.failed;
      notifyListeners();
      debugPrint(
        'WebSocket: 已達最大重連次數 ($_maxReconnectAttempts)，停止重連。'
        '請呼叫 reconnect() 手動重試。',
      );
      return;
    }

    _reconnectTimer?.cancel();
    _state = WebSocketState.reconnecting;
    notifyListeners();

    // 指數退避重連（1s, 2s, 4s, 8s, 16s，上限 30s）
    final delay = Duration(seconds: (1 << _reconnectAttempts).clamp(1, 30));
    _reconnectAttempts++;

    debugPrint(
      'WebSocket: 第 $_reconnectAttempts/$_maxReconnectAttempts 次重連，'
      '${delay.inSeconds} 秒後嘗試...',
    );

    _reconnectTimer = Timer(delay, () {
      connect();
    });
  }

  /// 手動重連
  Future<void> reconnect() async {
    _reconnectAttempts = 0;
    disconnect();
    await connect();
  }

  @override
  void dispose() {
    disconnect();
    super.dispose();
  }
}
