import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/portfolio.dart';

class PortfolioDetailScreen extends StatefulWidget {
  final int portfolioId;

  const PortfolioDetailScreen({super.key, required this.portfolioId});

  @override
  State<PortfolioDetailScreen> createState() => _PortfolioDetailScreenState();
}

class _PortfolioDetailScreenState extends State<PortfolioDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  PortfolioDetail? _detail;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadDetail();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final detail = await apiService.getPortfolioDetail(widget.portfolioId);
      setState(() {
        _detail = detail;
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
    return Scaffold(
      appBar: AppBar(
        title: Text(_detail?.name ?? '投資組合'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDetail,
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'delete') {
                _confirmDelete();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'delete',
                child: Row(
                  children: [
                    Icon(Icons.delete, color: Colors.red),
                    SizedBox(width: 8),
                    Text('刪除組合', style: TextStyle(color: Colors.red)),
                  ],
                ),
              ),
            ],
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '持股'),
            Tab(text: '配置'),
            Tab(text: '績效'),
          ],
        ),
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddHoldingDialog,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text('載入失敗: $_error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadDetail,
              child: const Text('重試'),
            ),
          ],
        ),
      );
    }

    if (_detail == null) {
      return const Center(child: Text('無數據'));
    }

    return Column(
      children: [
        _buildSummaryCard(),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildHoldingsTab(),
              _buildAllocationTab(),
              _buildPerformanceTab(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryCard() {
    final isProfit = _detail!.totalPnl >= 0;
    final pnlColor = isProfit ? Colors.green : Colors.red;

    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildSummaryItem('總成本', _formatCurrency(_detail!.totalCost)),
            _buildSummaryItem('市值', _formatCurrency(_detail!.totalValue)),
            _buildSummaryItem(
              '損益',
              '${isProfit ? '+' : ''}${_formatCurrency(_detail!.totalPnl)}',
              valueColor: pnlColor,
            ),
            _buildSummaryItem(
              '報酬率',
              '${isProfit ? '+' : ''}${_detail!.totalPnlPercent.toStringAsFixed(2)}%',
              valueColor: pnlColor,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value, {Color? valueColor}) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: Colors.grey),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: valueColor,
          ),
        ),
      ],
    );
  }

  Widget _buildHoldingsTab() {
    if (_detail!.holdings.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inventory_2_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('尚無持股'),
            SizedBox(height: 8),
            Text(
              '點擊右下角按鈕新增持股',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadDetail,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: _detail!.holdings.length,
        itemBuilder: (context, index) {
          return _buildHoldingCard(_detail!.holdings[index]);
        },
      ),
    );
  }

  Widget _buildHoldingCard(PortfolioHolding holding) {
    final isProfit = (holding.unrealizedPnl ?? 0) >= 0;
    final pnlColor = isProfit ? Colors.green : Colors.red;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onLongPress: () => _showHoldingActions(holding),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        holding.stockName ?? holding.stockId,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        holding.stockId,
                        style: const TextStyle(
                          fontSize: 12,
                          color: Colors.grey,
                        ),
                      ),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      if (holding.currentPrice != null)
                        Text(
                          '\$${holding.currentPrice!.toStringAsFixed(2)}',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      if (holding.unrealizedPnlPercent != null)
                        Text(
                          '${isProfit ? '+' : ''}${holding.unrealizedPnlPercent!.toStringAsFixed(2)}%',
                          style: TextStyle(
                            fontSize: 14,
                            color: pnlColor,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                    ],
                  ),
                ],
              ),
              const Divider(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildHoldingInfo('持股', '${holding.quantity} 股'),
                  _buildHoldingInfo('成本', '\$${holding.avgCost.toStringAsFixed(2)}'),
                  _buildHoldingInfo(
                    '市值',
                    holding.marketValue != null
                        ? '\$${holding.marketValue!.toStringAsFixed(0)}'
                        : '-',
                  ),
                  _buildHoldingInfo(
                    '損益',
                    holding.unrealizedPnl != null
                        ? '${isProfit ? '+' : ''}\$${holding.unrealizedPnl!.toStringAsFixed(0)}'
                        : '-',
                    valueColor: pnlColor,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHoldingInfo(String label, String value, {Color? valueColor}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: Colors.grey),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: valueColor,
          ),
        ),
      ],
    );
  }

  Widget _buildAllocationTab() {
    if (_detail!.holdings.isEmpty) {
      return const Center(child: Text('無持股數據'));
    }

    // 計算各股票的配置比例
    final allocations = _detail!.holdings
        .where((h) => h.marketValue != null && h.marketValue! > 0)
        .map((h) => {
              'name': h.stockName ?? h.stockId,
              'value': h.marketValue!,
              'weight': h.marketValue! / _detail!.totalValue * 100,
            })
        .toList();

    allocations.sort((a, b) => (b['weight'] as double).compareTo(a['weight'] as double));

    final colors = [
      Colors.blue,
      Colors.green,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.pink,
      Colors.indigo,
      Colors.amber,
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // 簡單的條狀圖
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '持股配置',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ...allocations.asMap().entries.map((entry) {
                    final index = entry.key;
                    final item = entry.value;
                    final color = colors[index % colors.length];

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    width: 12,
                                    height: 12,
                                    decoration: BoxDecoration(
                                      color: color,
                                      borderRadius: BorderRadius.circular(2),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(item['name'] as String),
                                ],
                              ),
                              Text(
                                '${(item['weight'] as double).toStringAsFixed(1)}%',
                                style: const TextStyle(fontWeight: FontWeight.w500),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: (item['weight'] as double) / 100,
                              backgroundColor: Colors.grey.shade200,
                              valueColor: AlwaysStoppedAnimation<Color>(color),
                              minHeight: 8,
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
        ],
      ),
    );
  }

  Widget _buildPerformanceTab() {
    if (_detail == null) return const Center(child: Text('無數據'));

    final totalPnl = _detail!.totalPnl;
    final totalPnlPct = _detail!.totalPnlPercent;
    final isProfit = totalPnl >= 0;
    final pnlColor = isProfit ? Colors.green : Colors.red;

    // 計算各持股的已實現/未實現損益
    double totalUnrealized = 0;
    for (final h in _detail!.holdings) {
      totalUnrealized += h.unrealizedPnl ?? 0;
    }

    // 計算集中度（最大持股佔比）
    double maxWeight = 0;
    String maxHolding = '';
    if (_detail!.totalValue > 0) {
      for (final h in _detail!.holdings) {
        final weight = (h.marketValue ?? 0) / _detail!.totalValue;
        if (weight > maxWeight) {
          maxWeight = weight;
          maxHolding = h.stockName ?? h.stockId;
        }
      }
    }

    // 計算勝率
    int winCount = 0;
    int totalCount = 0;
    for (final h in _detail!.holdings) {
      if (h.unrealizedPnl != null) {
        totalCount++;
        if (h.unrealizedPnl! > 0) winCount++;
      }
    }
    final winRate = totalCount > 0 ? winCount / totalCount * 100 : 0.0;

    return RefreshIndicator(
      onRefresh: _loadDetail,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 總報酬卡片
            Card(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      pnlColor.withAlpha(30),
                      pnlColor.withAlpha(10),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  children: [
                    const Text('總報酬', style: TextStyle(fontSize: 14, color: Colors.grey)),
                    const SizedBox(height: 8),
                    Text(
                      '${isProfit ? '+' : ''}${_formatCurrency(totalPnl)}',
                      style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: pnlColor),
                    ),
                    Text(
                      '${isProfit ? '+' : ''}${totalPnlPct.toStringAsFixed(2)}%',
                      style: TextStyle(fontSize: 18, color: pnlColor),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // 績效指標
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('績效指標', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const Divider(),
                    _buildPerfRow('未實現損益', '${totalUnrealized >= 0 ? '+' : ''}${_formatCurrency(totalUnrealized)}',
                        color: totalUnrealized >= 0 ? Colors.green : Colors.red),
                    _buildPerfRow('持股勝率', '${winRate.toStringAsFixed(1)}%',
                        color: winRate >= 50 ? Colors.green : Colors.red),
                    _buildPerfRow('持股數量', '${_detail!.holdings.length} 檔'),
                    if (maxHolding.isNotEmpty)
                      _buildPerfRow('最大持股', '$maxHolding (${(maxWeight * 100).toStringAsFixed(1)}%)'),
                    _buildPerfRow('集中度', maxWeight > 0.5
                        ? '高度集中'
                        : maxWeight > 0.3
                            ? '中度集中'
                            : '分散',
                        color: maxWeight > 0.5 ? Colors.red : Colors.green),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // 各持股損益排行
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('持股損益排行', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const Divider(),
                    ..._detail!.holdings
                        .where((h) => h.unrealizedPnl != null)
                        .toList()
                      ..sort((a, b) => (b.unrealizedPnl ?? 0).compareTo(a.unrealizedPnl ?? 0)),
                    ..._detail!.holdings
                        .where((h) => h.unrealizedPnl != null)
                        .toList()
                        .map((h) {
                      final pnl = h.unrealizedPnl ?? 0;
                      final pct = h.unrealizedPnlPercent ?? 0;
                      final isHoldingProfit = pnl >= 0;
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Row(
                          children: [
                            Expanded(
                              flex: 3,
                              child: Text(h.stockName ?? h.stockId,
                                  style: const TextStyle(fontWeight: FontWeight.w500)),
                            ),
                            Expanded(
                              flex: 2,
                              child: Text(
                                '${isHoldingProfit ? '+' : ''}\$${pnl.toStringAsFixed(0)}',
                                textAlign: TextAlign.right,
                                style: TextStyle(
                                  color: isHoldingProfit ? Colors.green : Colors.red,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            SizedBox(
                              width: 70,
                              child: Text(
                                '${isHoldingProfit ? '+' : ''}${pct.toStringAsFixed(1)}%',
                                textAlign: TextAlign.right,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: isHoldingProfit ? Colors.green : Colors.red,
                                ),
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
          ],
        ),
      ),
    );
  }

  Widget _buildPerfRow(String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  String _formatCurrency(double value) {
    if (value >= 10000) {
      return '\$${(value / 10000).toStringAsFixed(2)}萬';
    }
    return '\$${value.toStringAsFixed(0)}';
  }

  void _showAddHoldingDialog() {
    final stockIdController = TextEditingController();
    final quantityController = TextEditingController();
    final costController = TextEditingController();
    DateTime selectedDate = DateTime.now();

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('新增持股'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: stockIdController,
                  decoration: const InputDecoration(
                    labelText: '股票代碼',
                    hintText: '例如：2330',
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: quantityController,
                  decoration: const InputDecoration(
                    labelText: '持股數量',
                    hintText: '例如：1000',
                  ),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: costController,
                  decoration: const InputDecoration(
                    labelText: '平均成本',
                    hintText: '例如：500.00',
                  ),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                ),
                const SizedBox(height: 16),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('買入日期'),
                  subtitle: Text(
                    '${selectedDate.year}/${selectedDate.month}/${selectedDate.day}',
                  ),
                  trailing: const Icon(Icons.calendar_today),
                  onTap: () async {
                    final date = await showDatePicker(
                      context: context,
                      initialDate: selectedDate,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now(),
                    );
                    if (date != null) {
                      setDialogState(() {
                        selectedDate = date;
                      });
                    }
                  },
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('取消'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (stockIdController.text.isEmpty ||
                    quantityController.text.isEmpty ||
                    costController.text.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('請填寫所有必要欄位')),
                  );
                  return;
                }

                try {
                  final apiService =
                      Provider.of<ApiService>(context, listen: false);
                  await apiService.addPortfolioHolding(
                    widget.portfolioId,
                    stockIdController.text,
                    int.parse(quantityController.text),
                    double.parse(costController.text),
                    selectedDate,
                  );
                  if (context.mounted) {
                    Navigator.pop(context);
                    _loadDetail();
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('新增失敗: $e')),
                    );
                  }
                }
              },
              child: const Text('新增'),
            ),
          ],
        ),
      ),
    );
  }

  void _showHoldingActions(PortfolioHolding holding) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.delete, color: Colors.red),
              title: const Text('刪除持股', style: TextStyle(color: Colors.red)),
              onTap: () {
                Navigator.pop(context);
                _confirmDeleteHolding(holding);
              },
            ),
          ],
        ),
      ),
    );
  }

  void _confirmDeleteHolding(PortfolioHolding holding) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('確認刪除'),
        content: Text('確定要刪除 ${holding.stockName ?? holding.stockId} 的持股嗎？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              try {
                final apiService =
                    Provider.of<ApiService>(context, listen: false);
                await apiService.deletePortfolioHolding(holding.id);
                if (context.mounted) {
                  Navigator.pop(context);
                  _loadDetail();
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('刪除失敗: $e')),
                  );
                }
              }
            },
            child: const Text('刪除'),
          ),
        ],
      ),
    );
  }

  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('確認刪除'),
        content: Text('確定要刪除「${_detail?.name}」投資組合嗎？此操作無法復原。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              try {
                final apiService =
                    Provider.of<ApiService>(context, listen: false);
                await apiService.deletePortfolio(widget.portfolioId);
                if (context.mounted) {
                  Navigator.pop(context);
                  Navigator.pop(context);
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('刪除失敗: $e')),
                  );
                }
              }
            },
            child: const Text('刪除'),
          ),
        ],
      ),
    );
  }
}
