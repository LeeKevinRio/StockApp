import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Stock market enum
enum StockMarket { taiwan, us }

/// Market provider for managing current market selection
///
/// 注意：此 provider 只決定「資料來源市場」，不影響 UI 語系（語系由 LocaleProvider 管理）。
class MarketProvider with ChangeNotifier {
  static const String _key = 'app_default_market';

  StockMarket _currentMarket = StockMarket.taiwan;
  bool _initialized = false;

  MarketProvider() {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final code = prefs.getString(_key);
      if (code == 'US') {
        _currentMarket = StockMarket.us;
      }
    } catch (_) {
      // 失敗時保留預設台股
    }
    _initialized = true;
    notifyListeners();
  }

  Future<void> _persist() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_key, marketCode);
    } catch (_) {
      // 儲存失敗不影響 in-memory 狀態
    }
  }

  bool get initialized => _initialized;

  /// Get current market
  StockMarket get currentMarket => _currentMarket;

  /// Get market code for API calls
  String get marketCode => _currentMarket == StockMarket.taiwan ? 'TW' : 'US';

  /// Check if current market is Taiwan
  bool get isTaiwanMarket => _currentMarket == StockMarket.taiwan;

  /// Check if current market is US
  bool get isUSMarket => _currentMarket == StockMarket.us;

  /// Get currency symbol for current market
  String get currencySymbol => _currentMarket == StockMarket.taiwan ? 'NT\$' : '\$';

  /// Get currency code for current market
  String get currencyCode => _currentMarket == StockMarket.taiwan ? 'TWD' : 'USD';

  /// Get market display name
  String get marketDisplayName => _currentMarket == StockMarket.taiwan ? '台股' : '美股';

  /// Switch to a specific market
  void switchMarket(StockMarket market) {
    if (_currentMarket != market) {
      _currentMarket = market;
      notifyListeners();
      _persist();
    }
  }

  /// Toggle between markets
  void toggleMarket() {
    _currentMarket = _currentMarket == StockMarket.taiwan
        ? StockMarket.us
        : StockMarket.taiwan;
    notifyListeners();
    _persist();
  }

  /// Set market by code string
  void setMarketByCode(String code) {
    final market = code.toUpperCase() == 'US'
        ? StockMarket.us
        : StockMarket.taiwan;
    switchMarket(market);
  }
}
