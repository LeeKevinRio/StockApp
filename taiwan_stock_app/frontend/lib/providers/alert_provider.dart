import 'package:flutter/foundation.dart';
import '../models/alert.dart';
import '../services/api_service.dart';

class AlertProvider with ChangeNotifier {
  final ApiService _apiService;
  List<PriceAlert> _alerts = [];
  bool _isLoading = false;
  String? _error;

  AlertProvider(this._apiService);

  List<PriceAlert> get alerts => _alerts;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// 獲取啟用中的告警
  List<PriceAlert> get activeAlerts =>
      _alerts.where((a) => a.isActive && !a.isTriggered).toList();

  /// 獲取已觸發的告警
  List<PriceAlert> get triggeredAlerts =>
      _alerts.where((a) => a.isTriggered).toList();

  /// 告警數量統計
  int get totalCount => _alerts.length;
  int get activeCount => activeAlerts.length;
  int get triggeredCount => triggeredAlerts.length;

  /// 載入所有告警
  Future<void> loadAlerts({bool? activeOnly}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _alerts = await _apiService.getAlerts(activeOnly: activeOnly);
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 刷新
  Future<void> refresh() async {
    await loadAlerts();
  }

  /// 創建告警
  Future<PriceAlert> createAlert(CreateAlertRequest request) async {
    try {
      final alert = await _apiService.createAlert(request);
      _alerts.insert(0, alert);
      notifyListeners();
      return alert;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 刪除告警
  Future<void> deleteAlert(int alertId) async {
    try {
      await _apiService.deleteAlert(alertId);
      _alerts.removeWhere((a) => a.id == alertId);
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 切換告警狀態
  Future<void> toggleAlert(int alertId) async {
    try {
      final alert = _alerts.firstWhere((a) => a.id == alertId);
      final updated = await _apiService.toggleAlert(alertId, !alert.isActive);
      final index = _alerts.indexWhere((a) => a.id == alertId);
      if (index != -1) {
        _alerts[index] = updated;
        notifyListeners();
      }
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 檢查告警（觸發檢測）
  Future<List<PriceAlert>> checkAlerts() async {
    try {
      final triggered = await _apiService.checkAlerts();
      // 刷新列表以獲取最新狀態
      await loadAlerts();
      return triggered;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 根據股票ID獲取告警
  List<PriceAlert> getAlertsForStock(String stockId) {
    return _alerts.where((a) => a.stockId == stockId).toList();
  }

  /// 清除錯誤
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
