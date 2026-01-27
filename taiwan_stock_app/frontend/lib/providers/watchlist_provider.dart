import 'package:flutter/foundation.dart';
import '../models/watchlist_item.dart';
import '../services/api_service.dart';
import '../widgets/common/sort_filter_bar.dart';

class WatchlistProvider with ChangeNotifier {
  final ApiService _apiService;
  List<WatchlistItem> _items = [];
  List<WatchlistItem> _sortedItems = [];
  bool _isLoading = false;
  String? _error;
  SortOption _currentSort = SortOption.addedRecent;
  Set<String> _industryFilter = {};
  String? _marketFilter;  // null means all, 'TW' or 'US'

  WatchlistProvider(this._apiService);

  List<WatchlistItem> get items => _sortedItems.isEmpty ? _items : _sortedItems;
  List<WatchlistItem> get allItems => _items;
  bool get isLoading => _isLoading;
  String? get error => _error;
  SortOption get currentSort => _currentSort;
  Set<String> get industryFilter => _industryFilter;
  String? get marketFilter => _marketFilter;

  /// 檢查股票是否已在自選股中
  bool isInWatchlist(String stockId) {
    return _items.any((item) => item.stockId == stockId);
  }

  // Get unique industries from watchlist
  Set<String> get availableIndustries {
    return _items
        .where((item) => item.industry != null && item.industry!.isNotEmpty)
        .map((item) => item.industry!)
        .toSet();
  }

  Future<void> loadWatchlist({String? market}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _items = await _apiService.getWatchlist(market: market ?? _marketFilter);
      _applySortAndFilter();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Set market filter and reload watchlist
  void setMarketFilter(String? market) {
    if (_marketFilter != market) {
      _marketFilter = market;
      loadWatchlist(market: market);
    }
  }

  Future<void> refresh() async {
    await loadWatchlist(market: _marketFilter);
  }

  Future<void> addStock(String stockId, {String? notes, String market = 'TW'}) async {
    try {
      await _apiService.addToWatchlist(stockId, notes: notes, market: market);
      await loadWatchlist(market: _marketFilter);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  Future<void> removeStock(String stockId) async {
    try {
      await _apiService.removeFromWatchlist(stockId);
      _items.removeWhere((item) => item.stockId == stockId);
      _applySortAndFilter();
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  void setSortOption(SortOption option) {
    _currentSort = option;
    _applySortAndFilter();
    notifyListeners();
  }

  void toggleIndustryFilter(String industry) {
    if (_industryFilter.contains(industry)) {
      _industryFilter.remove(industry);
    } else {
      _industryFilter.add(industry);
    }
    _applySortAndFilter();
    notifyListeners();
  }

  void clearFilters() {
    _industryFilter.clear();
    _applySortAndFilter();
    notifyListeners();
  }

  void _applySortAndFilter() {
    // Apply filter
    List<WatchlistItem> filtered = _items;
    if (_industryFilter.isNotEmpty) {
      filtered = _items.where((item) =>
        item.industry != null && _industryFilter.contains(item.industry)
      ).toList();
    }

    // Apply sort
    _sortedItems = List.from(filtered);
    switch (_currentSort) {
      case SortOption.nameAsc:
        _sortedItems.sort((a, b) => a.name.compareTo(b.name));
        break;
      case SortOption.nameDesc:
        _sortedItems.sort((a, b) => b.name.compareTo(a.name));
        break;
      case SortOption.priceHigh:
        _sortedItems.sort((a, b) =>
          (b.currentPrice ?? 0).compareTo(a.currentPrice ?? 0));
        break;
      case SortOption.priceLow:
        _sortedItems.sort((a, b) =>
          (a.currentPrice ?? 0).compareTo(b.currentPrice ?? 0));
        break;
      case SortOption.changeHigh:
        _sortedItems.sort((a, b) =>
          (b.changePercent ?? 0).compareTo(a.changePercent ?? 0));
        break;
      case SortOption.changeLow:
        _sortedItems.sort((a, b) =>
          (a.changePercent ?? 0).compareTo(b.changePercent ?? 0));
        break;
      case SortOption.volumeHigh:
        _sortedItems.sort((a, b) =>
          (b.volume ?? 0).compareTo(a.volume ?? 0));
        break;
      case SortOption.addedRecent:
        // Keep original order (assuming it's sorted by add date)
        break;
    }
  }
}
