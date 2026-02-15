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
      return _buildSkeletonLoading();
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('載入失敗', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.grey), textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadData,
              icon: const Icon(Icons.refresh),
              label: const Text('重試'),
            ),
          ],
        ),
      );
    }

    if (_data == null) {
      return const Center(child: Text('暫無社群數據'));
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 來源標籤
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
                      isTaiwan ? '來源: PTT / Dcard / Mobile01' : '來源: Reddit',
                      style: TextStyle(
                        color: isTaiwan ? Colors.red : Colors.orange,
                        fontWeight: FontWeight.w500,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            _buildSentimentSummary(),
            const SizedBox(height: 20),
            _buildSentimentDistribution(),
            const SizedBox(height: 20),
            _buildSentimentTrend(),
            const SizedBox(height: 20),
            _buildRecentPosts(),
          ],
        ),
      ),
    );
  }

  /// 骨架屏載入動畫
  Widget _buildSkeletonLoading() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          const SizedBox(height: 20),
          // 情緒摘要骨架
          _buildSkeletonCard(height: 120),
          const SizedBox(height: 16),
          // 分布圖骨架
          _buildSkeletonCard(height: 60),
          const SizedBox(height: 16),
          // 趨勢圖骨架
          _buildSkeletonCard(height: 100),
          const SizedBox(height: 16),
          // 貼文列表骨架
          ...[1, 2, 3].map((_) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: _buildSkeletonCard(height: 70),
          )),
        ],
      ),
    );
  }

  Widget _buildSkeletonCard({required double height}) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(12),
      ),
      child: const Center(
        child: SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
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
        sentimentColor = Colors.green.shade600;
        sentimentIcon = Icons.trending_up;
        sentimentText = '看多情緒';
        break;
      case 'negative':
        sentimentColor = Colors.red.shade600;
        sentimentIcon = Icons.trending_down;
        sentimentText = '看空情緒';
        break;
      default:
        sentimentColor = Colors.blueGrey;
        sentimentIcon = Icons.trending_flat;
        sentimentText = '中性情緒';
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
                      '社群輿論',
                      style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
                    ),
                    Text(
                      sentimentText,
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: sentimentColor,
                      ),
                    ),
                    if (summary.score != 0)
                      Text(
                        '情緒分數: ${summary.score > 0 ? "+" : ""}${(summary.score * 100).toStringAsFixed(0)}',
                        style: TextStyle(fontSize: 12, color: sentimentColor),
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
                _buildStatItem('看多', summary.positive.toString(), Colors.green.shade600),
                _buildStatItem('看空', summary.negative.toString(), Colors.red.shade600),
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
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color),
        ),
        Text(
          label,
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
        ),
      ],
    );
  }

  Widget _buildSentimentDistribution() {
    final summary = _data!.sentimentSummary;
    final total = summary.total;

    if (total == 0) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('情緒分布', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Row(
            children: [
              Expanded(
                flex: (summary.positiveRatio * 100).round().clamp(1, 100),
                child: Container(height: 28, color: Colors.green.shade400),
              ),
              Expanded(
                flex: (summary.negativeRatio * 100).round().clamp(1, 100),
                child: Container(height: 28, color: Colors.red.shade400),
              ),
              Expanded(
                flex: ((1 - summary.positiveRatio - summary.negativeRatio) * 100).round().clamp(1, 100),
                child: Container(height: 28, color: Colors.grey.shade300),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(children: [
              Container(width: 12, height: 12, color: Colors.green.shade400),
              const SizedBox(width: 4),
              Text('看多 ${(summary.positiveRatio * 100).toStringAsFixed(0)}%',
                  style: const TextStyle(fontSize: 12)),
            ]),
            Row(children: [
              Container(width: 12, height: 12, color: Colors.red.shade400),
              const SizedBox(width: 4),
              Text('看空 ${(summary.negativeRatio * 100).toStringAsFixed(0)}%',
                  style: const TextStyle(fontSize: 12)),
            ]),
            Row(children: [
              Container(width: 12, height: 12, color: Colors.grey.shade300),
              const SizedBox(width: 4),
              Text('中性 ${((1 - summary.positiveRatio - summary.negativeRatio) * 100).toStringAsFixed(0)}%',
                  style: const TextStyle(fontSize: 12)),
            ]),
          ],
        ),
      ],
    );
  }

  Widget _buildSentimentTrend() {
    // 使用 sentiment_trend 數據（來自後端 7 天趨勢）
    if (_data == null) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('7日情緒趨勢', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Row(
            children: [
              Icon(Icons.show_chart, color: Colors.blue.shade300),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  '情緒趨勢數據將在累積多日資料後顯示',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ),
            ],
          ),
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
              isTaiwan ? '近期討論' : 'Reddit 討論',
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
                  Icon(Icons.forum, size: 48, color: Colors.grey.shade400),
                  const SizedBox(height: 8),
                  Text('暫無相關討論', style: TextStyle(color: Colors.grey.shade600)),
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
    Color sentimentBg;
    String sentimentLabel;
    switch (post.sentiment) {
      case 'positive':
        sentimentColor = Colors.green.shade700;
        sentimentBg = Colors.green.shade50;
        sentimentLabel = '看多';
        break;
      case 'negative':
        sentimentColor = Colors.red.shade700;
        sentimentBg = Colors.red.shade50;
        sentimentLabel = '看空';
        break;
      default:
        sentimentColor = Colors.blueGrey.shade600;
        sentimentBg = Colors.blueGrey.shade50;
        sentimentLabel = '中性';
    }

    // 平台顏色
    Color platformColor;
    switch (post.platform) {
      case 'ptt':
        platformColor = Colors.indigo;
        break;
      case 'dcard':
        platformColor = Colors.blue;
        break;
      case 'mobile01':
        platformColor = Colors.teal;
        break;
      default:
        platformColor = Colors.grey;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () => _openPostUrl(post.url),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 標題
              Text(
                post.title,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 8),
              // 底部資訊列
              Row(
                children: [
                  // 平台標籤
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: platformColor.withAlpha(26),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      post.board ?? post.platform.toUpperCase(),
                      style: TextStyle(fontSize: 11, color: platformColor, fontWeight: FontWeight.w500),
                    ),
                  ),
                  const SizedBox(width: 8),
                  // 推噓
                  if (post.pushCount > 0) ...[
                    Icon(Icons.thumb_up_alt_outlined, size: 12, color: Colors.green.shade600),
                    const SizedBox(width: 2),
                    Text('${post.pushCount}', style: TextStyle(fontSize: 11, color: Colors.green.shade600)),
                    const SizedBox(width: 6),
                  ],
                  if (post.booCount > 0) ...[
                    Icon(Icons.thumb_down_alt_outlined, size: 12, color: Colors.red.shade600),
                    const SizedBox(width: 2),
                    Text('${post.booCount}', style: TextStyle(fontSize: 11, color: Colors.red.shade600)),
                    const SizedBox(width: 6),
                  ],
                  const Spacer(),
                  // 時間
                  if (post.timeAgo.isNotEmpty)
                    Text(post.timeAgo, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                  const SizedBox(width: 8),
                  // 情緒標籤
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: sentimentBg,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: sentimentColor.withAlpha(80)),
                    ),
                    child: Text(
                      sentimentLabel,
                      style: TextStyle(fontSize: 11, color: sentimentColor, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
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
        const SnackBar(content: Text('無法開啟連結')),
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
