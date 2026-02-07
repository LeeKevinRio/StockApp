import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import '../models/social_sentiment.dart';
import '../services/api_service.dart';

class SentimentView extends StatefulWidget {
  final String stockId;
  final String market;

  const SentimentView({
    super.key,
    required this.stockId,
    this.market = 'TW',
  });

  @override
  State<SentimentView> createState() => _SentimentViewState();
}

class _SentimentViewState extends State<SentimentView> {
  StockSentimentResponse? _data;
  bool _isLoading = true;
  String? _error;

  bool get isTaiwan => widget.market == 'TW';

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void didUpdateWidget(covariant SentimentView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.stockId != widget.stockId || oldWidget.market != widget.market) {
      _loadData();
    }
  }

  Future<void> _loadData() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final sentimentData = await apiService.getStockSentiment(
        widget.stockId,
        market: widget.market,
      );

      if (!mounted) return;
      setState(() {
        _data = sentimentData;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(
              isTaiwan ? 'Loading PTT sentiment...' : 'Loading Reddit sentiment...',
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('Error: $_error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadData,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_data == null) {
      return const Center(child: Text('No data available'));
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Source Badge
            Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: isTaiwan ? Colors.red.withAlpha(26) : Colors.orange.withAlpha(26),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isTaiwan ? Icons.forum : Icons.reddit,
                      size: 16,
                      color: isTaiwan ? Colors.red : Colors.orange,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      isTaiwan ? 'Source: TW Social' : 'Source: Reddit',
                      style: TextStyle(
                        color: isTaiwan ? Colors.red : Colors.orange,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
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
        sentimentText = isTaiwan ? 'Bullish Sentiment' : 'Bullish Sentiment';
        break;
      case 'negative':
        sentimentColor = Colors.red;
        sentimentIcon = Icons.trending_down;
        sentimentText = isTaiwan ? 'Bearish Sentiment' : 'Bearish Sentiment';
        break;
      default:
        sentimentColor = Colors.grey;
        sentimentIcon = Icons.trending_flat;
        sentimentText = 'Mixed Sentiment';
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
                      'Social Sentiment',
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
                _buildStatItem('Mentions', _data!.totalMentions.toString(), isTaiwan ? Colors.blue : Colors.orange),
                _buildStatItem('Bullish', summary.positive.toString(), Colors.green),
                _buildStatItem('Bearish', summary.negative.toString(), Colors.red),
                _buildStatItem('Neutral', summary.neutral.toString(), Colors.grey),
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
          'Sentiment Distribution',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: Row(
            children: [
              Expanded(
                flex: (summary.positiveRatio * 100).round().clamp(1, 100),
                child: Container(height: 24, color: Colors.green),
              ),
              Expanded(
                flex: (summary.negativeRatio * 100).round().clamp(1, 100),
                child: Container(height: 24, color: Colors.red),
              ),
              Expanded(
                flex: ((1 - summary.positiveRatio - summary.negativeRatio) * 100).round().clamp(1, 100),
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
              'Bullish ${(summary.positiveRatio * 100).toStringAsFixed(0)}%',
              style: const TextStyle(fontSize: 12, color: Colors.green),
            ),
            Text(
              'Bearish ${(summary.negativeRatio * 100).toStringAsFixed(0)}%',
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
            Text(
              isTaiwan ? 'Social Discussions' : 'Reddit Discussions',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Text(
              isTaiwan ? 'PTT, Dcard, Mobile01' : 'r/wallstreetbets, r/stocks...',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (_data!.recentPosts.isEmpty)
          Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Icon(
                    isTaiwan ? Icons.forum : Icons.reddit,
                    size: 48,
                    color: Colors.grey.shade400,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'No recent discussions found',
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
          )
        else
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

    final sourceColor = isTaiwan ? Colors.red : Colors.orange;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () => _openPostUrl(post.url),
        borderRadius: BorderRadius.circular(8),
        child: ListTile(
          leading: CircleAvatar(
            backgroundColor: sourceColor.withAlpha(51),
            child: Icon(
              isTaiwan ? Icons.article : Icons.reddit,
              color: sourceColor,
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
              Text(
                post.board ?? (isTaiwan ? 'PTT' : 'Reddit'),
                style: TextStyle(
                  fontSize: 12,
                  color: sourceColor,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              if (isTaiwan) ...[
                if (post.pushCount > 0)
                  Text(
                    '+${post.pushCount}',
                    style: const TextStyle(fontSize: 12, color: Colors.green),
                  ),
                if (post.booCount > 0) ...[
                  const SizedBox(width: 4),
                  Text(
                    '-${post.booCount}',
                    style: const TextStyle(fontSize: 12, color: Colors.red),
                  ),
                ],
              ] else ...[
                if (post.pushCount > 0) ...[
                  const Icon(Icons.arrow_upward, size: 12, color: Colors.orange),
                  Text(
                    '${post.pushCount}',
                    style: const TextStyle(fontSize: 12, color: Colors.orange),
                  ),
                ],
                if (post.commentCount > 0) ...[
                  const SizedBox(width: 4),
                  const Icon(Icons.comment, size: 12, color: Colors.grey),
                  Text(
                    '${post.commentCount}',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                ],
              ],
              const Spacer(),
              Text(
                post.timeAgo,
                style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
              ),
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
                  _getSentimentLabel(post.sentiment),
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

  String _getSentimentLabel(String? sentiment) {
    switch (sentiment) {
      case 'positive':
        return 'Bullish';
      case 'negative':
        return 'Bearish';
      default:
        return 'Neutral';
    }
  }

  Future<void> _openPostUrl(String? url) async {
    if (url == null || url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No link available for this post')),
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
            SnackBar(content: Text('Cannot open link: $url')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error opening link: $e')),
        );
      }
    }
  }
}
