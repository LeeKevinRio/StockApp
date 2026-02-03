// Basic Flutter widget test for Taiwan Stock App

import 'package:flutter_test/flutter_test.dart';
import 'package:taiwan_stock_app/models/stock.dart';
import 'package:taiwan_stock_app/models/stock_history.dart';
import 'package:taiwan_stock_app/models/watchlist_item.dart';

void main() {
  group('App smoke tests', () {
    test('Stock model can be created', () {
      final stock = Stock(
        stockId: '2330',
        name: '台積電',
        market: 'TSE',
        industry: '半導體業',
      );

      expect(stock.stockId, '2330');
      expect(stock.name, '台積電');
    });

    test('StockHistory model can be created', () {
      final history = StockHistory(
        date: DateTime(2024, 1, 15),
        open: 100.0,
        high: 105.0,
        low: 98.0,
        close: 103.0,
        volume: 10000,
      );

      expect(history.open, 100.0);
      expect(history.close, 103.0);
      expect(history.isRising, true);
    });

    test('WatchlistItem model can be created', () {
      final item = WatchlistItem(
        stockId: '2330',
        name: '台積電',
        currentPrice: 580.0,
        changePercent: 2.5,
      );

      expect(item.stockId, '2330');
      expect(item.isUp, true);
    });
  });
}
