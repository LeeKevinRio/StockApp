import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:provider/provider.dart';
import '../models/news.dart';
import '../services/api_service.dart';

class NewsCard extends StatelessWidget {
  final StockNews news;

  const NewsCard({super.key, required this.news});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: () => _openUrl(context, news.sourceUrl),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 標題
              Text(
                news.title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),

              // 摘要
              if (news.summary != null && news.summary!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    news.summary!,
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.grey,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),

              // 連結提示
              if (news.sourceUrl != null && news.sourceUrl!.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      Icon(Icons.link, size: 14, color: Colors.blue.shade400),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          news.sourceUrl!,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.blue.shade400,
                            decoration: TextDecoration.underline,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),

              // 底部資訊
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // 來源和時間
                  Expanded(
                    child: Row(
                      children: [
                        if (news.source != null)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade200,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              news.source!,
                              style: const TextStyle(
                                fontSize: 12,
                                color: Colors.grey,
                              ),
                            ),
                          ),
                        const SizedBox(width: 8),
                        Text(
                          news.timeAgo,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                  ),

                  // 情緒標籤
                  if (news.sentiment != null) _buildSentimentChip(news),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSentimentChip(StockNews news) {
    Color color;
    Color bgColor;
    IconData icon;
    String label;

    switch (news.sentiment) {
      case 'positive':
        color = Colors.green.shade700;
        bgColor = Colors.green.shade50;
        icon = Icons.trending_up;
        label = news.sentimentText;
        break;
      case 'negative':
        color = Colors.red.shade700;
        bgColor = Colors.red.shade50;
        icon = Icons.trending_down;
        label = news.sentimentText;
        break;
      default:
        color = Colors.blueGrey.shade600;
        bgColor = Colors.blueGrey.shade50;
        icon = Icons.remove;
        label = news.sentimentText;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
          if (news.sentimentScore != null) ...[
            const SizedBox(width: 4),
            Text(
              '${(news.sentimentScore! * 100).toStringAsFixed(0)}',
              style: TextStyle(
                fontSize: 10,
                color: color.withAlpha(180),
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _openUrl(BuildContext context, String? url) async {
    if (url == null || url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('無法開啟連結')),
      );
      return;
    }

    final uri = Uri.parse(url);
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('無法開啟連結: $url')),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('開啟連結時發生錯誤: $e')),
        );
      }
    }
  }
}

class NewsListView extends StatefulWidget {
  final String stockId;
  final String market;

  const NewsListView({super.key, required this.stockId, this.market = 'TW'});

  @override
  State<NewsListView> createState() => _NewsListViewState();
}

class _NewsListViewState extends State<NewsListView> {
  List<StockNews> _newsList = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadNews();
  }

  Future<void> _loadNews() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();

      // Use unified getStockNews with market parameter
      final response = await apiService.getStockNews(
        widget.stockId,
        limit: 15,
        market: widget.market,
      );

      // Parse news from response
      final List<dynamic> newsData = response['news'] ?? [];
      _newsList = newsData.map<StockNews>((item) => StockNews.fromJson(item)).toList();

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
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                '載入失敗',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadNews,
                icon: const Icon(Icons.refresh),
                label: const Text('重試'),
              ),
            ],
          ),
        ),
      );
    }

    if (_newsList.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.newspaper, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('暫無相關新聞'),
            const SizedBox(height: 8),
            Text(
              '找不到 ${widget.stockId} 的相關新聞',
              style: const TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadNews,
              icon: const Icon(Icons.refresh),
              label: const Text('重新載入'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadNews,
      child: ListView.builder(
        itemCount: _newsList.length,
        itemBuilder: (context, index) {
          return NewsCard(news: _newsList[index]);
        },
      ),
    );
  }
}
