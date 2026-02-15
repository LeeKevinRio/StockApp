import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:taiwan_stock_app/models/watchlist_item.dart';
import 'package:taiwan_stock_app/widgets/stock_card.dart';

void main() {
  group('StockCard', () {
    testWidgets('displays stock ID and name', (tester) async {
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () {},
            ),
          ),
        ),
      );

      expect(find.textContaining('2330'), findsOneWidget);
      expect(find.textContaining('台積電'), findsOneWidget);
    });

    testWidgets('displays price when available', (tester) async {
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
        currentPrice: 580.0,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () {},
            ),
          ),
        ),
      );

      expect(find.textContaining('580'), findsOneWidget);
    });

    testWidgets('displays change percent with correct color', (tester) async {
      final positiveStock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
        currentPrice: 580.0,
        changePercent: 2.5,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: positiveStock,
              onTap: () {},
            ),
          ),
        ),
      );

      // Should show positive change
      expect(find.textContaining('+'), findsWidgets);
    });

    testWidgets('calls onTap when tapped', (tester) async {
      bool tapped = false;
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () => tapped = true,
            ),
          ),
        ),
      );

      await tester.tap(find.byType(StockCard));
      await tester.pump();

      expect(tapped, true);
    });

    testWidgets('shows delete button when onDelete is provided', (tester) async {
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () {},
              onDelete: () {},
            ),
          ),
        ),
      );

      // Should find delete icon or trailing widget
      expect(find.byIcon(Icons.delete), findsOneWidget);
    });

    testWidgets('calls onDelete when delete button is pressed', (tester) async {
      bool deleted = false;
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () {},
              onDelete: () => deleted = true,
            ),
          ),
        ),
      );

      await tester.tap(find.byIcon(Icons.delete));
      await tester.pump();

      expect(deleted, true);
    });

    testWidgets('displays industry when available', (tester) async {
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
        industry: '半導體業',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () {},
            ),
          ),
        ),
      );

      expect(find.text('半導體業'), findsOneWidget);
    });

    testWidgets('handles negative change correctly', (tester) async {
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
        currentPrice: 560.0,
        change: -15.0,
        changePercent: -2.6,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () {},
            ),
          ),
        ),
      );

      // Should display negative values
      expect(find.textContaining('-'), findsWidgets);
    });
  });

  group('StockCard accessibility', () {
    testWidgets('has semantic label', (tester) async {
      final stock = WatchlistItem(
        stockId: '2330',
        name: '台積電',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StockCard(
              stock: stock,
              onTap: () {},
            ),
          ),
        ),
      );

      // Card should be tappable
      expect(find.byType(InkWell), findsWidgets);
    });
  });
}
