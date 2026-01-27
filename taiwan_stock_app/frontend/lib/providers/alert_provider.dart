import 'package:flutter/foundation.dart';
import '../models/price_alert.dart';
import '../services/api_service.dart';

class AlertProvider with ChangeNotifier {
  final ApiService _apiService;
  List<PriceAlert> _alerts = [];
  List<PriceAlert> _triggeredAlerts = [];
  bool _isLoading = false;
  String? _error;

  AlertProvider(this._apiService);

  List<PriceAlert> get alerts => _alerts;
  List<PriceAlert> get triggeredAlerts => _triggeredAlerts;
  List<PriceAlert> get activeAlerts =>
      _alerts.where((a) => a.isActive && !a.isTriggered).toList();
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadAlerts() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _apiService.getAlerts();
      _alerts = data.map((e) => PriceAlert.fromJson(e)).toList();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadTriggeredAlerts() async {
    try {
      final data = await _apiService.getTriggeredAlerts();
      _triggeredAlerts = data.map((e) => PriceAlert.fromJson(e)).toList();
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<void> refresh() async {
    await loadAlerts();
    await loadTriggeredAlerts();
  }

  Future<void> createAlert({
    required String stockId,
    required String alertType,
    double? targetPrice,
    double? percentThreshold,
    bool notifyPush = true,
    bool notifyEmail = false,
    String? notes,
  }) async {
    try {
      await _apiService.createAlert(
        stockId: stockId,
        alertType: alertType,
        targetPrice: targetPrice,
        percentThreshold: percentThreshold,
        notifyPush: notifyPush,
        notifyEmail: notifyEmail,
        notes: notes,
      );
      await loadAlerts();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> updateAlert(
    int alertId, {
    String? alertType,
    double? targetPrice,
    double? percentThreshold,
    bool? notifyPush,
    bool? notifyEmail,
    String? notes,
  }) async {
    try {
      await _apiService.updateAlert(
        alertId,
        alertType: alertType,
        targetPrice: targetPrice,
        percentThreshold: percentThreshold,
        notifyPush: notifyPush,
        notifyEmail: notifyEmail,
        notes: notes,
      );
      await loadAlerts();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> deleteAlert(int alertId) async {
    try {
      await _apiService.deleteAlert(alertId);
      _alerts.removeWhere((alert) => alert.id == alertId);
      _triggeredAlerts.removeWhere((alert) => alert.id == alertId);
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> toggleAlert(int alertId) async {
    try {
      await _apiService.toggleAlert(alertId);
      await loadAlerts();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> resetAlert(int alertId) async {
    try {
      await _apiService.resetAlert(alertId);
      await loadAlerts();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  List<PriceAlert> getAlertsForStock(String stockId) {
    return _alerts.where((a) => a.stockId == stockId).toList();
  }
}
