/// 社群情緒分析模型

class SocialPost {
  final String? id;
  final String platform;
  final String? board;
  final String title;
  final String? content;
  final String? author;
  final String? url;
  final List<String>? mentionedStocks;
  final String? sentiment;
  final double? sentimentScore;
  final int pushCount;
  final int booCount;
  final int commentCount;
  final DateTime? postedAt;

  SocialPost({
    this.id,
    required this.platform,
    this.board,
    required this.title,
    this.content,
    this.author,
    this.url,
    this.mentionedStocks,
    this.sentiment,
    this.sentimentScore,
    this.pushCount = 0,
    this.booCount = 0,
    this.commentCount = 0,
    this.postedAt,
  });

  factory SocialPost.fromJson(Map<String, dynamic> json) {
    return SocialPost(
      id: json['id']?.toString(),
      platform: json['platform'] ?? 'unknown',
      board: json['board'],
      title: json['title'] ?? '',
      content: json['content'],
      author: json['author'],
      url: json['url'],
      mentionedStocks: json['mentioned_stocks'] != null
          ? List<String>.from(json['mentioned_stocks'])
          : null,
      sentiment: json['sentiment'],
      sentimentScore: json['sentiment_score'] != null
          ? double.tryParse(json['sentiment_score'].toString())
          : null,
      pushCount: json['push_count'] ?? 0,
      booCount: json['boo_count'] ?? 0,
      commentCount: json['comment_count'] ?? 0,
      postedAt: json['posted_at'] != null
          ? DateTime.tryParse(json['posted_at'].toString())
          : null,
    );
  }

  String get sentimentText {
    switch (sentiment) {
      case 'positive':
        return '看多';
      case 'negative':
        return '看空';
      case 'neutral':
        return '中性';
      default:
        return '未分析';
    }
  }

  String get timeAgo {
    if (postedAt == null) return '';

    final now = DateTime.now();
    final diff = now.difference(postedAt!);

    if (diff.inMinutes < 60) {
      return '${diff.inMinutes} 分鐘前';
    } else if (diff.inHours < 24) {
      return '${diff.inHours} 小時前';
    } else if (diff.inDays < 7) {
      return '${diff.inDays} 天前';
    } else {
      return '${postedAt!.month}/${postedAt!.day}';
    }
  }
}

class SentimentSummary {
  final int positive;
  final int negative;
  final int neutral;
  final double score;
  final String overall;

  SentimentSummary({
    required this.positive,
    required this.negative,
    required this.neutral,
    required this.score,
    required this.overall,
  });

  factory SentimentSummary.fromJson(Map<String, dynamic> json) {
    return SentimentSummary(
      positive: json['positive'] ?? 0,
      negative: json['negative'] ?? 0,
      neutral: json['neutral'] ?? 0,
      score: (json['score'] ?? 0).toDouble(),
      overall: json['overall'] ?? 'neutral',
    );
  }

  int get total => positive + negative + neutral;

  double get positiveRatio => total > 0 ? positive / total : 0;
  double get negativeRatio => total > 0 ? negative / total : 0;
}

class StockSentimentResponse {
  final String stockId;
  final int totalMentions;
  final SentimentSummary sentimentSummary;
  final List<SocialPost> recentPosts;

  StockSentimentResponse({
    required this.stockId,
    required this.totalMentions,
    required this.sentimentSummary,
    required this.recentPosts,
  });

  factory StockSentimentResponse.fromJson(Map<String, dynamic> json) {
    return StockSentimentResponse(
      stockId: json['stock_id'] ?? '',
      totalMentions: json['total_mentions'] ?? 0,
      sentimentSummary:
          SentimentSummary.fromJson(json['sentiment_summary'] ?? {}),
      recentPosts: (json['recent_posts'] as List?)
              ?.map((e) => SocialPost.fromJson(e))
              .toList() ??
          [],
    );
  }
}

class HotStock {
  final String stockId;
  final String? stockName;
  final int mentionCount;
  final double? sentimentScore;
  final String sentiment;
  final List<SocialPost> samplePosts;

  HotStock({
    required this.stockId,
    this.stockName,
    required this.mentionCount,
    this.sentimentScore,
    required this.sentiment,
    required this.samplePosts,
  });

  factory HotStock.fromJson(Map<String, dynamic> json) {
    return HotStock(
      stockId: json['stock_id'] ?? '',
      stockName: json['stock_name'],
      mentionCount: json['mention_count'] ?? 0,
      sentimentScore: json['sentiment_score']?.toDouble(),
      sentiment: json['sentiment'] ?? 'neutral',
      samplePosts: (json['sample_posts'] as List?)
              ?.map((e) => SocialPost.fromJson(e))
              .toList() ??
          [],
    );
  }
}
