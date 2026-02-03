import 'package:flutter_test/flutter_test.dart';
import 'package:taiwan_stock_app/models/stock.dart';

void main() {
  group('Stock', () {
    test('fromJson creates Stock with all fields', () {
      final json = {
        'stock_id': '2330',
        'name': '台積電',
        'market': 'TSE',
        'industry': '半導體業',
      };

      final stock = Stock.fromJson(json);

      expect(stock.stockId, '2330');
      expect(stock.name, '台積電');
      expect(stock.market, 'TSE');
      expect(stock.industry, '半導體業');
    });

    test('fromJson handles null industry', () {
      final json = {
        'stock_id': '2330',
        'name': '台積電',
        'market': 'TSE',
        'industry': null,
      };

      final stock = Stock.fromJson(json);

      expect(stock.stockId, '2330');
      expect(stock.industry, isNull);
    });

    test('fromJson handles missing industry', () {
      final json = {
        'stock_id': '2330',
        'name': '台積電',
        'market': 'TSE',
      };

      final stock = Stock.fromJson(json);

      expect(stock.stockId, '2330');
      expect(stock.industry, isNull);
    });

    test('toJson converts Stock to JSON', () {
      final stock = Stock(
        stockId: '2330',
        name: '台積電',
        market: 'TSE',
        industry: '半導體業',
      );

      final json = stock.toJson();

      expect(json['stock_id'], '2330');
      expect(json['name'], '台積電');
      expect(json['market'], 'TSE');
      expect(json['industry'], '半導體業');
    });

    test('roundtrip serialization preserves data', () {
      final original = Stock(
        stockId: '2317',
        name: '鴻海',
        market: 'TSE',
        industry: '其他電子業',
      );

      final json = original.toJson();
      final restored = Stock.fromJson(json);

      expect(restored.stockId, original.stockId);
      expect(restored.name, original.name);
      expect(restored.market, original.market);
      expect(restored.industry, original.industry);
    });
  });

  group('StockPrice', () {
    test('fromJson creates StockPrice with all fields', () {
      final json = {
        'stock_id': '2330',
        'name': '台積電',
        'current_price': 580.0,
        'change': 15.0,
        'change_percent': 2.65,
        'open': 570.0,
        'high': 585.0,
        'low': 568.0,
        'volume': 25000000,
        'updated_at': '2024-01-15T10:00:00',
      };

      final price = StockPrice.fromJson(json);

      expect(price.stockId, '2330');
      expect(price.currentPrice, 580.0);
      expect(price.change, 15.0);
      expect(price.changePercent, 2.65);
      expect(price.volume, 25000000);
    });

    test('isUp returns correct value', () {
      final positivePrice = StockPrice(
        stockId: '2330',
        name: '台積電',
        currentPrice: 580.0,
        change: 15.0,
        changePercent: 2.65,
        open: 570.0,
        high: 585.0,
        low: 568.0,
        volume: 25000000,
        updatedAt: DateTime.now(),
      );

      final negativePrice = StockPrice(
        stockId: '2330',
        name: '台積電',
        currentPrice: 560.0,
        change: -15.0,
        changePercent: -2.65,
        open: 575.0,
        high: 578.0,
        low: 558.0,
        volume: 25000000,
        updatedAt: DateTime.now(),
      );

      expect(positivePrice.isUp, true);
      expect(negativePrice.isUp, false);
    });

    test('isDown returns correct value', () {
      final positivePrice = StockPrice(
        stockId: '2330',
        name: '台積電',
        currentPrice: 580.0,
        change: 15.0,
        changePercent: 2.65,
        open: 570.0,
        high: 585.0,
        low: 568.0,
        volume: 25000000,
        updatedAt: DateTime.now(),
      );

      final negativePrice = StockPrice(
        stockId: '2330',
        name: '台積電',
        currentPrice: 560.0,
        change: -15.0,
        changePercent: -2.65,
        open: 575.0,
        high: 578.0,
        low: 558.0,
        volume: 25000000,
        updatedAt: DateTime.now(),
      );

      expect(positivePrice.isDown, false);
      expect(negativePrice.isDown, true);
    });
  });
}
