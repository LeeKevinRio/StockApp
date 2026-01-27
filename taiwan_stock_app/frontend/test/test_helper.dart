import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:mocktail/mocktail.dart';

import 'package:taiwan_stock_app/services/api_service.dart';
import 'package:taiwan_stock_app/providers/auth_provider.dart';
import 'package:taiwan_stock_app/providers/watchlist_provider.dart';
import 'package:taiwan_stock_app/providers/ai_provider.dart';
import 'package:taiwan_stock_app/providers/app_state_provider.dart';
import 'package:taiwan_stock_app/providers/theme_provider.dart';
import 'package:taiwan_stock_app/services/auth_service.dart';

// Mock classes
class MockApiService extends Mock implements ApiService {}

class MockAuthService extends Mock implements AuthService {}

class MockAuthProvider extends Mock implements AuthProvider {}

class MockWatchlistProvider extends Mock implements WatchlistProvider {}

class MockAIProvider extends Mock implements AIProvider {}

class MockAppStateProvider extends Mock implements AppStateProvider {}

class MockThemeProvider extends Mock implements ThemeProvider {}

/// Creates a test widget wrapped with necessary providers
Widget createTestWidget({
  required Widget child,
  ApiService? apiService,
  AuthProvider? authProvider,
  WatchlistProvider? watchlistProvider,
  AIProvider? aiProvider,
  AppStateProvider? appStateProvider,
  ThemeProvider? themeProvider,
}) {
  return MultiProvider(
    providers: [
      if (apiService != null) Provider.value(value: apiService),
      if (authProvider != null)
        ChangeNotifierProvider.value(value: authProvider),
      if (watchlistProvider != null)
        ChangeNotifierProvider.value(value: watchlistProvider),
      if (aiProvider != null) ChangeNotifierProvider.value(value: aiProvider),
      if (appStateProvider != null)
        ChangeNotifierProvider.value(value: appStateProvider),
      if (themeProvider != null)
        ChangeNotifierProvider.value(value: themeProvider),
    ],
    child: MaterialApp(
      home: child,
    ),
  );
}

/// Creates a simple MaterialApp wrapper for widget testing
Widget wrapWithMaterialApp(Widget child) {
  return MaterialApp(
    home: Scaffold(body: child),
  );
}

/// Sample data factory functions for testing
class TestDataFactory {
  static Map<String, dynamic> createStockJson({
    String stockId = '2330',
    String name = '台積電',
    String market = 'TSE',
    String? industry = '半導體業',
  }) {
    return {
      'stock_id': stockId,
      'name': name,
      'market': market,
      'industry': industry,
    };
  }

  static Map<String, dynamic> createStockHistoryJson({
    String date = '2024-01-15',
    double open = 100.0,
    double high = 105.0,
    double low = 98.0,
    double close = 103.0,
    int volume = 10000,
  }) {
    return {
      'date': date,
      'open': open,
      'high': high,
      'low': low,
      'close': close,
      'volume': volume,
    };
  }

  static Map<String, dynamic> createWatchlistItemJson({
    String stockId = '2330',
    String name = '台積電',
    String? market,
    String? industry = '半導體業',
    double? currentPrice,
    double? change,
    double? changePercent,
    int? volume,
    String? notes,
  }) {
    return {
      'stock_id': stockId,
      'name': name,
      'market': market,
      'industry': industry,
      'current_price': currentPrice,
      'change': change,
      'change_percent': changePercent,
      'volume': volume,
      'notes': notes,
    };
  }

  static List<Map<String, dynamic>> createSampleStockList() {
    return [
      createStockJson(stockId: '2330', name: '台積電'),
      createStockJson(stockId: '2317', name: '鴻海', industry: '其他電子業'),
      createStockJson(stockId: '2454', name: '聯發科'),
    ];
  }

  static List<Map<String, dynamic>> createSampleHistoryList({int days = 30}) {
    final List<Map<String, dynamic>> history = [];
    final startDate = DateTime(2024, 1, 1);
    double basePrice = 100.0;

    for (int i = 0; i < days; i++) {
      final date = startDate.add(Duration(days: i));
      final change = (i % 3 == 0 ? 1 : -0.5) * (i % 5 + 1);
      basePrice += change;

      history.add(createStockHistoryJson(
        date: '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}',
        open: basePrice - 1,
        high: basePrice + 2,
        low: basePrice - 2,
        close: basePrice,
        volume: 10000 + i * 100,
      ));
    }

    return history;
  }
}
