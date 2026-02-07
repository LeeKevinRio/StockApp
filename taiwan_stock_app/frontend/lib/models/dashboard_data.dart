/// Dashboard 儀表板數據模型

/// 市場概況數據
class MarketOverview {
  final double indexValue;        // 指數值
  final double indexChange;       // 漲跌點數
  final double changePercent;     // 漲跌幅百分比
  final int totalVolume;          // 總成交量（億）
  final int upCount;              // 上漲家數
  final int downCount;            // 下跌家數
  final int flatCount;            // 平盤家數
  final String indexName;         // 指數名稱
  final DateTime updateTime;      // 更新時間

  MarketOverview({
    required this.indexValue,
    required this.indexChange,
    required this.changePercent,
    required this.totalVolume,
    required this.upCount,
    required this.downCount,
    required this.flatCount,
    required this.indexName,
    required this.updateTime,
  });

  bool get isUp => indexChange > 0;
  bool get isDown => indexChange < 0;

  factory MarketOverview.fromJson(Map<String, dynamic> json) {
    return MarketOverview(
      indexValue: (json['index_value'] as num?)?.toDouble() ?? 0,
      indexChange: (json['index_change'] as num?)?.toDouble() ?? 0,
      changePercent: (json['change_percent'] as num?)?.toDouble() ?? 0,
      totalVolume: json['total_volume'] as int? ?? 0,
      upCount: json['up_count'] as int? ?? 0,
      downCount: json['down_count'] as int? ?? 0,
      flatCount: json['flat_count'] as int? ?? 0,
      indexName: json['index_name'] as String? ?? '',
      updateTime: json['update_time'] != null
          ? DateTime.parse(json['update_time'] as String)
          : DateTime.now(),
    );
  }

  /// 創建台股預設市場概況
  factory MarketOverview.taiwanDefault() {
    return MarketOverview(
      indexValue: 0,
      indexChange: 0,
      changePercent: 0,
      totalVolume: 0,
      upCount: 0,
      downCount: 0,
      flatCount: 0,
      indexName: '加權指數',
      updateTime: DateTime.now(),
    );
  }

  /// 創建美股預設市場概況
  factory MarketOverview.usDefault() {
    return MarketOverview(
      indexValue: 0,
      indexChange: 0,
      changePercent: 0,
      totalVolume: 0,
      upCount: 0,
      downCount: 0,
      flatCount: 0,
      indexName: 'S&P 500',
      updateTime: DateTime.now(),
    );
  }
}

/// 自選股漲跌排行項
class TopMover {
  final String stockId;
  final String name;
  final double price;
  final double changePercent;
  final String market;

  TopMover({
    required this.stockId,
    required this.name,
    required this.price,
    required this.changePercent,
    this.market = 'TW',
  });

  bool get isUp => changePercent > 0;
  bool get isDown => changePercent < 0;

  factory TopMover.fromJson(Map<String, dynamic> json) {
    return TopMover(
      stockId: json['stock_id'] as String,
      name: json['name'] as String,
      price: (json['price'] as num?)?.toDouble() ?? 0,
      changePercent: (json['change_percent'] as num?)?.toDouble() ?? 0,
      market: json['market'] as String? ?? 'TW',
    );
  }
}

/// 自選股摘要
class WatchlistSummary {
  final int totalStocks;          // 自選股總數
  final int upCount;              // 上漲數
  final int downCount;            // 下跌數
  final int flatCount;            // 平盤數
  final int alertTriggered;       // 已觸發警報數
  final List<TopMover> topGainers; // 漲幅前3
  final List<TopMover> topLosers;  // 跌幅前3

  WatchlistSummary({
    required this.totalStocks,
    required this.upCount,
    required this.downCount,
    required this.flatCount,
    required this.alertTriggered,
    required this.topGainers,
    required this.topLosers,
  });

  factory WatchlistSummary.fromJson(Map<String, dynamic> json) {
    return WatchlistSummary(
      totalStocks: json['total'] as int? ?? 0,
      upCount: json['up_count'] as int? ?? 0,
      downCount: json['down_count'] as int? ?? 0,
      flatCount: json['flat_count'] as int? ?? 0,
      alertTriggered: json['alerts_triggered'] as int? ?? 0,
      topGainers: (json['top_gainers'] as List<dynamic>?)
          ?.map((e) => TopMover.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      topLosers: (json['top_losers'] as List<dynamic>?)
          ?.map((e) => TopMover.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
    );
  }

  factory WatchlistSummary.empty() {
    return WatchlistSummary(
      totalStocks: 0,
      upCount: 0,
      downCount: 0,
      flatCount: 0,
      alertTriggered: 0,
      topGainers: [],
      topLosers: [],
    );
  }
}

/// AI 精選推薦
class AIPick {
  final String stockId;
  final String name;
  final String suggestion;        // BUY/SELL/HOLD
  final double confidence;
  final String shortReason;       // 簡短理由
  final double? targetPrice;
  final double? currentPrice;
  final String market;

  AIPick({
    required this.stockId,
    required this.name,
    required this.suggestion,
    required this.confidence,
    required this.shortReason,
    this.targetPrice,
    this.currentPrice,
    this.market = 'TW',
  });

  bool get isBuy => suggestion.toUpperCase() == 'BUY';
  bool get isSell => suggestion.toUpperCase() == 'SELL';
  bool get isHold => suggestion.toUpperCase() == 'HOLD';

  String get suggestionText {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return '建議買入';
      case 'SELL':
        return '建議賣出';
      case 'HOLD':
        return '建議持有';
      default:
        return suggestion;
    }
  }

  factory AIPick.fromJson(Map<String, dynamic> json) {
    return AIPick(
      stockId: json['stock_id'] as String,
      name: json['name'] as String? ?? '',
      suggestion: json['suggestion'] as String,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
      shortReason: json['short_reason'] as String? ?? '',
      targetPrice: (json['target_price'] as num?)?.toDouble(),
      currentPrice: (json['current_price'] as num?)?.toDouble(),
      market: json['market'] as String? ?? 'TW',
    );
  }
}

/// 簡要新聞項
class NewsItem {
  final String id;
  final String title;
  final String source;
  final DateTime publishTime;
  final String? imageUrl;
  final String? url;

  NewsItem({
    required this.id,
    required this.title,
    required this.source,
    required this.publishTime,
    this.imageUrl,
    this.url,
  });

  factory NewsItem.fromJson(Map<String, dynamic> json) {
    return NewsItem(
      id: json['id'] as String? ?? '',
      title: json['title'] as String,
      source: json['source'] as String? ?? '',
      publishTime: json['publish_time'] != null
          ? DateTime.parse(json['publish_time'] as String)
          : DateTime.now(),
      imageUrl: json['image_url'] as String?,
      url: json['url'] as String?,
    );
  }
}

/// 警報摘要
class AlertSummary {
  final int activeCount;          // 啟用中警報數
  final int triggeredToday;       // 今日觸發數

  AlertSummary({
    required this.activeCount,
    required this.triggeredToday,
  });

  factory AlertSummary.fromJson(Map<String, dynamic> json) {
    return AlertSummary(
      activeCount: json['active'] as int? ?? 0,
      triggeredToday: json['triggered_today'] as int? ?? 0,
    );
  }

  factory AlertSummary.empty() {
    return AlertSummary(activeCount: 0, triggeredToday: 0);
  }
}

/// 完整 Dashboard 數據
class DashboardData {
  final MarketOverview marketOverview;
  final WatchlistSummary watchlistSummary;
  final List<AIPick> aiPicks;
  final List<NewsItem> latestNews;
  final AlertSummary alertSummary;

  DashboardData({
    required this.marketOverview,
    required this.watchlistSummary,
    required this.aiPicks,
    required this.latestNews,
    required this.alertSummary,
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      marketOverview: MarketOverview.fromJson(
        json['market'] as Map<String, dynamic>? ?? {},
      ),
      watchlistSummary: WatchlistSummary.fromJson(
        json['watchlist_summary'] as Map<String, dynamic>? ?? {},
      ),
      aiPicks: (json['ai_picks'] as List<dynamic>?)
          ?.map((e) => AIPick.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      latestNews: (json['latest_news'] as List<dynamic>?)
          ?.map((e) => NewsItem.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      alertSummary: AlertSummary.fromJson(
        json['alert_summary'] as Map<String, dynamic>? ?? {},
      ),
    );
  }

  factory DashboardData.empty({String market = 'TW'}) {
    return DashboardData(
      marketOverview: market == 'TW'
          ? MarketOverview.taiwanDefault()
          : MarketOverview.usDefault(),
      watchlistSummary: WatchlistSummary.empty(),
      aiPicks: [],
      latestNews: [],
      alertSummary: AlertSummary.empty(),
    );
  }
}
