import 'package:flutter/foundation.dart';
import '../models/dashboard_data.dart';
import '../models/watchlist_item.dart';
import '../models/ai_suggestion.dart';
import '../services/api_service.dart';

/// Dashboard 儀表板狀態管理 Provider
class DashboardProvider with ChangeNotifier {
  final ApiService _apiService;

  DashboardData? _dashboardData;
  bool _isLoading = false;
  String? _error;
  String _currentMarket = 'TW';
  DateTime? _lastRefresh;

  DashboardProvider(this._apiService);

  /// 獲取 Dashboard 數據
  DashboardData? get dashboardData => _dashboardData;

  /// 是否正在加載
  bool get isLoading => _isLoading;

  /// 錯誤信息
  String? get error => _error;

  /// 當前市場
  String get currentMarket => _currentMarket;

  /// 是否有數據
  bool get hasData => _dashboardData != null;

  /// 市場概況
  MarketOverview? get marketOverview => _dashboardData?.marketOverview;

  /// 自選股摘要
  WatchlistSummary? get watchlistSummary => _dashboardData?.watchlistSummary;

  /// AI 精選
  List<AIPick> get aiPicks => _dashboardData?.aiPicks ?? [];

  /// 最新新聞
  List<NewsItem> get latestNews => _dashboardData?.latestNews ?? [];

  /// 警報摘要
  AlertSummary? get alertSummary => _dashboardData?.alertSummary;

  /// 設置市場
  void setMarket(String market) {
    if (_currentMarket != market) {
      _currentMarket = market;
      loadDashboard(forceRefresh: true);
    }
  }

  /// 加載 Dashboard 數據
  Future<void> loadDashboard({bool forceRefresh = false}) async {
    // 檢查是否需要刷新（10秒內不重複加載）
    if (!forceRefresh && _lastRefresh != null) {
      final elapsed = DateTime.now().difference(_lastRefresh!);
      if (elapsed.inSeconds < 10 && _dashboardData != null) {
        return;
      }
    }

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // 並行加載各個數據源
      final results = await Future.wait([
        _loadMarketOverview(),
        _loadWatchlistSummary(),
        _loadAIPicks(),
        _loadLatestNews(),
        _loadAlertSummary(),
      ]);

      _dashboardData = DashboardData(
        marketOverview: results[0] as MarketOverview,
        watchlistSummary: results[1] as WatchlistSummary,
        aiPicks: results[2] as List<AIPick>,
        latestNews: results[3] as List<NewsItem>,
        alertSummary: results[4] as AlertSummary,
      );

      _lastRefresh = DateTime.now();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      // 如果出錯，使用空數據
      _dashboardData ??= DashboardData.empty(market: _currentMarket);
      notifyListeners();
      if (kDebugMode) {
        print('Dashboard load error: $e');
      }
    }
  }

  /// 刷新 Dashboard
  Future<void> refresh() async {
    await loadDashboard(forceRefresh: true);
  }

  /// 加載市場概況
  Future<MarketOverview> _loadMarketOverview() async {
    try {
      // 嘗試從 API 獲取市場概況
      // 暫時使用模擬數據
      if (_currentMarket == 'TW') {
        return MarketOverview(
          indexValue: 22856.78,
          indexChange: 156.32,
          changePercent: 0.69,
          totalVolume: 3245,
          upCount: 523,
          downCount: 412,
          flatCount: 156,
          indexName: '加權指數',
          updateTime: DateTime.now(),
        );
      } else {
        return MarketOverview(
          indexValue: 5234.56,
          indexChange: -23.45,
          changePercent: -0.45,
          totalVolume: 0,
          upCount: 245,
          downCount: 267,
          flatCount: 0,
          indexName: 'S&P 500',
          updateTime: DateTime.now(),
        );
      }
    } catch (e) {
      return _currentMarket == 'TW'
          ? MarketOverview.taiwanDefault()
          : MarketOverview.usDefault();
    }
  }

  /// 加載自選股摘要
  Future<WatchlistSummary> _loadWatchlistSummary() async {
    try {
      final watchlist = await _apiService.getWatchlist(market: _currentMarket);

      int upCount = 0;
      int downCount = 0;
      int flatCount = 0;

      final sortedByGain = List<WatchlistItem>.from(watchlist)
        ..sort((a, b) => (b.changePercent ?? 0).compareTo(a.changePercent ?? 0));

      for (final item in watchlist) {
        final change = item.changePercent ?? 0;
        if (change > 0) {
          upCount++;
        } else if (change < 0) {
          downCount++;
        } else {
          flatCount++;
        }
      }

      final topGainers = sortedByGain.take(3).map((item) => TopMover(
        stockId: item.stockId,
        name: item.name,
        price: item.currentPrice ?? 0,
        changePercent: item.changePercent ?? 0,
        market: item.marketRegion,
      )).toList();

      final topLosers = sortedByGain.reversed.take(3).map((item) => TopMover(
        stockId: item.stockId,
        name: item.name,
        price: item.currentPrice ?? 0,
        changePercent: item.changePercent ?? 0,
        market: item.marketRegion,
      )).toList();

      return WatchlistSummary(
        totalStocks: watchlist.length,
        upCount: upCount,
        downCount: downCount,
        flatCount: flatCount,
        alertTriggered: 0, // TODO: 從警報 API 獲取
        topGainers: topGainers,
        topLosers: topLosers,
      );
    } catch (e) {
      if (kDebugMode) {
        print('Load watchlist summary error: $e');
      }
      return WatchlistSummary.empty();
    }
  }

  /// 加載 AI 精選
  Future<List<AIPick>> _loadAIPicks() async {
    try {
      // 先嘗試讀取快取
      var suggestions = await _apiService.getAISuggestions();

      // 如果沒有快取，觸發 AI 生成
      if (suggestions.isEmpty) {
        suggestions = await _apiService.getAISuggestions(generateMissing: true);
      }

      if (suggestions.isEmpty) {
        return [];
      }

      // 優先顯示 BUY 建議，如果沒有則顯示所有建議
      var picks = suggestions
          .where((s) => s.suggestion.toUpperCase() == 'BUY')
          .toList();

      // 如果沒有 BUY 建議，顯示信心度最高的建議
      if (picks.isEmpty) {
        picks = List.from(suggestions);
      }

      // 依照信心度排序
      picks.sort((a, b) => b.confidence.compareTo(a.confidence));

      return picks.take(3).map((s) => AIPick(
        stockId: s.stockId,
        name: s.name,
        suggestion: s.suggestion,
        confidence: s.confidence,
        shortReason: _generateShortReason(s),
        targetPrice: s.targetPrice,
        currentPrice: null,
        market: _currentMarket,
      )).toList();
    } catch (e) {
      if (kDebugMode) {
        print('Load AI picks error: $e');
      }
      return [];
    }
  }

  /// 生成簡短理由
  String _generateShortReason(AISuggestion suggestion) {
    if (suggestion.keyFactors.isNotEmpty) {
      return suggestion.keyFactors.first.factor;
    }
    if (suggestion.reasoning != null && suggestion.reasoning!.isNotEmpty) {
      final reason = suggestion.reasoning!;
      return reason.length > 30 ? '${reason.substring(0, 30)}...' : reason;
    }
    return '技術指標顯示買入訊號';
  }

  /// 加載最新新聞
  Future<List<NewsItem>> _loadLatestNews() async {
    try {
      final newsData = await _apiService.getMarketNews(market: _currentMarket);
      final newsList = newsData['news'] as List<dynamic>? ?? [];

      return newsList.take(5).map((n) {
        final newsMap = n as Map<String, dynamic>;
        return NewsItem(
          id: newsMap['id']?.toString() ?? '',
          title: newsMap['title'] as String? ?? '',
          source: newsMap['source'] as String? ?? '',
          publishTime: newsMap['published_at'] != null
              ? DateTime.parse(newsMap['published_at'] as String)
              : DateTime.now(),
          imageUrl: newsMap['image_url'] as String?,
          url: newsMap['url'] as String?,
        );
      }).toList();
    } catch (e) {
      if (kDebugMode) {
        print('Load news error: $e');
      }
      return [];
    }
  }

  /// 加載警報摘要
  Future<AlertSummary> _loadAlertSummary() async {
    try {
      final alerts = await _apiService.getAlerts();

      final activeCount = alerts.where((a) {
        return a.isActive && !a.isTriggered;
      }).length;

      final today = DateTime.now();
      final triggeredToday = alerts.where((a) {
        if (!a.isTriggered || a.triggeredAt == null) return false;
        final triggeredAt = a.triggeredAt!;
        return triggeredAt.year == today.year &&
            triggeredAt.month == today.month &&
            triggeredAt.day == today.day;
      }).length;

      return AlertSummary(
        activeCount: activeCount,
        triggeredToday: triggeredToday,
      );
    } catch (e) {
      if (kDebugMode) {
        print('Load alert summary error: $e');
      }
      return AlertSummary.empty();
    }
  }
}
