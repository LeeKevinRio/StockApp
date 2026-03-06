import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';
import '../models/social_sentiment.dart';
import '../providers/market_provider.dart';

class SocialScreen extends StatefulWidget {
  const SocialScreen({super.key});

  @override
  State<SocialScreen> createState() => _SocialScreenState();
}

class _SocialScreenState extends State<SocialScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // Taiwan data (PTT)
  List<HotStock> _twHotStocks = [];
  Map<String, dynamic>? _twMarketSentiment;
  bool _isTwLoading = true;
  String? _twError;

  // US data (Reddit)
  List<HotStock> _usHotStocks = [];
  Map<String, dynamic>? _usMarketSentiment;
  bool _isUsLoading = true;
  String? _usError;

  String _currentMarket = 'TW';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadAllData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadAllData() async {
    await Future.wait([
      _loadTWData(),
      _loadUSData(),
    ]);
  }

  Future<void> _loadTWData() async {
    setState(() {
      _isTwLoading = true;
      _twError = null;
    });

    try {
      final apiService = context.read<ApiService>();

      final hotStocksResponse = await apiService.getHotStocks(limit: 20, market: 'TW');
      final List<dynamic> stocksData = hotStocksResponse['stocks'] ?? [];

      final marketSentiment = await apiService.getMarketSentiment(market: 'TW');

      setState(() {
        _twHotStocks = stocksData.map((e) => HotStock.fromJson(e)).toList();
        _twMarketSentiment = marketSentiment;
        _isTwLoading = false;
      });
    } catch (e) {
      setState(() {
        _twError = e.toString();
        _isTwLoading = false;
      });
    }
  }

  Future<void> _loadUSData() async {
    setState(() {
      _isUsLoading = true;
      _usError = null;
    });

    try {
      final apiService = context.read<ApiService>();

      final hotStocksResponse = await apiService.getHotStocks(limit: 20, market: 'US');
      final List<dynamic> stocksData = hotStocksResponse['stocks'] ?? [];

      final marketSentiment = await apiService.getMarketSentiment(market: 'US');

      setState(() {
        _usHotStocks = stocksData.map((e) => HotStock.fromJson(e)).toList();
        _usMarketSentiment = marketSentiment;
        _isUsLoading = false;
      });
    } catch (e) {
      setState(() {
        _usError = e.toString();
        _isUsLoading = false;
      });
    }
  }

  Future<void> _openUrl(String? url) async {
    if (url == null || url.isEmpty) return;

    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Social Sentiment'),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(96),
            child: Column(
              children: [
                // Market Switcher
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: SegmentedButton<String>(
                          segments: [
                            ButtonSegment<String>(
                              value: 'TW',
                              label: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Container(
                                    width: 16,
                                    height: 12,
                                    decoration: BoxDecoration(
                                      color: Colors.red,
                                      borderRadius: BorderRadius.circular(2),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  const Text('PTT'),
                                ],
                              ),
                              icon: const Icon(Icons.forum, size: 18),
                            ),
                            ButtonSegment<String>(
                              value: 'US',
                              label: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Container(
                                    width: 16,
                                    height: 12,
                                    decoration: BoxDecoration(
                                      color: Colors.orange,
                                      borderRadius: BorderRadius.circular(2),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  const Text('Reddit'),
                                ],
                              ),
                              icon: const Icon(Icons.reddit, size: 18),
                            ),
                          ],
                          selected: {_currentMarket},
                          onSelectionChanged: (Set<String> selection) {
                            setState(() {
                              _currentMarket = selection.first;
                            });
                          },
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton(
                        icon: const Icon(Icons.refresh),
                        onPressed: _currentMarket == 'TW' ? _loadTWData : _loadUSData,
                      ),
                    ],
                  ),
                ),
                // Content Tabs
                TabBar(
                  controller: _tabController,
                  tabs: [
                    Tab(
                      icon: const Icon(Icons.trending_up),
                      text: _currentMarket == 'TW' ? 'Hot Stocks' : 'Trending',
                    ),
                    Tab(
                      icon: const Icon(Icons.sentiment_satisfied),
                      text: _currentMarket == 'TW' ? 'Market Mood' : 'Sentiment',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        body: _currentMarket == 'TW'
            ? _buildMarketContent(
                isLoading: _isTwLoading,
                error: _twError,
                hotStocks: _twHotStocks,
                marketSentiment: _twMarketSentiment,
                onRefresh: _loadTWData,
                isTaiwan: true,
              )
            : _buildMarketContent(
                isLoading: _isUsLoading,
                error: _usError,
                hotStocks: _usHotStocks,
                marketSentiment: _usMarketSentiment,
                onRefresh: _loadUSData,
                isTaiwan: false,
              ),
      ),
    );
  }

  Widget _buildMarketContent({
    required bool isLoading,
    required String? error,
    required List<HotStock> hotStocks,
    required Map<String, dynamic>? marketSentiment,
    required Future<void> Function() onRefresh,
    required bool isTaiwan,
  }) {
    if (isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(
              isTaiwan
                  ? 'Loading PTT discussions...'
                  : 'Loading Reddit discussions...',
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    if (error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.red.shade300,
            ),
            const SizedBox(height: 16),
            Text('Error: $error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onRefresh,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    return TabBarView(
      controller: _tabController,
      children: [
        _buildHotStocksTab(hotStocks, onRefresh, isTaiwan),
        _buildMarketSentimentTab(marketSentiment, onRefresh, isTaiwan),
      ],
    );
  }

  Widget _buildHotStocksTab(List<HotStock> hotStocks, Future<void> Function() onRefresh, bool isTaiwan) {
    if (hotStocks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isTaiwan ? Icons.forum : Icons.reddit,
              size: 64,
              color: Colors.grey,
            ),
            const SizedBox(height: 16),
            Text(
              isTaiwan ? 'No PTT discussions found' : 'No Reddit discussions found',
              style: const TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh),
              label: const Text('Refresh'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: hotStocks.length,
        itemBuilder: (context, index) {
          return _buildHotStockCard(hotStocks[index], index + 1, isTaiwan);
        },
      ),
    );
  }

  Widget _buildHotStockCard(HotStock stock, int rank, bool isTaiwan) {
    final sentimentColor = _getSentimentColor(stock.sentiment);
    final sourceLabel = isTaiwan ? 'PTT' : 'Reddit';
    final badgeColor = isTaiwan ? Colors.red : Colors.orange;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: badgeColor.withAlpha(26),
          child: Text(
            '#$rank',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: badgeColor,
            ),
          ),
        ),
        title: Row(
          children: [
            // Market badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
              decoration: BoxDecoration(
                color: badgeColor.withAlpha(26),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                isTaiwan ? 'TW' : 'US',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: badgeColor,
                ),
              ),
            ),
            const SizedBox(width: 6),
            Text(
              stock.stockId,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            if (stock.stockName != null) ...[
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  stock.stockName!,
                  style: TextStyle(color: Theme.of(context).textTheme.bodySmall?.color, fontSize: 14),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ],
        ),
        subtitle: Row(
          children: [
            Icon(Icons.forum, size: 14, color: Colors.grey[400]),
            const SizedBox(width: 4),
            Text('${stock.mentionCount} ${isTaiwan ? "posts" : "mentions"}'),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
              decoration: BoxDecoration(
                color: sentimentColor.withAlpha(26),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                _getSentimentText(stock.sentiment, isTaiwan),
                style: TextStyle(fontSize: 11, color: sentimentColor),
              ),
            ),
            const Spacer(),
            Text(
              sourceLabel,
              style: TextStyle(
                fontSize: 11,
                color: badgeColor,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        children: [
          if (stock.samplePosts.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isTaiwan ? 'Related Posts' : 'Reddit Discussions',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  ...stock.samplePosts.take(5).map((post) => _buildPostItem(post, isTaiwan)),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildPostItem(SocialPost post, bool isTaiwan) {
    return InkWell(
      onTap: () => _openUrl(post.url),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              isTaiwan ? Icons.article : Icons.reddit,
              size: 16,
              color: isTaiwan ? Colors.grey[400] : Colors.orange[300],
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    post.title,
                    style: const TextStyle(fontSize: 14),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text(
                        post.board ?? (isTaiwan ? 'PTT' : 'Reddit'),
                        style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor),
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
                        // Reddit upvotes
                        if (post.pushCount > 0) ...[
                          const Icon(Icons.arrow_upward, size: 12, color: Colors.orange),
                          Text(
                            '${post.pushCount}',
                            style: const TextStyle(fontSize: 12, color: Colors.orange),
                          ),
                        ],
                        if (post.commentCount > 0) ...[
                          const SizedBox(width: 8),
                          const Icon(Icons.comment, size: 12, color: Colors.grey),
                          const SizedBox(width: 2),
                          Text(
                            '${post.commentCount}',
                            style: TextStyle(fontSize: 12, color: Theme.of(context).textTheme.bodySmall?.color),
                          ),
                        ],
                      ],
                      const Spacer(),
                      Text(
                        post.timeAgo,
                        style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor),
                      ),
                      const SizedBox(width: 4),
                      const Icon(Icons.open_in_new, size: 12, color: Colors.grey),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMarketSentimentTab(Map<String, dynamic>? marketSentiment, Future<void> Function() onRefresh, bool isTaiwan) {
    if (marketSentiment == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.sentiment_neutral, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('No sentiment data available'),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh),
              label: const Text('Refresh'),
            ),
          ],
        ),
      );
    }

    final overall = marketSentiment['overall'] ?? 'neutral';
    final score = (marketSentiment['score'] ?? 0).toDouble();
    final positive = marketSentiment['positive'] ?? 0;
    final negative = marketSentiment['negative'] ?? 0;
    final neutral = marketSentiment['neutral'] ?? 0;
    final total = positive + negative + neutral;
    final source = marketSentiment['source'] ?? (isTaiwan ? 'PTT' : 'Reddit');

    return RefreshIndicator(
      onRefresh: onRefresh,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Source Badge
            Container(
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
                    'Source: $source',
                    style: TextStyle(
                      color: isTaiwan ? Colors.red : Colors.orange,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            // Overall Sentiment Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                      isTaiwan ? 'Taiwan Market Sentiment' : 'US Market Sentiment',
                      style: const TextStyle(fontSize: 16, color: Colors.grey),
                    ),
                    const SizedBox(height: 16),
                    Icon(
                      _getSentimentIcon(overall),
                      size: 64,
                      color: _getSentimentColor(overall),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _getSentimentText(overall, isTaiwan),
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: _getSentimentColor(overall),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Sentiment Score: ${score.toStringAsFixed(2)}',
                      style: const TextStyle(color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Sentiment Distribution
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Sentiment Distribution',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    _buildSentimentBar(isTaiwan ? 'Bullish' : 'Bullish', positive, total, Colors.green),
                    const SizedBox(height: 12),
                    _buildSentimentBar('Neutral', neutral, total, Colors.grey),
                    const SizedBox(height: 12),
                    _buildSentimentBar(isTaiwan ? 'Bearish' : 'Bearish', negative, total, Colors.red),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Stats Cards
            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    'Total Posts',
                    total.toString(),
                    isTaiwan ? Icons.forum : Icons.reddit,
                    color: isTaiwan ? Colors.blue : Colors.orange,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildStatCard(
                    'Bull Ratio',
                    total > 0 ? '${(positive / total * 100).toStringAsFixed(1)}%' : '0%',
                    Icons.trending_up,
                    color: Colors.green,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Subreddits/Boards Info
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isTaiwan ? 'Data Sources (PTT Boards)' : 'Data Sources (Subreddits)',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: isTaiwan
                          ? [
                              _buildSourceChip('PTT Stock', Colors.blue),
                              _buildSourceChip('PTT Option', Colors.purple),
                              _buildSourceChip('Dcard', Colors.teal),
                              _buildSourceChip('Mobile01', Colors.green),
                            ]
                          : [
                              _buildSourceChip('r/wallstreetbets', Colors.orange),
                              _buildSourceChip('r/stocks', Colors.blue),
                              _buildSourceChip('r/investing', Colors.green),
                              _buildSourceChip('r/options', Colors.purple),
                              _buildSourceChip('r/StockMarket', Colors.teal),
                            ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSourceChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withAlpha(77)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: color,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _buildSentimentBar(String label, int count, int total, Color color) {
    final ratio = total > 0 ? count / total : 0.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label),
            Text('$count (${(ratio * 100).toStringAsFixed(1)}%)'),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: ratio,
            backgroundColor: Colors.grey[800],
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 8,
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, {Color? color}) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, size: 32, color: color ?? Colors.blue),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              label,
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  Color _getSentimentColor(String sentiment) {
    switch (sentiment) {
      case 'positive':
        return Colors.green;
      case 'negative':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _getSentimentText(String sentiment, bool isTaiwan) {
    switch (sentiment) {
      case 'positive':
        return isTaiwan ? 'Bullish' : 'Bullish';
      case 'negative':
        return isTaiwan ? 'Bearish' : 'Bearish';
      default:
        return 'Neutral';
    }
  }

  IconData _getSentimentIcon(String sentiment) {
    switch (sentiment) {
      case 'positive':
        return Icons.trending_up;
      case 'negative':
        return Icons.trending_down;
      default:
        return Icons.trending_flat;
    }
  }
}
