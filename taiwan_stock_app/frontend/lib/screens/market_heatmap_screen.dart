import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/market_provider.dart';
import '../providers/locale_provider.dart';
import '../widgets/market_switcher.dart';

class MarketHeatmapScreen extends StatefulWidget {
  const MarketHeatmapScreen({super.key});

  @override
  State<MarketHeatmapScreen> createState() => _MarketHeatmapScreenState();
}

class _MarketHeatmapScreenState extends State<MarketHeatmapScreen>
    with SingleTickerProviderStateMixin {
  Map<String, dynamic>? _heatmapData;
  Map<String, dynamic>? _rankingsData;
  bool _isLoading = true;
  String? _error;
  String _rankCategory = 'gainers';
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _rankingsData = null;
    });

    try {
      final api = context.read<ApiService>();
      final market = context.read<MarketProvider>().marketCode;

      // 先載入 heatmap（通常很快），讓 UI 先顯示
      final heatmap = await api.getMarketHeatmap(market: market);
      if (mounted) {
        setState(() {
          _heatmapData = heatmap;
          _isLoading = false;
        });
      }

      // 背景載入 rankings（首次冷啟動可能需要 30 秒）
      _loadRankings(api, market);
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _loadRankings(ApiService api, String market) async {
    try {
      final rankings = await api.getMarketRankings(
        market: market,
        category: _rankCategory,
      );
      if (mounted) {
        setState(() {
          _rankingsData = rankings;
        });
      }
    } catch (e) {
      // Rankings 載入失敗不影響 heatmap 顯示
      debugPrint('Rankings load failed: $e');
    }
  }

  void _onMarketChanged() {
    _loadData();
  }

  @override
  Widget build(BuildContext context) {
    // 文字依「語系」決定，不再連動市場
    final isEn = context.watch<LocaleProvider>().isEnglish;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (Navigator.of(context).canPop()) {
              Navigator.of(context).pop();
            } else {
              Navigator.of(context).pushReplacementNamed('/home');
            }
          },
        ),
        title: Text(isEn ? 'Market Heatmap' : '市場熱力圖'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 4),
            child: CompactMarketSwitcher(onMarketChanged: _onMarketChanged),
          ),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: isEn ? 'Sector Heatmap' : '產業熱力圖'),
            Tab(text: isEn ? 'Rankings' : '漲跌排行'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildError()
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildHeatmapTab(),
                    _buildRankingsTab(),
                  ],
                ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          Text('載入失敗: $_error'),
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

  // === 熱力圖 Tab ===
  Widget _buildHeatmapTab() {
    final sectors = (_heatmapData?['sectors'] as List?) ?? [];
    if (sectors.isEmpty) {
      return const Center(child: Text('暫無數據'));
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            // Treemap 風格熱力圖
            _buildTreemap(sectors),
            const SizedBox(height: 16),
            // 產業詳細列表
            ...sectors.map((s) => _buildSectorCard(s)),
          ],
        ),
      ),
    );
  }

  Widget _buildTreemap(List<dynamic> sectors) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: LayoutBuilder(
          builder: (context, constraints) {
            return CustomPaint(
              size: Size(constraints.maxWidth, 250),
              painter: _HeatmapPainter(sectors),
            );
          },
        ),
      ),
    );
  }

  Widget _buildSectorCard(dynamic sector) {
    final name = sector['name'] ?? '';
    final avgChange = (sector['avg_change'] ?? 0.0).toDouble();
    final stocks = (sector['stocks'] as List?) ?? [];
    final color = avgChange >= 0 ? Colors.red : Colors.green;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ExpansionTile(
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: _getHeatColor(avgChange).withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Center(
            child: Text(
              '${avgChange >= 0 ? "+" : ""}${avgChange.toStringAsFixed(1)}%',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ),
        ),
        title: Text(name, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text('${stocks.length} 支股票'),
        children: stocks.map<Widget>((stock) {
          final changePct = (stock['change_percent'] ?? 0.0).toDouble();
          final stockColor = changePct >= 0 ? Colors.red : Colors.green;
          return ListTile(
            dense: true,
            title: Text('${stock["stock_id"]} ${stock["name"] ?? ""}'),
            trailing: Text(
              '${changePct >= 0 ? "+" : ""}${changePct.toStringAsFixed(2)}%',
              style: TextStyle(
                  fontWeight: FontWeight.bold, color: stockColor),
            ),
            onTap: () {
              final market = context.read<MarketProvider>().marketCode;
              Navigator.pushNamed(context, '/stock-detail', arguments: {
                'stockId': stock['stock_id'],
                'market': market,
              });
            },
          );
        }).toList(),
      ),
    );
  }

  // === 排行榜 Tab ===
  Widget _buildRankingsTab() {
    final isEn = context.watch<LocaleProvider>().isEnglish;
    return Column(
      children: [
        // 分類選擇
        Padding(
          padding: const EdgeInsets.all(12),
          child: SegmentedButton<String>(
            segments: [
              ButtonSegment(value: 'gainers', label: Text(isEn ? 'Gainers' : '漲幅')),
              ButtonSegment(value: 'losers', label: Text(isEn ? 'Losers' : '跌幅')),
              ButtonSegment(value: 'volume', label: Text(isEn ? 'Volume' : '成交量')),
              ButtonSegment(value: 'active', label: Text(isEn ? 'Active' : '波動')),
            ],
            selected: {_rankCategory},
            onSelectionChanged: (values) {
              setState(() => _rankCategory = values.first);
              _loadData();
            },
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _loadData,
            child: _buildRankingsList(),
          ),
        ),
      ],
    );
  }

  Widget _buildRankingsList() {
    if (_rankingsData == null) {
      return const Center(child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 12),
          Text('排行榜載入中...', style: TextStyle(color: Colors.grey)),
        ],
      ));
    }
    final stocks = (_rankingsData?['stocks'] as List?) ?? [];
    if (stocks.isEmpty) {
      return const Center(child: Text('暫無數據'));
    }

    return ListView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      itemCount: stocks.length,
      itemBuilder: (context, index) {
        final stock = stocks[index];
        final changePct = (stock['change_percent'] ?? 0.0).toDouble();
        final isUp = changePct >= 0;
        final color = isUp ? Colors.red : Colors.green;

        return ListTile(
          leading: CircleAvatar(
            backgroundColor: color.withValues(alpha: 0.1),
            child: Text(
              '${index + 1}',
              style: TextStyle(
                  fontWeight: FontWeight.bold, color: color, fontSize: 14),
            ),
          ),
          title: Text(
            '${stock["stock_id"]} ${stock["name"] ?? ""}',
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          subtitle: _rankCategory == 'volume'
              ? Text('成交量: ${_formatVolume(stock["volume"] ?? 0)}')
              : null,
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${stock["price"]}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              Text(
                '${isUp ? "+" : ""}${changePct.toStringAsFixed(2)}%',
                style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.bold,
                    fontSize: 13),
              ),
            ],
          ),
          onTap: () {
            final market = context.read<MarketProvider>().marketCode;
            Navigator.pushNamed(context, '/stock-detail', arguments: {
              'stockId': stock['stock_id'],
              'market': market,
            });
          },
        );
      },
    );
  }

  Color _getHeatColor(double change) {
    if (change >= 3) return Colors.red.shade800;
    if (change >= 1.5) return Colors.red.shade600;
    if (change >= 0.5) return Colors.red.shade300;
    if (change >= 0) return Colors.red.shade100;
    if (change >= -0.5) return Colors.green.shade100;
    if (change >= -1.5) return Colors.green.shade300;
    if (change >= -3) return Colors.green.shade600;
    return Colors.green.shade800;
  }

  String _formatVolume(dynamic vol) {
    final v = (vol is int) ? vol : (vol as num).toInt();
    if (v >= 100000000) return '${(v / 100000000).toStringAsFixed(1)}億';
    if (v >= 10000) return '${(v / 10000).toStringAsFixed(1)}萬';
    return v.toString();
  }
}

/// 熱力圖 CustomPainter
class _HeatmapPainter extends CustomPainter {
  final List<dynamic> sectors;
  _HeatmapPainter(this.sectors);

  @override
  void paint(Canvas canvas, Size size) {
    if (sectors.isEmpty) return;

    final totalStocks = sectors.fold<int>(
        0, (sum, s) => sum + ((s['stocks'] as List?)?.length ?? 0));
    if (totalStocks == 0) return;

    double x = 0;
    final rowHeight = size.height;

    for (final sector in sectors) {
      final stocks = (sector['stocks'] as List?) ?? [];
      final sectorWidth =
          (stocks.length / totalStocks) * size.width;
      if (sectorWidth < 2) continue;

      final avgChange = (sector['avg_change'] ?? 0.0).toDouble();
      final color = _getColor(avgChange);

      // 繪製產業區塊
      final rect = Rect.fromLTWH(x, 0, sectorWidth, rowHeight);
      canvas.drawRect(rect, Paint()..color = color);

      // 繪製邊框
      canvas.drawRect(
          rect,
          Paint()
            ..color = Colors.white
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1);

      // 繪製文字
      if (sectorWidth > 40) {
        final textPainter = TextPainter(
          text: TextSpan(
            text: '${sector["name"]}\n${avgChange >= 0 ? "+" : ""}${avgChange.toStringAsFixed(1)}%',
            style: TextStyle(
              color: avgChange.abs() > 1 ? Colors.white : Colors.black87,
              fontSize: sectorWidth > 80 ? 11 : 9,
              fontWeight: FontWeight.bold,
            ),
          ),
          textAlign: TextAlign.center,
          textDirection: TextDirection.ltr,
        );
        textPainter.layout(maxWidth: sectorWidth - 4);
        textPainter.paint(
          canvas,
          Offset(
            x + (sectorWidth - textPainter.width) / 2,
            (rowHeight - textPainter.height) / 2,
          ),
        );
      }

      x += sectorWidth;
    }
  }

  Color _getColor(double change) {
    if (change >= 3) return Colors.red.shade800;
    if (change >= 1.5) return Colors.red.shade600;
    if (change >= 0.5) return Colors.red.shade400;
    if (change >= 0) return Colors.red.shade200;
    if (change >= -0.5) return Colors.green.shade200;
    if (change >= -1.5) return Colors.green.shade400;
    if (change >= -3) return Colors.green.shade600;
    return Colors.green.shade800;
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
