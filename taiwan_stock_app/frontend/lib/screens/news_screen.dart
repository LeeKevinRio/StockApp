import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';
import '../models/news.dart';

class NewsScreen extends StatefulWidget {
  const NewsScreen({super.key});

  @override
  State<NewsScreen> createState() => _NewsScreenState();
}

class _NewsScreenState extends State<NewsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<StockNews> _twNews = [];
  List<StockNews> _usNews = [];
  bool _isLoadingTW = true;
  bool _isLoadingUS = true;
  String? _errorTW;
  String? _errorUS;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadTWNews();
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    super.dispose();
  }

  void _onTabChanged() {
    if (_tabController.index == 0 && _twNews.isEmpty && !_isLoadingTW) {
      _loadTWNews();
    } else if (_tabController.index == 1 && _usNews.isEmpty && !_isLoadingUS) {
      _loadUSNews();
    } else if (_tabController.index == 1 && _usNews.isEmpty) {
      _loadUSNews();
    }
  }

  Future<void> _loadTWNews() async {
    setState(() {
      _isLoadingTW = true;
      _errorTW = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final response = await apiService.getMarketNews(limit: 30, market: 'TW');
      final List<dynamic> newsData = response['news'] ?? [];

      setState(() {
        _twNews = newsData.map((e) => StockNews.fromJson(e)).toList();
        _isLoadingTW = false;
      });
    } catch (e) {
      setState(() {
        _errorTW = e.toString();
        _isLoadingTW = false;
      });
    }
  }

  Future<void> _loadUSNews() async {
    setState(() {
      _isLoadingUS = true;
      _errorUS = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final response = await apiService.getMarketNews(limit: 30, market: 'US');
      final List<dynamic> newsData = response['news'] ?? [];

      setState(() {
        _usNews = newsData.map((e) => StockNews.fromJson(e)).toList();
        _isLoadingUS = false;
      });
    } catch (e) {
      setState(() {
        _errorUS = e.toString();
        _isLoadingUS = false;
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Financial News'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(
              icon: Icon(Icons.flag, size: 18),
              text: 'TW News',
            ),
            Tab(
              icon: Icon(Icons.public, size: 18),
              text: 'US News',
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              if (_tabController.index == 0) {
                _loadTWNews();
              } else {
                _loadUSNews();
              }
            },
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildNewsTab(
            news: _twNews,
            isLoading: _isLoadingTW,
            error: _errorTW,
            onRefresh: _loadTWNews,
            emptyMessage: 'No Taiwan news',
            source: 'Taiwan',
          ),
          _buildNewsTab(
            news: _usNews,
            isLoading: _isLoadingUS,
            error: _errorUS,
            onRefresh: _loadUSNews,
            emptyMessage: 'No US news',
            source: 'US',
          ),
        ],
      ),
    );
  }

  Widget _buildNewsTab({
    required List<StockNews> news,
    required bool isLoading,
    required String? error,
    required Future<void> Function() onRefresh,
    required String emptyMessage,
    required String source,
  }) {
    if (isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(
              'Loading $source news...',
              style: TextStyle(color: Theme.of(context).hintColor),
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
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('Load failed: $error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onRefresh,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (news.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.newspaper, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(emptyMessage, style: TextStyle(color: Theme.of(context).hintColor)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onRefresh,
              child: const Text('Refresh'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: news.length,
        itemBuilder: (context, index) {
          return _buildNewsCard(news[index], source);
        },
      ),
    );
  }

  Widget _buildNewsCard(StockNews news, String source) {
    final isUS = source == 'US';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: InkWell(
        onTap: () => _openUrl(news.sourceUrl),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: (isUS ? Colors.blue : Colors.red).withAlpha(26),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      news.source ?? (isUS ? 'Global News' : 'Taiwan News'),
                      style: TextStyle(
                        fontSize: 12,
                        color: isUS ? Colors.blue : Colors.red,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: _getSentimentColor(news.sentiment).withAlpha(26),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      _getSentimentLabel(news.sentiment),
                      style: TextStyle(
                        fontSize: 10,
                        color: _getSentimentColor(news.sentiment),
                      ),
                    ),
                  ),
                  const Spacer(),
                  if (news.publishedAt != null)
                    Text(
                      _formatDate(news.publishedAt!),
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).hintColor,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                news.title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              if (news.summary != null && news.summary!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  news.summary!,
                  style: TextStyle(
                    fontSize: 14,
                    color: Theme.of(context).textTheme.bodySmall?.color,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
              if (news.stockId != null) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.blue.withAlpha(26),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    news.stockId!,
                    style: const TextStyle(
                      fontSize: 11,
                      color: Colors.blue,
                    ),
                  ),
                ),
              ],
              // Show link indicator
              if (news.sourceUrl != null && news.sourceUrl!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Icon(
                        Icons.open_in_new,
                        size: 14,
                        color: Colors.grey[400],
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'Tap to read',
                        style: TextStyle(
                          fontSize: 11,
                          color: Theme.of(context).hintColor,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getSentimentColor(String? sentiment) {
    switch (sentiment) {
      case 'positive':
        return Colors.green;
      case 'negative':
        return Colors.red;
      default:
        return Colors.grey;
    }
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

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 60) {
      return '${diff.inMinutes}m ago';
    } else if (diff.inHours < 24) {
      return '${diff.inHours}h ago';
    } else if (diff.inDays < 7) {
      return '${diff.inDays}d ago';
    } else {
      return '${date.month}/${date.day}';
    }
  }
}
