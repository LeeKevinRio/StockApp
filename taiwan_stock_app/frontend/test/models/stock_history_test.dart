import 'package:flutter_test/flutter_test.dart';
import 'package:taiwan_stock_app/models/stock_history.dart';

void main() {
  group('StockHistory', () {
    test('fromJson creates StockHistory with date string', () {
      final json = {
        'date': '2024-01-15',
        'open': 100.0,
        'high': 105.0,
        'low': 98.0,
        'close': 103.0,
        'volume': 10000,
      };

      final history = StockHistory.fromJson(json);

      expect(history.date.year, 2024);
      expect(history.date.month, 1);
      expect(history.date.day, 15);
      expect(history.open, 100.0);
      expect(history.high, 105.0);
      expect(history.low, 98.0);
      expect(history.close, 103.0);
      expect(history.volume, 10000);
    });

    test('fromJson handles integer volume', () {
      final json = {
        'date': '2024-01-15',
        'open': 100.0,
        'high': 105.0,
        'low': 98.0,
        'close': 103.0,
        'volume': 10000,
      };

      final history = StockHistory.fromJson(json);
      expect(history.volume, 10000);
    });

    test('fromJson handles double volume (converts to int)', () {
      final json = {
        'date': '2024-01-15',
        'open': 100.0,
        'high': 105.0,
        'low': 98.0,
        'close': 103.0,
        'volume': 10000.5,
      };

      final history = StockHistory.fromJson(json);
      expect(history.volume, 10000);
    });

    test('isRising returns true when close > open', () {
      final rising = StockHistory(
        date: DateTime(2024, 1, 15),
        open: 100.0,
        high: 105.0,
        low: 98.0,
        close: 103.0,
        volume: 10000,
      );

      expect(rising.isRising, true);
    });

    test('isRising returns false when close < open', () {
      final falling = StockHistory(
        date: DateTime(2024, 1, 15),
        open: 103.0,
        high: 105.0,
        low: 98.0,
        close: 100.0,
        volume: 10000,
      );

      expect(falling.isRising, false);
    });

    test('isRising returns true when close == open (flat)', () {
      final flat = StockHistory(
        date: DateTime(2024, 1, 15),
        open: 100.0,
        high: 105.0,
        low: 98.0,
        close: 100.0,
        volume: 10000,
      );

      expect(flat.isRising, true);
    });

    test('change calculates correctly', () {
      final history = StockHistory(
        date: DateTime(2024, 1, 15),
        open: 100.0,
        high: 105.0,
        low: 98.0,
        close: 103.0,
        volume: 10000,
      );

      expect(history.change, 3.0);
    });

    test('changePercent calculates correctly', () {
      final history = StockHistory(
        date: DateTime(2024, 1, 15),
        open: 100.0,
        high: 105.0,
        low: 98.0,
        close: 103.0,
        volume: 10000,
      );

      expect(history.changePercent, 3.0);
    });

    test('toJson converts StockHistory to JSON', () {
      final history = StockHistory(
        date: DateTime(2024, 1, 15),
        open: 100.0,
        high: 105.0,
        low: 98.0,
        close: 103.0,
        volume: 10000,
      );

      final json = history.toJson();

      expect(json['date'], '2024-01-15');
      expect(json['open'], 100.0);
      expect(json['high'], 105.0);
      expect(json['low'], 98.0);
      expect(json['close'], 103.0);
      expect(json['volume'], 10000);
    });

    test('roundtrip serialization preserves data', () {
      final original = StockHistory(
        date: DateTime(2024, 3, 20),
        open: 150.5,
        high: 160.25,
        low: 145.75,
        close: 158.0,
        volume: 50000,
      );

      final json = original.toJson();
      final restored = StockHistory.fromJson(json);

      expect(restored.date, original.date);
      expect(restored.open, original.open);
      expect(restored.high, original.high);
      expect(restored.low, original.low);
      expect(restored.close, original.close);
      expect(restored.volume, original.volume);
    });
  });

  group('StockHistory list operations', () {
    test('can sort by date', () {
      final histories = [
        StockHistory(date: DateTime(2024, 1, 15), open: 100, high: 105, low: 98, close: 103, volume: 10000),
        StockHistory(date: DateTime(2024, 1, 10), open: 95, high: 100, low: 93, close: 98, volume: 8000),
        StockHistory(date: DateTime(2024, 1, 20), open: 103, high: 108, low: 101, close: 106, volume: 12000),
      ];

      histories.sort((a, b) => a.date.compareTo(b.date));

      expect(histories[0].date.day, 10);
      expect(histories[1].date.day, 15);
      expect(histories[2].date.day, 20);
    });

    test('can calculate average close price', () {
      final histories = [
        StockHistory(date: DateTime(2024, 1, 15), open: 100, high: 105, low: 98, close: 100, volume: 10000),
        StockHistory(date: DateTime(2024, 1, 16), open: 100, high: 105, low: 98, close: 110, volume: 10000),
        StockHistory(date: DateTime(2024, 1, 17), open: 100, high: 105, low: 98, close: 90, volume: 10000),
      ];

      final avgClose = histories.map((h) => h.close).reduce((a, b) => a + b) / histories.length;

      expect(avgClose, 100.0);
    });
  });
}
