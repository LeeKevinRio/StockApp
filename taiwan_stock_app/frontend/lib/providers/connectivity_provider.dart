import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';

/// 網路連線狀態 Provider
/// 定期 ping 後端 /health 端點檢查連線
class ConnectivityProvider extends ChangeNotifier {
  bool _isOnline = true;
  Timer? _timer;

  /// 連續失敗次數，需累積到門檻才判定離線，避免單次逾時誤報
  int _consecutiveFailures = 0;

  /// 連續失敗幾次才判定離線（Render 冷啟動 / 偶發慢回應的容錯）
  static const int _failureThreshold = 3;

  /// 單次檢查逾時時間（後端 /health 會連 DB，冷啟動更久，需放寬）
  static const Duration _checkTimeout = Duration(seconds: 15);

  bool get isOnline => _isOnline;
  bool get isOffline => !_isOnline;

  ConnectivityProvider() {
    _checkConnectivity();
    // 每 30 秒檢查一次連線狀態
    _timer = Timer.periodic(const Duration(seconds: 30), (_) {
      _checkConnectivity();
    });
  }

  Future<void> _checkConnectivity() async {
    try {
      final response = await http
          .get(Uri.parse('${AppConfig.apiBaseUrl}/health'))
          .timeout(_checkTimeout);
      if (response.statusCode == 200) {
        _onSuccess();
      } else {
        _onFailure();
      }
    } catch (_) {
      _onFailure();
    }
  }

  void _onSuccess() {
    _consecutiveFailures = 0;
    _setOnline(true);
  }

  void _onFailure() {
    _consecutiveFailures++;
    // 只有連續失敗達門檻才判定離線，避免偶發逾時誤報
    if (_consecutiveFailures >= _failureThreshold) {
      _setOnline(false);
    }
  }

  void _setOnline(bool online) {
    if (_isOnline != online) {
      _isOnline = online;
      notifyListeners();
    }
  }

  /// 手動重新檢查連線
  Future<void> retry() async {
    await _checkConnectivity();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}
