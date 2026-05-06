import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/watchlist_provider.dart';
import '../providers/market_provider.dart';
import '../providers/locale_provider.dart';
import '../services/api_service.dart';
import '../models/stock.dart';
import '../utils/debouncer.dart';
import '../widgets/common/skeleton_loader.dart';
import '../widgets/common/error_view.dart';
import '../widgets/market_switcher.dart';

class StockSearchScreen extends StatefulWidget {
  const StockSearchScreen({super.key});

  @override
  State<StockSearchScreen> createState() => _StockSearchScreenState();
}

class _StockSearchScreenState extends State<StockSearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  final Debouncer _debouncer = Debouncer(delay: const Duration(milliseconds: 300));
  List<Stock> _searchResults = [];
  bool _isSearching = false;
  String? _error;
  String _lastQuery = '';
  String? _lastMarket;

  @override
  void dispose() {
    _searchController.dispose();
    _debouncer.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    setState(() {});

    if (query.trim().isEmpty) {
      _debouncer.cancel();
      setState(() {
        _searchResults = [];
        _error = null;
        _lastQuery = '';
      });
      return;
    }

    // Show loading immediately but debounce the actual search
    if (query != _lastQuery) {
      setState(() {
        _isSearching = true;
      });
    }

    _debouncer.run(() => _search(query));
  }

  Future<void> _search(String query) async {
    if (query.trim().isEmpty) {
      setState(() {
        _searchResults = [];
        _error = null;
        _isSearching = false;
      });
      return;
    }

    _lastQuery = query;

    try {
      final apiService = context.read<ApiService>();
      final marketProvider = context.read<MarketProvider>();
      final results = await apiService.searchStocks(query, market: marketProvider.marketCode);
      if (mounted && query == _searchController.text) {
        setState(() {
          _searchResults = results;
          _isSearching = false;
          _error = null;
        });
      }
    } catch (e) {
      if (mounted && query == _searchController.text) {
        setState(() {
          _error = e.toString();
          _isSearching = false;
        });
      }
    }
  }

  /// 切換市場時清空搜尋框、結果與錯誤狀態，避免上一個市場的內容殘留
  void _clearSearchOnMarketChange() {
    _debouncer.cancel();
    _searchController.clear();
    setState(() {
      _searchResults = [];
      _error = null;
      _isSearching = false;
      _lastQuery = '';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer2<MarketProvider, LocaleProvider>(
      builder: (context, marketProvider, locale, child) {
        // 偵測市場切換並清空輸入框/結果
        final currentMarket = marketProvider.marketCode;
        if (_lastMarket != null && _lastMarket != currentMarket) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (mounted) _clearSearchOnMarketChange();
          });
        }
        _lastMarket = currentMarket;

        final marketLabel = marketProvider.isUSMarket
            ? locale.tr('美股', 'US')
            : locale.tr('台股', 'TW');

        return Scaffold(
          appBar: AppBar(
            title: Text(locale.tr('搜尋$marketLabel', 'Search $marketLabel')),
            actions: [
              Padding(
                padding: const EdgeInsets.only(right: 8.0),
                child: CompactMarketSwitcher(
                  onMarketChanged: () {
                    // 切市場直接清空，不沿用上一市場的查詢字串
                    _clearSearchOnMarketChange();
                  },
                ),
              ),
            ],
          ),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: locale.tr(
                      marketProvider.isUSMarket
                          ? '輸入美股代碼（例如 AAPL）'
                          : '輸入股票代碼或名稱',
                      marketProvider.isUSMarket
                          ? 'Enter stock symbol (e.g., AAPL)'
                          : 'Enter stock ID or name',
                    ),
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchController.clear();
                              _onSearchChanged('');
                            },
                          )
                        : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  onChanged: _onSearchChanged,
                  textInputAction: TextInputAction.search,
                  onSubmitted: (value) {
                    _debouncer.cancel();
                    _search(value);
                  },
                ),
              ),
              // Recent searches hint
              if (_searchController.text.isEmpty)
                _buildRecentSearches(),
              Expanded(
                child: _buildBody(),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildRecentSearches() {
    final marketProvider = context.watch<MarketProvider>();
    final locale = context.watch<LocaleProvider>();

    // Popular/suggested stocks 是依市場決定（資料），與語系無關
    final suggestions = marketProvider.isUSMarket
        ? ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META']
        : ['2330', '2317', '2454', '2412', '2882'];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            locale.tr('熱門搜尋', 'Popular Stocks'),
            style: TextStyle(
              fontSize: 12,
              color: Theme.of(context).textTheme.bodySmall?.color,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: suggestions.map((code) {
              return ActionChip(
                label: Text(code),
                onPressed: () {
                  _searchController.text = code;
                  _onSearchChanged(code);
                },
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_isSearching) {
      return ListView.builder(
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: 5,
        itemBuilder: (context, index) => const SearchResultSkeleton(),
      );
    }

    final locale = context.watch<LocaleProvider>();

    if (_error != null) {
      return ErrorView(
        message: locale.tr('搜尋失敗', 'Search failed'),
        details: _error,
        onRetry: () => _search(_searchController.text),
      );
    }

    if (_searchController.text.isEmpty) {
      final marketProvider = context.watch<MarketProvider>();
      // 例子是市場決定的資料；外框文案是語系決定
      final example = marketProvider.isUSMarket ? 'AAPL、GOOGL' : '2330、台積電';
      final exampleEn = marketProvider.isUSMarket ? 'AAPL, GOOGL' : '2330, TSMC';
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search, size: 64, color: Theme.of(context).disabledColor),
            const SizedBox(height: 16),
            Text(locale.tr(
              '輸入股票代碼或名稱開始搜尋',
              'Enter stock symbol to search',
            )),
            const SizedBox(height: 8),
            Text(
              locale.tr('例如：$example', 'e.g., $exampleEn'),
              style: TextStyle(color: Theme.of(context).textTheme.bodySmall?.color),
            ),
          ],
        ),
      );
    }

    if (_searchResults.isEmpty) {
      return ErrorView.notFound(
        message: locale.tr(
          '找不到符合「${_searchController.text}」的股票',
          'No results for "${_searchController.text}"',
        ),
        onRetry: () => _search(_searchController.text),
      );
    }

    final marketProvider = context.watch<MarketProvider>();
    return ListView.builder(
      itemCount: _searchResults.length,
      itemBuilder: (context, index) {
        final stock = _searchResults[index];
        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: ListTile(
            onTap: () {
              Navigator.pushNamed(
                context,
                '/stock-detail',
                arguments: {
                  'stockId': stock.stockId,
                  'market': marketProvider.marketCode,
                },
              );
            },
            title: Text(
              '${stock.stockId} ${stock.name}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(stock.industry ?? stock.sector ?? ''),
            trailing: _AddToWatchlistButton(
              stockId: stock.stockId,
              market: marketProvider.marketCode,
            ),
          ),
        );
      },
    );
  }

}

class _AddToWatchlistButton extends StatefulWidget {
  final String stockId;
  final String market;

  const _AddToWatchlistButton({
    required this.stockId,
    required this.market,
  });

  @override
  State<_AddToWatchlistButton> createState() => _AddToWatchlistButtonState();
}

class _AddToWatchlistButtonState extends State<_AddToWatchlistButton> {
  bool _isAdding = false;

  Future<void> _addToWatchlist() async {
    if (_isAdding) return;

    setState(() => _isAdding = true);

    final locale = context.read<LocaleProvider>();
    try {
      await context.read<WatchlistProvider>().addStock(
        widget.stockId,
        market: widget.market,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(locale.tr('已加入自選股', 'Added to watchlist')),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(locale.tr('錯誤：$e', 'Error: $e')),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isAdding = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer2<WatchlistProvider, LocaleProvider>(
      builder: (context, watchlistProvider, locale, child) {
        final isInWatchlist = watchlistProvider.isInWatchlist(widget.stockId);

        if (isInWatchlist) {
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.green.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.green.withValues(alpha: 0.3)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.check_circle, size: 18, color: Colors.green),
                const SizedBox(width: 4),
                Text(
                  locale.tr('已加入', 'Added'),
                  style: const TextStyle(
                    color: Colors.green,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          );
        }

        return ElevatedButton.icon(
          icon: _isAdding
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.add, size: 18),
          label: Text(_isAdding
              ? locale.tr('加入中...', 'Adding...')
              : locale.tr('加入', 'Add')),
          onPressed: _isAdding ? null : _addToWatchlist,
        );
      },
    );
  }
}
