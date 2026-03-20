import 'package:flutter/foundation.dart';
import '../models/dashboard_data.dart';
import '../models/watchlist_item.dart';
import '../models/ai_suggestion.dart';
import '../widgets/dashboard/ai_discovery_card.dart';
import '../services/api_service.dart';

/// Dashboard 儀表板狀態管理 Provider
class DashboardProvider with ChangeNotifier {
  final ApiService _apiService;

  DashboardData? _dashboardData;
  bool _isLoading = false;
  bool _isLoadingAI = false;
  bool _isLoadingDiscovery = false;
  bool _hasScannedDiscovery = false;
  String? _error;
  String _currentMarket = 'TW';
  DateTime? _lastRefresh;

  // AI 潛力股掃描結果
  List<AIDiscoveryPick> _discoveryPicks = [];
  String _discoveryMarketSummary = '';

  DashboardProvider(this._apiService);

  /// 獲取 Dashboard 數據
  DashboardData? get dashboardData => _dashboardData;

  /// 是否正在加載
  bool get isLoading => _isLoading;

  /// AI 精選是否正在加載
  bool get isLoadingAI => _isLoadingAI;

  /// AI 潛力股是否正在加載
  bool get isLoadingDiscovery => _isLoadingDiscovery;

  /// 是否已掃描過
  bool get hasScannedDiscovery => _hasScannedDiscovery;

  /// AI 潛力股推薦
  List<AIDiscoveryPick> get discoveryPicks => _discoveryPicks;

  /// 市場掃描摘要
  String get discoveryMarketSummary => _discoveryMarketSummary;

  /// 錯誤信息
  String? get error => _error;

  /// 當前市場
  String get currentMarket => _currentMarket;

  /// 是否有數據
  bool get hasData => _dashboardData != null;

  /// 最後一次資料刷新時間
  DateTime? get lastRefreshTime => _lastRefresh;

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
      if (kDebugMode) {
        print('[Dashboard] Switching market: $_currentMarket → $market');
      }
      _currentMarket = market;
      // 保留舊數據顯示（避免白屏），標記載入中讓 UI 顯示進度指示
      _discoveryPicks = [];
      _discoveryMarketSummary = '';
      _hasScannedDiscovery = false;
      notifyListeners();
      loadDashboard(forceRefresh: true);
    }
  }

  /// 觸發 AI 潛力股掃描
  Future<void> scanDiscovery({bool refresh = false}) async {
    _isLoadingDiscovery = true;
    notifyListeners();

    try {
      final data = await _apiService.getAIDiscovery(
        market: _currentMarket,
        refresh: refresh,
        topN: 5,
      );
      _discoveryPicks = (data['picks'] as List<dynamic>?)
              ?.map((e) => AIDiscoveryPick.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [];
      _discoveryMarketSummary = data['market_summary'] as String? ?? '';
      _hasScannedDiscovery = true;
    } catch (e) {
      if (kDebugMode) {
        print('AI Discovery scan error: $e');
      }
      _discoveryMarketSummary = '掃描失敗，請稍後再試';
    } finally {
      _isLoadingDiscovery = false;
      notifyListeners();
    }
  }

  /// 快速載入已快取的潛力股（不觸發掃描）
  Future<void> _loadDiscoveryQuick() async {
    try {
      final data = await _apiService.getAIDiscoveryQuick(market: _currentMarket);
      final picks = (data['picks'] as List<dynamic>?)
              ?.map((e) => AIDiscoveryPick.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [];
      if (picks.isNotEmpty) {
        _discoveryPicks = picks;
        _discoveryMarketSummary = data['market_summary'] as String? ?? '';
        _hasScannedDiscovery = true;
        notifyListeners();
      }
    } catch (e) {
      if (kDebugMode) {
        print('AI Discovery quick load error: $e');
      }
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
      // 並行加載快速數據源（不含 AI 精選，避免阻塞整個 Dashboard）
      final results = await Future.wait([
        _loadMarketOverview(),
        _loadWatchlistSummary(),
        _loadLatestNews(),
        _loadAlertSummary(),
      ]);

      final watchlistSummary = results[1] as WatchlistSummary;
      final alertSummary = results[3] as AlertSummary;

      _dashboardData = DashboardData(
        marketOverview: results[0] as MarketOverview,
        watchlistSummary: WatchlistSummary(
          totalStocks: watchlistSummary.totalStocks,
          upCount: watchlistSummary.upCount,
          downCount: watchlistSummary.downCount,
          flatCount: watchlistSummary.flatCount,
          alertTriggered: alertSummary.triggeredToday,
          topGainers: watchlistSummary.topGainers,
          topLosers: watchlistSummary.topLosers,
        ),
        aiPicks: _dashboardData?.aiPicks ?? [],
        latestNews: results[2] as List<NewsItem>,
        alertSummary: alertSummary,
      );

      _lastRefresh = DateTime.now();
      _isLoading = false;
      notifyListeners();

      // AI 精選獨立異步加載（不阻塞 Dashboard 渲染）
      _loadAIPicksAsync();
      // 嘗試快速載入已快取的 AI 潛力股
      _loadDiscoveryQuick();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      _dashboardData ??= DashboardData.empty(market: _currentMarket);
      notifyListeners();
      if (kDebugMode) {
        print('Dashboard load error: $e');
      }
    }
  }

  /// 異步加載 AI 精選（不阻塞主 Dashboard）
  Future<void> _loadAIPicksAsync() async {
    _isLoadingAI = true;
    notifyListeners();

    try {
      final picks = await _loadAIPicks();
      if (_dashboardData != null) {
        _dashboardData = DashboardData(
          marketOverview: _dashboardData!.marketOverview,
          watchlistSummary: _dashboardData!.watchlistSummary,
          aiPicks: picks,
          latestNews: _dashboardData!.latestNews,
          alertSummary: _dashboardData!.alertSummary,
        );
      }
    } catch (e) {
      if (kDebugMode) {
        print('AI picks async load error: $e');
      }
    } finally {
      _isLoadingAI = false;
      notifyListeners();
    }
  }

  /// 刷新 Dashboard
  Future<void> refresh() async {
    await loadDashboard(forceRefresh: true);
  }

  /// 加載市場概況（從熱力圖 API 聚合真實數據）
  Future<MarketOverview> _loadMarketOverview() async {
    try {
      final heatmapData = await _apiService.getMarketHeatmap(market: _currentMarket);
      final sectors = heatmapData['sectors'] as List<dynamic>? ?? [];

      int upCount = 0;
      int downCount = 0;
      int flatCount = 0;
      double totalVolume = 0;
      double totalChange = 0;
      int stockCount = 0;

      for (final sector in sectors) {
        final sectorMap = sector as Map<String, dynamic>;
        final stocks = sectorMap['stocks'] as List<dynamic>? ?? [];
        for (final stock in stocks) {
          final s = stock as Map<String, dynamic>;
          final changePct = (s['change_percent'] as num?)?.toDouble() ?? 0;
          if (changePct > 0) {
            upCount++;
          } else if (changePct < 0) {
            downCount++;
          } else {
            flatCount++;
          }
          totalVolume += (s['volume'] as num?)?.toDouble() ?? 0;
          totalChange += changePct;
          stockCount++;
        }
      }

      final avgChange = stockCount > 0 ? totalChange / stockCount : 0.0;
      // 成交量轉為億元（張 × 1000 股 / 1億）
      final volumeInYi = (totalVolume * 1000 / 100000000).round();

      return MarketOverview(
        indexValue: 0,
        indexChange: 0,
        changePercent: avgChange,
        totalVolume: volumeInYi,
        upCount: upCount,
        downCount: downCount,
        flatCount: flatCount,
        indexName: _currentMarket == 'TW' ? '代表股概況' : 'US Market',
        updateTime: DateTime.now(),
      );
    } catch (e) {
      if (kDebugMode) {
        print('Load market overview error: $e');
      }
      return _currentMarket == 'TW'
          ? MarketOverview.taiwanDefault()
          : MarketOverview.usDefault();
    }
  }

  /// 加載自選股摘要
  Future<WatchlistSummary> _loadWatchlistSummary() async {
    try {
      if (kDebugMode) {
        print('[Dashboard] Loading watchlist summary for market: $_currentMarket');
      }
      final watchlist = await _apiService.getWatchlist(market: _currentMarket);

      if (kDebugMode) {
        print('[Dashboard] Watchlist returned ${watchlist.length} items for $_currentMarket');
      }

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

      // 只從有實際漲幅的項目中取 top gainers（排除 changePercent <= 0）
      final topGainers = sortedByGain
        .where((item) => (item.changePercent ?? 0) > 0)
        .take(3).map((item) => TopMover(
          stockId: item.stockId,
          name: item.name,
          price: item.currentPrice ?? 0,
          changePercent: item.changePercent ?? 0,
          market: item.marketRegion,
        )).toList();

      // 只從有實際跌幅的項目中取 top losers（排除 changePercent >= 0）
      final topLosers = sortedByGain.reversed
        .where((item) => (item.changePercent ?? 0) < 0)
        .take(3).map((item) => TopMover(
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
        alertTriggered: 0, // placeholder：由 loadDashboard() 用 alertSummary.triggeredToday 覆蓋
        topGainers: topGainers,
        topLosers: topLosers,
      );
    } catch (e) {
      if (kDebugMode) {
        print('[Dashboard] Load watchlist summary error for $_currentMarket: $e');
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
        currentPrice: s.currentPrice,
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
