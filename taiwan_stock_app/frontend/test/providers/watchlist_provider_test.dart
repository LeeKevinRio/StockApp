import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:taiwan_stock_app/providers/watchlist_provider.dart';
import 'package:taiwan_stock_app/services/api_service.dart';
import 'package:taiwan_stock_app/models/watchlist_item.dart';
import 'package:taiwan_stock_app/widgets/common/sort_filter_bar.dart';

class MockApiService extends Mock implements ApiService {}

void main() {
  late MockApiService mockApiService;
  late WatchlistProvider provider;

  setUp(() {
    mockApiService = MockApiService();
    provider = WatchlistProvider(mockApiService);
  });

  group('WatchlistProvider', () {
    group('Initial State', () {
      test('starts with empty items', () {
        expect(provider.items, isEmpty);
      });

      test('starts with isLoading false', () {
        expect(provider.isLoading, false);
      });

      test('starts with no error', () {
        expect(provider.error, isNull);
      });

      test('starts with default sort option', () {
        expect(provider.currentSort, SortOption.addedRecent);
      });
    });

    group('loadWatchlist', () {
      test('sets loading state while fetching', () async {
        when(() => mockApiService.getWatchlist()).thenAnswer(
          (_) async {
            await Future.delayed(const Duration(milliseconds: 100));
            return [];
          },
        );

        final loadFuture = provider.loadWatchlist();

        expect(provider.isLoading, true);

        await loadFuture;

        expect(provider.isLoading, false);
      });

      test('loads items successfully', () async {
        final mockItems = [
          WatchlistItem(
            stockId: '2330',
            name: '台積電',
          ),
          WatchlistItem(
            stockId: '2317',
            name: '鴻海',
          ),
        ];

        when(() => mockApiService.getWatchlist()).thenAnswer((_) async => mockItems);

        await provider.loadWatchlist();

        expect(provider.items.length, 2);
        expect(provider.items[0].stockId, '2330');
        expect(provider.error, isNull);
      });

      test('handles error during load', () async {
        when(() => mockApiService.getWatchlist()).thenThrow(Exception('Network error'));

        await provider.loadWatchlist();

        expect(provider.error, contains('Network error'));
        expect(provider.isLoading, false);
      });
    });

    group('addStock', () {
      test('calls API and reloads watchlist', () async {
        when(() => mockApiService.addToWatchlist('2330', notes: null))
            .thenAnswer((_) async {});
        when(() => mockApiService.getWatchlist()).thenAnswer((_) async => [
              WatchlistItem(stockId: '2330', name: '台積電'),
            ]);

        await provider.addStock('2330');

        verify(() => mockApiService.addToWatchlist('2330', notes: null)).called(1);
        verify(() => mockApiService.getWatchlist()).called(1);
      });

      test('passes notes to API', () async {
        when(() => mockApiService.addToWatchlist('2330', notes: 'Test note'))
            .thenAnswer((_) async {});
        when(() => mockApiService.getWatchlist()).thenAnswer((_) async => []);

        await provider.addStock('2330', notes: 'Test note');

        verify(() => mockApiService.addToWatchlist('2330', notes: 'Test note')).called(1);
      });
    });

    group('removeStock', () {
      test('removes stock from local list immediately', () async {
        // Setup initial state
        when(() => mockApiService.getWatchlist()).thenAnswer((_) async => [
              WatchlistItem(stockId: '2330', name: '台積電'),
              WatchlistItem(stockId: '2317', name: '鴻海'),
            ]);
        await provider.loadWatchlist();

        when(() => mockApiService.removeFromWatchlist('2330'))
            .thenAnswer((_) async {});

        await provider.removeStock('2330');

        expect(provider.items.any((item) => item.stockId == '2330'), false);
        expect(provider.items.length, 1);
      });
    });

    group('Sorting', () {
      setUp(() async {
        final mockItems = [
          WatchlistItem(
            stockId: '2330',
            name: '台積電',
            currentPrice: 500.0,
            changePercent: 2.5,
          ),
          WatchlistItem(
            stockId: '2317',
            name: '鴻海',
            currentPrice: 100.0,
            changePercent: -1.0,
          ),
          WatchlistItem(
            stockId: '2454',
            name: '聯發科',
            currentPrice: 800.0,
            changePercent: 5.0,
          ),
        ];

        when(() => mockApiService.getWatchlist()).thenAnswer((_) async => mockItems);
        await provider.loadWatchlist();
      });

      test('sorts by name ascending', () {
        provider.setSortOption(SortOption.nameAsc);

        expect(provider.items[0].name, '台積電');
        expect(provider.items[1].name, '聯發科');
        expect(provider.items[2].name, '鴻海');
      });

      test('sorts by price high to low', () {
        provider.setSortOption(SortOption.priceHigh);

        expect(provider.items[0].stockId, '2454'); // 800
        expect(provider.items[1].stockId, '2330'); // 500
        expect(provider.items[2].stockId, '2317'); // 100
      });

      test('sorts by change percent high to low', () {
        provider.setSortOption(SortOption.changeHigh);

        expect(provider.items[0].stockId, '2454'); // 5%
        expect(provider.items[1].stockId, '2330'); // 2.5%
        expect(provider.items[2].stockId, '2317'); // -1%
      });
    });

    group('Filtering', () {
      setUp(() async {
        final mockItems = [
          WatchlistItem(
            stockId: '2330',
            name: '台積電',
            industry: '半導體業',
          ),
          WatchlistItem(
            stockId: '2317',
            name: '鴻海',
            industry: '其他電子業',
          ),
          WatchlistItem(
            stockId: '2454',
            name: '聯發科',
            industry: '半導體業',
          ),
        ];

        when(() => mockApiService.getWatchlist()).thenAnswer((_) async => mockItems);
        await provider.loadWatchlist();
      });

      test('gets available industries', () {
        expect(provider.availableIndustries.length, 2);
        expect(provider.availableIndustries.contains('半導體業'), true);
        expect(provider.availableIndustries.contains('其他電子業'), true);
      });

      test('filters by industry', () {
        provider.toggleIndustryFilter('半導體業');

        expect(provider.items.length, 2);
        expect(provider.items.every((item) => item.industry == '半導體業'), true);
      });

      test('clears filters', () {
        provider.toggleIndustryFilter('半導體業');
        expect(provider.items.length, 2);

        provider.clearFilters();
        expect(provider.items.length, 3);
      });
    });
  });
}
