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

  /// 清除錯誤狀態
  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> loadWatchlist({String? market, bool silent = false}) async {
    if (!silent) {
      _isLoading = true;
      _error = null;
      notifyListeners();
    }

    try {
      _items = await _apiService.getWatchlist(market: market ?? _marketFilter);
      _applySortAndFilter();
      _error = null;  // 清除任何之前的錯誤
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
    // 即使市場相同也強制重新載入（解決首次載入問題）
    _marketFilter = market;
    // 清除舊資料，避免顯示混合結果
    _items = [];
    _sortedItems = [];
    notifyListeners();
    loadWatchlist(market: market);
  }

  Future<void> refresh() async {
    await loadWatchlist(market: _marketFilter);
  }

  Future<void> addStock(String stockId, {String? notes, String market = 'TW'}) async {
    // 先檢查是否已在自選股中
    if (isInWatchlist(stockId)) {
      throw Exception(market == 'US' ? 'Already in watchlist' : '此股票已在自選股中');
    }

    try {
      await _apiService.addToWatchlist(stockId, notes: notes, market: market);
      // 靜默刷新列表（不顯示 loading）
      await loadWatchlist(market: _marketFilter, silent: true);
    } catch (e) {
      // 不要設置全局 error，只拋出讓調用方處理
      rethrow;
    }
  }

  Future<void> removeStock(String stockId) async {
    // 樂觀更新：先從本地移除
    final removedItem = _items.firstWhere(
      (item) => item.stockId == stockId,
      orElse: () => throw Exception('Stock not found'),
    );
    _items.removeWhere((item) => item.stockId == stockId);
    _applySortAndFilter();
    notifyListeners();

    try {
      await _apiService.removeFromWatchlist(stockId);
    } catch (e) {
      // 如果刪除失敗，恢復本地狀態
      _items.add(removedItem);
      _applySortAndFilter();
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
