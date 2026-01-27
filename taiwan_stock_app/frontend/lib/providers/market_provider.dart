import 'package:flutter/foundation.dart';

/// Stock market enum
enum StockMarket { taiwan, us }

/// Market provider for managing current market selection
class MarketProvider with ChangeNotifier {
  StockMarket _currentMarket = StockMarket.taiwan;

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
    }
  }

  /// Toggle between markets
  void toggleMarket() {
    _currentMarket = _currentMarket == StockMarket.taiwan
        ? StockMarket.us
        : StockMarket.taiwan;
    notifyListeners();
  }

  /// Set market by code string
  void setMarketByCode(String code) {
    final market = code.toUpperCase() == 'US'
        ? StockMarket.us
        : StockMarket.taiwan;
    switchMarket(market);
  }
}
