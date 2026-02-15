import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class TradingDiaryScreen extends StatefulWidget {
  const TradingDiaryScreen({super.key});

  @override
  State<TradingDiaryScreen> createState() => _TradingDiaryScreenState();
}

class _TradingDiaryScreenState extends State<TradingDiaryScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<Map<String, dynamic>> _entries = [];
  Map<String, dynamic>? _stats;
  bool _isLoading = true;
  String? _error;
  String _searchQuery = '';
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final api = context.read<ApiService>();
      final results = await Future.wait([
        api.getDiaryEntries(limit: 100),
        api.getDiaryStats(days: 30),
      ]);

      if (mounted) {
        setState(() {
          final diaryData = results[0] as Map<String, dynamic>;
          _entries = (diaryData['entries'] as List?)
                  ?.cast<Map<String, dynamic>>() ??
              [];
          _stats = results[1] as Map<String, dynamic>;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
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
        title: const Text('交易日記'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '日記'),
            Tab(text: '統計'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('載入失敗: $_error'),
                      ElevatedButton(onPressed: _loadData, child: const Text('重試')),
                    ],
                  ),
                )
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildDiaryList(),
                    _buildStatsView(),
                  ],
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddDiaryDialog,
        icon: const Icon(Icons.add),
        label: const Text('新增日記'),
      ),
    );
  }

  Widget _buildDiaryList() {
    final filtered = _searchQuery.isEmpty
        ? _entries
        : _entries.where((e) {
            final notes = (e['notes'] as String? ?? '').toLowerCase();
            final stockId = (e['stock_id'] as String? ?? '').toLowerCase();
            final tags = (e['tags'] as String? ?? '').toLowerCase();
            final q = _searchQuery.toLowerCase();
            return notes.contains(q) || stockId.contains(q) || tags.contains(q);
          }).toList();

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: '搜尋日記 (股票/標籤/內容)',
              prefixIcon: const Icon(Icons.search, size: 20),
              isDense: true,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              suffixIcon: _searchQuery.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 18),
                      onPressed: () {
                        _searchController.clear();
                        setState(() => _searchQuery = '');
                      },
                    )
                  : null,
            ),
            onChanged: (v) => setState(() => _searchQuery = v),
          ),
        ),
        Expanded(
          child: filtered.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(_searchQuery.isNotEmpty ? Icons.search_off : Icons.book_outlined,
                          size: 64, color: Colors.grey),
                      const SizedBox(height: 16),
                      Text(
                        _searchQuery.isNotEmpty ? '找不到符合的日記' : '尚無交易日記',
                        style: const TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: filtered.length,
                    itemBuilder: (context, index) => _buildDiaryCard(filtered[index]),
                  ),
                ),
        ),
      ],
    );
  }

  Widget _buildDiaryCard(Map<String, dynamic> entry) {
    final tradeType = entry['trade_type'] as String? ?? 'note';
    final emotion = entry['emotion'] as String?;
    final rating = entry['rating'] as int?;
    final pnl = entry['pnl'] as num?;
    final stockId = entry['stock_id'] as String?;
    final notes = entry['notes'] as String?;
    final lesson = entry['lesson_learned'] as String?;
    final tags = entry['tags'] as String?;
    final dateStr = entry['trade_date'] as String? ?? '';

    final typeIcon = _getTradeTypeIcon(tradeType);
    final typeColor = _getTradeTypeColor(tradeType);

    String dateDisplay = '';
    try {
      final dt = DateTime.parse(dateStr);
      dateDisplay = '${dt.month}/${dt.day} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      dateDisplay = dateStr;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 頂部行
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: typeColor.withAlpha(25),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(typeIcon, size: 14, color: typeColor),
                      const SizedBox(width: 4),
                      Text(
                        _getTradeTypeText(tradeType),
                        style: TextStyle(color: typeColor, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                if (stockId != null) ...[
                  const SizedBox(width: 8),
                  Text(stockId, style: const TextStyle(fontWeight: FontWeight.bold)),
                ],
                const Spacer(),
                Text(dateDisplay, style: TextStyle(fontSize: 11, color: Colors.grey[500])),
                PopupMenuButton<String>(
                  itemBuilder: (context) => [
                    const PopupMenuItem(value: 'delete', child: Text('刪除', style: TextStyle(color: Colors.red))),
                  ],
                  onSelected: (value) {
                    if (value == 'delete') _deleteDiaryEntry(entry['id']);
                  },
                  iconSize: 18,
                ),
              ],
            ),
            // 盈虧
            if (pnl != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(
                    '${pnl >= 0 ? "+" : ""}\$${pnl.toStringAsFixed(0)}',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: pnl >= 0 ? Colors.red : Colors.green,
                    ),
                  ),
                  if (entry['pnl_percent'] != null) ...[
                    const SizedBox(width: 8),
                    Text(
                      '(${(entry['pnl_percent'] as num) >= 0 ? "+" : ""}${(entry['pnl_percent'] as num).toStringAsFixed(2)}%)',
                      style: TextStyle(
                        color: (entry['pnl_percent'] as num) >= 0 ? Colors.red : Colors.green,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ],
              ),
            ],
            // 筆記
            if (notes != null && notes.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(notes, style: TextStyle(color: Colors.grey[700], height: 1.4)),
            ],
            // 教訓
            if (lesson != null && lesson.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.amber.withAlpha(20),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.withAlpha(80)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.lightbulb, size: 16, color: Colors.amber),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(lesson, style: const TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
              ),
            ],
            // 底部行：情緒 + 評分 + 標籤
            const SizedBox(height: 8),
            Row(
              children: [
                if (emotion != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: _getEmotionColor(emotion).withAlpha(25),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      _getEmotionText(emotion),
                      style: TextStyle(fontSize: 11, color: _getEmotionColor(emotion)),
                    ),
                  ),
                if (rating != null) ...[
                  const SizedBox(width: 8),
                  Row(
                    children: List.generate(5, (i) => Icon(
                      i < rating ? Icons.star : Icons.star_border,
                      size: 14,
                      color: Colors.amber,
                    )),
                  ),
                ],
                if (tags != null && tags.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      tags.split(',').map((t) => '#${t.trim()}').join(' '),
                      style: TextStyle(fontSize: 11, color: Colors.blue[400]),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsView() {
    if (_stats == null) {
      return const Center(child: Text('暫無統計數據'));
    }

    final stats = _stats!;
    final totalEntries = stats['total_entries'] ?? 0;
    final totalPnl = (stats['total_pnl'] as num? ?? 0).toDouble();
    final winRate = (stats['win_rate'] as num? ?? 0).toDouble();
    final avgRating = (stats['avg_rating'] as num? ?? 0).toDouble();
    final emotionDist = (stats['emotion_distribution'] as Map?) ?? {};

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // 概覽卡片
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('30 日統計', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const Divider(),
                  Row(
                    children: [
                      Expanded(child: _buildStatCard('日記數', '$totalEntries', Colors.blue)),
                      const SizedBox(width: 8),
                      Expanded(child: _buildStatCard(
                        '總盈虧',
                        '${totalPnl >= 0 ? "+" : ""}\$${totalPnl.toStringAsFixed(0)}',
                        totalPnl >= 0 ? Colors.red : Colors.green,
                      )),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(child: _buildStatCard('勝率', '${winRate.toStringAsFixed(1)}%', Colors.orange)),
                      const SizedBox(width: 8),
                      Expanded(child: _buildStatCard('平均評分', avgRating.toStringAsFixed(1), Colors.amber)),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // 交易類型
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('交易分佈', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const Divider(),
                  Row(
                    children: [
                      Expanded(child: _buildStatCard('買入', '${stats['buy_count'] ?? 0}', Colors.red)),
                      const SizedBox(width: 8),
                      Expanded(child: _buildStatCard('賣出', '${stats['sell_count'] ?? 0}', Colors.green)),
                      const SizedBox(width: 8),
                      Expanded(child: _buildStatCard('獲利', '${stats['win_count'] ?? 0}', Colors.blue)),
                      const SizedBox(width: 8),
                      Expanded(child: _buildStatCard('虧損', '${stats['loss_count'] ?? 0}', Colors.grey)),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // 情緒分佈
          if (emotionDist.isNotEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('情緒分佈', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const Divider(),
                    ...emotionDist.entries.map((e) {
                      final emotion = e.key as String;
                      final count = (e.value as num).toInt();
                      final total = emotionDist.values.fold<int>(0, (sum, v) => sum + (v as num).toInt());
                      final ratio = total > 0 ? count / total : 0.0;
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(
                          children: [
                            SizedBox(
                              width: 60,
                              child: Text(_getEmotionText(emotion), style: const TextStyle(fontSize: 13)),
                            ),
                            Expanded(
                              child: Stack(
                                children: [
                                  Container(
                                    height: 20,
                                    decoration: BoxDecoration(
                                      color: Colors.grey.withAlpha(30),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                  ),
                                  FractionallySizedBox(
                                    widthFactor: ratio,
                                    child: Container(
                                      height: 20,
                                      decoration: BoxDecoration(
                                        color: _getEmotionColor(emotion).withAlpha(150),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            SizedBox(
                              width: 40,
                              child: Text(
                                '$count',
                                textAlign: TextAlign.right,
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 16),
          // 情緒 vs 績效分析
          if (emotionDist.isNotEmpty)
            _buildEmotionPerformanceCard(),
          const SizedBox(height: 16),
          // 連勝/連敗追蹤
          _buildStreakCard(),
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  void _showAddDiaryDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => _AddDiarySheet(onCreated: _loadData),
    );
  }

  Future<void> _deleteDiaryEntry(int id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('確認刪除'),
        content: const Text('確定要刪除這則日記嗎？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('刪除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await context.read<ApiService>().deleteDiaryEntry(id);
        _loadData();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('刪除失敗: $e')),
          );
        }
      }
    }
  }

  IconData _getTradeTypeIcon(String type) {
    switch (type) {
      case 'buy': return Icons.add_circle;
      case 'sell': return Icons.remove_circle;
      case 'watch': return Icons.visibility;
      default: return Icons.note;
    }
  }

  Color _getTradeTypeColor(String type) {
    switch (type) {
      case 'buy': return Colors.red;
      case 'sell': return Colors.green;
      case 'watch': return Colors.blue;
      default: return Colors.grey;
    }
  }

  String _getTradeTypeText(String type) {
    switch (type) {
      case 'buy': return '買入';
      case 'sell': return '賣出';
      case 'watch': return '觀察';
      default: return '筆記';
    }
  }

  Color _getEmotionColor(String emotion) {
    switch (emotion) {
      case 'confident': return Colors.green;
      case 'calm': return Colors.blue;
      case 'anxious': return Colors.orange;
      case 'greedy': return Colors.red;
      case 'fearful': return Colors.purple;
      default: return Colors.grey;
    }
  }

  String _getEmotionText(String emotion) {
    switch (emotion) {
      case 'confident': return '自信';
      case 'calm': return '冷靜';
      case 'anxious': return '焦慮';
      case 'greedy': return '貪婪';
      case 'fearful': return '恐懼';
      default: return emotion;
    }
  }

  Widget _buildEmotionPerformanceCard() {
    // 按情緒分組計算平均損益
    final Map<String, List<double>> emotionPnls = {};
    for (final entry in _entries) {
      final emotion = entry['emotion'] as String?;
      final pnl = (entry['pnl'] as num?)?.toDouble();
      if (emotion != null && pnl != null) {
        emotionPnls.putIfAbsent(emotion, () => []).add(pnl);
      }
    }

    if (emotionPnls.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.psychology, size: 20, color: Colors.purple),
                SizedBox(width: 8),
                Text('情緒 vs 績效', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 4),
            Text('了解哪種情緒下交易表現最好', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
            const Divider(),
            ...emotionPnls.entries.map((e) {
              final avg = e.value.reduce((a, b) => a + b) / e.value.length;
              final winCount = e.value.where((p) => p > 0).length;
              final winRate = e.value.isNotEmpty ? winCount / e.value.length * 100 : 0.0;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  children: [
                    Container(
                      width: 8, height: 8,
                      decoration: BoxDecoration(
                        color: _getEmotionColor(e.key),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      width: 50,
                      child: Text(_getEmotionText(e.key), style: const TextStyle(fontSize: 13)),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '平均 ${avg >= 0 ? "+" : ""}\$${avg.toStringAsFixed(0)}',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: avg >= 0 ? Colors.red : Colors.green,
                            ),
                          ),
                          Text(
                            '勝率 ${winRate.toStringAsFixed(0)}% (${e.value.length}筆)',
                            style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildStreakCard() {
    // 計算連勝/連敗
    int currentStreak = 0;
    bool? lastWin;
    int maxWinStreak = 0;
    int maxLossStreak = 0;
    int tempWin = 0;
    int tempLoss = 0;

    final sorted = _entries
        .where((e) => e['pnl'] != null)
        .toList()
      ..sort((a, b) {
        final da = a['trade_date'] as String? ?? '';
        final db = b['trade_date'] as String? ?? '';
        return da.compareTo(db);
      });

    for (final entry in sorted) {
      final pnl = (entry['pnl'] as num).toDouble();
      final isWin = pnl > 0;

      if (isWin) {
        tempWin++;
        tempLoss = 0;
        if (tempWin > maxWinStreak) maxWinStreak = tempWin;
      } else {
        tempLoss++;
        tempWin = 0;
        if (tempLoss > maxLossStreak) maxLossStreak = tempLoss;
      }
    }

    // 計算目前連續狀態
    if (sorted.isNotEmpty) {
      final lastPnl = (sorted.last['pnl'] as num).toDouble();
      lastWin = lastPnl > 0;
      currentStreak = 1;
      for (int i = sorted.length - 2; i >= 0; i--) {
        final pnl = (sorted[i]['pnl'] as num).toDouble();
        if ((pnl > 0) == lastWin) {
          currentStreak++;
        } else {
          break;
        }
      }
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.local_fire_department, size: 20, color: Colors.orange),
                SizedBox(width: 8),
                Text('連續紀錄', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            const Divider(),
            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    '目前',
                    lastWin == null
                        ? '-'
                        : '${lastWin ? "連勝" : "連敗"} $currentStreak',
                    lastWin == true ? Colors.red : lastWin == false ? Colors.green : Colors.grey,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(child: _buildStatCard('最長連勝', '$maxWinStreak', Colors.red)),
                const SizedBox(width: 8),
                Expanded(child: _buildStatCard('最長連敗', '$maxLossStreak', Colors.green)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _AddDiarySheet extends StatefulWidget {
  final VoidCallback onCreated;

  const _AddDiarySheet({required this.onCreated});

  @override
  State<_AddDiarySheet> createState() => _AddDiarySheetState();
}

class _AddDiarySheetState extends State<_AddDiarySheet> {
  final _stockIdController = TextEditingController();
  final _notesController = TextEditingController();
  final _lessonController = TextEditingController();
  final _priceController = TextEditingController();
  final _quantityController = TextEditingController();
  final _pnlController = TextEditingController();
  final _tagsController = TextEditingController();
  String _tradeType = 'note';
  String? _emotion;
  int _rating = 3;
  bool _isLoading = false;

  @override
  void dispose() {
    _stockIdController.dispose();
    _notesController.dispose();
    _lessonController.dispose();
    _priceController.dispose();
    _quantityController.dispose();
    _pnlController.dispose();
    _tagsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text('新增交易日記',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // 類型選擇
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'buy', label: Text('買入'), icon: Icon(Icons.add_circle, size: 16)),
                ButtonSegment(value: 'sell', label: Text('賣出'), icon: Icon(Icons.remove_circle, size: 16)),
                ButtonSegment(value: 'watch', label: Text('觀察'), icon: Icon(Icons.visibility, size: 16)),
                ButtonSegment(value: 'note', label: Text('筆記'), icon: Icon(Icons.note, size: 16)),
              ],
              selected: {_tradeType},
              onSelectionChanged: (set) => setState(() => _tradeType = set.first),
            ),
            const SizedBox(height: 16),
            // 股票代碼 + 價格
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _stockIdController,
                    decoration: const InputDecoration(
                      labelText: '股票代碼 (選填)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _priceController,
                    decoration: const InputDecoration(
                      labelText: '成交價',
                      border: OutlineInputBorder(),
                      prefixText: '\$ ',
                    ),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _quantityController,
                    decoration: const InputDecoration(
                      labelText: '數量',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _pnlController,
                    decoration: const InputDecoration(
                      labelText: '盈虧',
                      border: OutlineInputBorder(),
                      prefixText: '\$ ',
                    ),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // 情緒選擇
            const Text('交易時的情緒', style: TextStyle(fontWeight: FontWeight.w500)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: ['confident', 'calm', 'anxious', 'greedy', 'fearful'].map((e) {
                final selected = _emotion == e;
                final labels = {
                  'confident': '自信', 'calm': '冷靜', 'anxious': '焦慮',
                  'greedy': '貪婪', 'fearful': '恐懼',
                };
                return ChoiceChip(
                  label: Text(labels[e] ?? e),
                  selected: selected,
                  onSelected: (_) => setState(() => _emotion = selected ? null : e),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            // 自評
            Row(
              children: [
                const Text('交易評分', style: TextStyle(fontWeight: FontWeight.w500)),
                const SizedBox(width: 12),
                ...List.generate(5, (i) => GestureDetector(
                  onTap: () => setState(() => _rating = i + 1),
                  child: Icon(
                    i < _rating ? Icons.star : Icons.star_border,
                    color: Colors.amber,
                    size: 28,
                  ),
                )),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _notesController,
              decoration: const InputDecoration(
                labelText: '交易筆記',
                border: OutlineInputBorder(),
                hintText: '記錄你的交易想法...',
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _lessonController,
              decoration: const InputDecoration(
                labelText: '交易教訓 (選填)',
                border: OutlineInputBorder(),
                hintText: '這次交易學到了什麼？',
              ),
              maxLines: 2,
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _tagsController,
              decoration: const InputDecoration(
                labelText: '標籤 (逗號分隔)',
                border: OutlineInputBorder(),
                hintText: '例如: 追高, 停損, 波段',
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 20, height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('儲存日記'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    setState(() => _isLoading = true);

    try {
      final data = <String, dynamic>{
        'trade_type': _tradeType,
        'notes': _notesController.text.isNotEmpty ? _notesController.text : null,
        'rating': _rating,
      };

      if (_stockIdController.text.isNotEmpty) data['stock_id'] = _stockIdController.text;
      if (_priceController.text.isNotEmpty) data['price'] = double.tryParse(_priceController.text);
      if (_quantityController.text.isNotEmpty) data['quantity'] = int.tryParse(_quantityController.text);
      if (_pnlController.text.isNotEmpty) data['pnl'] = double.tryParse(_pnlController.text);
      if (_emotion != null) data['emotion'] = _emotion;
      if (_lessonController.text.isNotEmpty) data['lesson_learned'] = _lessonController.text;
      if (_tagsController.text.isNotEmpty) data['tags'] = _tagsController.text;

      await context.read<ApiService>().createDiaryEntry(data);

      if (mounted) {
        Navigator.pop(context);
        widget.onCreated();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('日記已儲存')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('儲存失敗: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }
}
