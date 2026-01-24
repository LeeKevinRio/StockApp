import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/social_sentiment.dart';

class SentimentView extends StatefulWidget {
  final String stockId;

  const SentimentView({super.key, required this.stockId});

  @override
  State<SentimentView> createState() => _SentimentViewState();
}

class _SentimentViewState extends State<SentimentView> {
  StockSentimentResponse? _data;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // 模擬數據 - 實際會從 API 獲取
      await Future.delayed(const Duration(milliseconds: 500));

      _data = StockSentimentResponse(
        stockId: widget.stockId,
        totalMentions: 15,
        sentimentSummary: SentimentSummary(
          positive: 8,
          negative: 4,
          neutral: 3,
          score: 0.25,
          overall: 'positive',
        ),
        recentPosts: [
          SocialPost(
            id: 1,
            platform: 'ptt',
            board: 'Stock',
            title: '[心得] ${widget.stockId} 技術面分析',
            author: 'user1',
            url: 'https://www.ptt.cc/bbs/Stock/index.html',
            sentiment: 'positive',
            pushCount: 25,
            postedAt: DateTime.now().subtract(const Duration(hours: 2)),
          ),
          SocialPost(
            id: 2,
            platform: 'ptt',
            board: 'Stock',
            title: '[請益] ${widget.stockId} 現在可以進場嗎？',
            author: 'user2',
            url: 'https://www.ptt.cc/bbs/Stock/index.html',
            sentiment: 'neutral',
            pushCount: 10,
            postedAt: DateTime.now().subtract(const Duration(hours: 5)),
          ),
          SocialPost(
            id: 3,
            platform: 'ptt',
            board: 'Stock',
            title: '[標的] ${widget.stockId} 突破壓力區',
            author: 'user3',
            url: 'https://www.ptt.cc/bbs/Stock/index.html',
            sentiment: 'positive',
            pushCount: 35,
            postedAt: DateTime.now().subtract(const Duration(days: 1)),
          ),
        ],
      );

      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('載入失敗: $_error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadData,
              child: const Text('重試'),
            ),
          ],
        ),
      );
    }

    if (_data == null) {
      return const Center(child: Text('無數據'));
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSentimentSummary(),
            const SizedBox(height: 24),
            _buildSentimentBar(),
            const SizedBox(height: 24),
            _buildRecentPosts(),
          ],
        ),
      ),
    );
  }

  Widget _buildSentimentSummary() {
    final summary = _data!.sentimentSummary;

    Color sentimentColor;
    IconData sentimentIcon;
    String sentimentText;

    switch (summary.overall) {
      case 'positive':
        sentimentColor = Colors.green;
        sentimentIcon = Icons.trending_up;
        sentimentText = '看多氣氛濃厚';
        break;
      case 'negative':
        sentimentColor = Colors.red;
        sentimentIcon = Icons.trending_down;
        sentimentText = '看空氣氛濃厚';
        break;
      default:
        sentimentColor = Colors.grey;
        sentimentIcon = Icons.trending_flat;
        sentimentText = '多空分歧';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(sentimentIcon, size: 48, color: sentimentColor),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '社群情緒',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                    Text(
                      sentimentText,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: sentimentColor,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatItem('討論數', _data!.totalMentions.toString(), Colors.blue),
                _buildStatItem('看多', summary.positive.toString(), Colors.green),
                _buildStatItem('看空', summary.negative.toString(), Colors.red),
                _buildStatItem('中性', summary.neutral.toString(), Colors.grey),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }

  Widget _buildSentimentBar() {
    final summary = _data!.sentimentSummary;
    final total = summary.total;

    if (total == 0) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '情緒分佈',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: Row(
            children: [
              Expanded(
                flex: (summary.positiveRatio * 100).round(),
                child: Container(height: 24, color: Colors.green),
              ),
              Expanded(
                flex: (summary.negativeRatio * 100).round(),
                child: Container(height: 24, color: Colors.red),
              ),
              Expanded(
                flex: ((1 - summary.positiveRatio - summary.negativeRatio) * 100).round(),
                child: Container(height: 24, color: Colors.grey.shade300),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '看多 ${(summary.positiveRatio * 100).toStringAsFixed(0)}%',
              style: const TextStyle(fontSize: 12, color: Colors.green),
            ),
            Text(
              '看空 ${(summary.negativeRatio * 100).toStringAsFixed(0)}%',
              style: const TextStyle(fontSize: 12, color: Colors.red),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildRecentPosts() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'PTT 近期討論',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Text(
              '來源: Stock 版',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ..._data!.recentPosts.map((post) => _buildPostCard(post)),
      ],
    );
  }

  Widget _buildPostCard(SocialPost post) {
    Color sentimentColor;
    switch (post.sentiment) {
      case 'positive':
        sentimentColor = Colors.green;
        break;
      case 'negative':
        sentimentColor = Colors.red;
        break;
      default:
        sentimentColor = Colors.grey;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () => _openPostUrl(post.url),
        borderRadius: BorderRadius.circular(8),
        child: ListTile(
          leading: CircleAvatar(
            backgroundColor: sentimentColor.withAlpha(51),
            child: Icon(
              post.sentiment == 'positive'
                  ? Icons.thumb_up
                  : (post.sentiment == 'negative' ? Icons.thumb_down : Icons.remove),
              color: sentimentColor,
              size: 20,
            ),
          ),
          title: Text(
            post.title,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 14),
          ),
          subtitle: Row(
            children: [
              Text(post.author ?? 'Anonymous'),
              const SizedBox(width: 8),
              Text('推 ${post.pushCount}'),
              const SizedBox(width: 8),
              Text(post.timeAgo),
            ],
          ),
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: sentimentColor.withAlpha(26),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  post.sentimentText,
                  style: TextStyle(fontSize: 12, color: sentimentColor),
                ),
              ),
              if (post.url != null && post.url!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(left: 8),
                  child: Icon(
                    Icons.open_in_new,
                    size: 16,
                    color: Colors.grey.shade400,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _openPostUrl(String? url) async {
    if (url == null || url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('此文章暫無連結')),
      );
      return;
    }

    final uri = Uri.parse(url);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('無法開啟連結: $url')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('開啟連結時發生錯誤: $e')),
        );
      }
    }
  }
}
