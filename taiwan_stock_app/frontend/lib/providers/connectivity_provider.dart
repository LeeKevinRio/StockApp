import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';

/// 網路連線狀態 Provider
/// 定期 ping 後端 /health 端點檢查連線
class ConnectivityProvider extends ChangeNotifier {
  bool _isOnline = true;
  Timer? _timer;

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
          .timeout(const Duration(seconds: 5));
      _setOnline(response.statusCode == 200);
    } catch (_) {
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
