/// 新聞資料模型

class StockNews {
  final String? id;
  final String? stockId;
  final String title;
  final String? content;
  final String? summary;
  final String? source;
  final String? sourceUrl;
  final String? sentiment;
  final double? sentimentScore;
  final DateTime? publishedAt;
  final DateTime? fetchedAt;

  StockNews({
    this.id,
    this.stockId,
    required this.title,
    this.content,
    this.summary,
    this.source,
    this.sourceUrl,
    this.sentiment,
    this.sentimentScore,
    this.publishedAt,
    this.fetchedAt,
  });

  factory StockNews.fromJson(Map<String, dynamic> json) {
    return StockNews(
      id: json['id']?.toString(),
      stockId: json['stock_id'],
      title: json['title'] ?? '',
      content: json['content'],
      summary: json['summary'],
      source: json['source'],
      sourceUrl: json['source_url'],
      sentiment: json['sentiment'],
      sentimentScore: json['sentiment_score'] != null
          ? double.tryParse(json['sentiment_score'].toString())
          : null,
      publishedAt: json['published_at'] != null
          ? DateTime.tryParse(json['published_at'])
          : null,
      fetchedAt: json['fetched_at'] != null
          ? DateTime.tryParse(json['fetched_at'])
          : null,
    );
  }

  String get sentimentText {
    switch (sentiment) {
      case 'positive':
        return '正面';
      case 'negative':
        return '負面';
      case 'neutral':
        return '中性';
      default:
        return '未分析';
    }
  }

  String get timeAgo {
    if (publishedAt == null) return '';

    final now = DateTime.now();
    final diff = now.difference(publishedAt!);

    if (diff.inMinutes < 60) {
      return '${diff.inMinutes} 分鐘前';
    } else if (diff.inHours < 24) {
      return '${diff.inHours} 小時前';
    } else if (diff.inDays < 7) {
      return '${diff.inDays} 天前';
    } else {
      return '${publishedAt!.month}/${publishedAt!.day}';
    }
  }
}

class NewsListResponse {
  final String? stockId;
  final int total;
  final List<StockNews> news;

  NewsListResponse({
    this.stockId,
    required this.total,
    required this.news,
  });

  factory NewsListResponse.fromJson(Map<String, dynamic> json) {
    return NewsListResponse(
      stockId: json['stock_id'],
      total: json['total'] ?? 0,
      news: (json['news'] as List?)
              ?.map((e) => StockNews.fromJson(e))
              .toList() ??
          [],
    );
  }
}
