import 'package:flutter/foundation.dart';
import '../models/watchlist_item.dart';
import '../services/api_service.dart';

class WatchlistProvider with ChangeNotifier {
  final ApiService _apiService;
  List<WatchlistItem> _items = [];
  bool _isLoading = false;
  String? _error;

  WatchlistProvider(this._apiService);

  List<WatchlistItem> get items => _items;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadWatchlist() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _items = await _apiService.getWatchlist();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refresh() async {
    await loadWatchlist();
  }

  Future<void> addStock(String stockId, {String? notes}) async {
    try {
      await _apiService.addToWatchlist(stockId, notes: notes);
      await loadWatchlist();
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
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }
}
