import 'package:flutter/foundation.dart';
import '../models/broker.dart';
import '../services/api_service.dart';

class BrokerProvider with ChangeNotifier {
  final ApiService _apiService;

  BrokerAccount _account = BrokerAccount.unlinked();
  List<BrokerPosition> _positions = [];
  bool _isLoading = false;
  bool _isSyncing = false;
  String? _error;

  BrokerProvider(this._apiService);

  // Getters
  BrokerAccount get account => _account;
  List<BrokerPosition> get positions => _positions;
  bool get isLoading => _isLoading;
  bool get isSyncing => _isSyncing;
  String? get error => _error;
  bool get isLinked => _account.linked;

  double get totalMarketValue =>
      _positions.fold(0, (sum, p) => sum + p.marketValue);
  double get totalUnrealizedPnl =>
      _positions.fold(0, (sum, p) => sum + p.unrealizedPnl);

  /// 載入連結狀態
  Future<void> loadStatus() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _account = await _apiService.getBrokerStatus();
      if (_account.linked) {
        _positions = await _apiService.getBrokerPositions();
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 連結帳戶
  Future<BrokerLinkResponse> linkAccount(
      String username, String password, String pin) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _apiService.linkBroker(username, password, pin);
      if (result.isActive) {
        await loadStatus();
      }
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  /// 驗證 2FA
  Future<BrokerLinkResponse> verify2FA(int accountId, String code) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final result = await _apiService.verifyBroker2FA(accountId, code);
      if (result.isActive) {
        await loadStatus();
      }
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  /// 同步持倉
  Future<void> syncPositions() async {
    _isSyncing = true;
    _error = null;
    notifyListeners();

    try {
      await _apiService.syncBroker();
      _positions = await _apiService.getBrokerPositions();
      _account = await _apiService.getBrokerStatus();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isSyncing = false;
      notifyListeners();
    }
  }

  /// 解除連結
  Future<void> unlinkAccount() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _apiService.unlinkBroker();
      _account = BrokerAccount.unlinked();
      _positions = [];
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
