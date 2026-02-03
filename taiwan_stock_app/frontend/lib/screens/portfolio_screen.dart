import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/portfolio.dart';
import '../providers/portfolio_provider.dart';

class PortfolioScreen extends StatefulWidget {
  const PortfolioScreen({super.key});

  @override
  State<PortfolioScreen> createState() => _PortfolioScreenState();
}

class _PortfolioScreenState extends State<PortfolioScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<PortfolioProvider>();
      provider.loadPortfolios().then((_) {
        if (provider.portfolios.isNotEmpty && provider.selectedPortfolio == null) {
          provider.selectPortfolio(provider.portfolios.first.id);
        }
      });
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('投資組合'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<PortfolioProvider>().refresh(),
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showCreatePortfolioDialog(context),
          ),
        ],
      ),
      body: Consumer<PortfolioProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.portfolios.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.portfolios.isEmpty) {
            return _buildEmptyState();
          }

          return Column(
            children: [
              _buildPortfolioSelector(provider),
              if (provider.selectedPortfolio != null) ...[
                _buildSummaryCard(provider),
                TabBar(
                  controller: _tabController,
                  tabs: const [
                    Tab(text: '持倉'),
                    Tab(text: '交易記錄'),
                    Tab(text: '配置圖'),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildPositionsList(provider),
                      _buildTransactionsList(provider),
                      _buildAllocationChart(provider),
                    ],
                  ),
                ),
              ],
            ],
          );
        },
      ),
      floatingActionButton: Consumer<PortfolioProvider>(
        builder: (context, provider, child) {
          if (provider.selectedPortfolio == null) return const SizedBox();
          return FloatingActionButton.extended(
            onPressed: () => _showAddTransactionDialog(context),
            icon: const Icon(Icons.add),
            label: const Text('新增交易'),
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.account_balance_wallet_outlined,
            size: 80,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            '尚無投資組合',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '點擊右上角 + 創建您的第一個投資組合',
            style: TextStyle(
              color: Colors.grey[500],
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => _showCreatePortfolioDialog(context),
            icon: const Icon(Icons.add),
            label: const Text('創建投資組合'),
          ),
        ],
      ),
    );
  }

  Widget _buildPortfolioSelector(PortfolioProvider provider) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: DropdownButtonFormField<int>(
        value: provider.selectedPortfolio?.id,
        decoration: const InputDecoration(
          labelText: '選擇投資組合',
          border: OutlineInputBorder(),
          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
        items: provider.portfolios.map((p) {
          return DropdownMenuItem<int>(
            value: p.id,
            child: Text(p.name),
          );
        }).toList(),
        onChanged: (value) {
          if (value != null) {
            provider.selectPortfolio(value);
          }
        },
      ),
    );
  }

  Widget _buildSummaryCard(PortfolioProvider provider) {
    final summary = provider.summary;
    final portfolio = provider.selectedPortfolio!;
    final isProfitable = (summary?.totalPnl ?? 0) >= 0;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isProfitable
              ? [Colors.green.shade700, Colors.green.shade500]
              : [Colors.red.shade700, Colors.red.shade500],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: (isProfitable ? Colors.green : Colors.red).withAlpha(80),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                portfolio.name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(50),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${summary?.positionsCount ?? 0} 檔持股',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            '\$${_formatNumber(summary?.totalValue ?? 0)}',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 32,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Icon(
                isProfitable ? Icons.trending_up : Icons.trending_down,
                color: Colors.white,
                size: 20,
              ),
              const SizedBox(width: 4),
              Text(
                '${isProfitable ? '+' : ''}\$${_formatNumber(summary?.totalPnl ?? 0)}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(50),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '${isProfitable ? '+' : ''}${(summary?.totalPnlPercent ?? 0).toStringAsFixed(2)}%',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildStatItem('初始資金', '\$${_formatNumber(portfolio.initialCapital)}'),
              ),
              Expanded(
                child: _buildStatItem('現金餘額', '\$${_formatNumber(summary?.cashBalance ?? 0)}'),
              ),
              Expanded(
                child: _buildStatItem(
                  '勝率',
                  '${summary?.winRate.toStringAsFixed(1) ?? 0}%',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value) {
    return Column(
      children: [
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withAlpha(180),
            fontSize: 12,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildPositionsList(PortfolioProvider provider) {
    if (provider.positions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inventory_2_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text('暫無持倉', style: TextStyle(color: Colors.grey[600])),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: provider.positions.length,
      itemBuilder: (context, index) {
        final position = provider.positions[index];
        return _buildPositionCard(position);
      },
    );
  }

  Widget _buildPositionCard(Position position) {
    final isProfitable = position.isProfitable;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          Navigator.pushNamed(context, '/stock-detail', arguments: position.stockId);
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${position.stockId} ${position.stockName}',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${position.quantity} 股',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '\$${position.currentPrice.toStringAsFixed(2)}',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                      ),
                      Row(
                        children: [
                          Icon(
                            isProfitable ? Icons.arrow_upward : Icons.arrow_downward,
                            size: 14,
                            color: isProfitable ? Colors.green : Colors.red,
                          ),
                          Text(
                            '${isProfitable ? '+' : ''}${position.unrealizedPnlPercent.toStringAsFixed(2)}%',
                            style: TextStyle(
                              color: isProfitable ? Colors.green : Colors.red,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
              const Divider(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildPositionInfo('成本', '\$${position.avgCost.toStringAsFixed(2)}'),
                  _buildPositionInfo('市值', '\$${_formatNumber(position.marketValue)}'),
                  _buildPositionInfo(
                    '損益',
                    '${isProfitable ? '+' : ''}\$${_formatNumber(position.unrealizedPnl)}',
                    color: isProfitable ? Colors.green : Colors.red,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPositionInfo(String label, String value, {Color? color}) {
    return Column(
      children: [
        Text(
          label,
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 12,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.w500,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildTransactionsList(PortfolioProvider provider) {
    if (provider.transactions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.receipt_long_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text('暫無交易記錄', style: TextStyle(color: Colors.grey[600])),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: provider.transactions.length,
      itemBuilder: (context, index) {
        final tx = provider.transactions[index];
        return _buildTransactionCard(tx);
      },
    );
  }

  Widget _buildTransactionCard(Transaction tx) {
    final isBuy = tx.isBuy;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: (isBuy ? Colors.green : Colors.red).withAlpha(30),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            isBuy ? Icons.add : Icons.remove,
            color: isBuy ? Colors.green : Colors.red,
          ),
        ),
        title: Text(
          '${tx.stockId} ${tx.stockName}',
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        subtitle: Text(
          '${isBuy ? '買入' : '賣出'} ${tx.quantity} 股 @ \$${tx.price.toStringAsFixed(2)}',
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '\$${_formatNumber(tx.totalAmount)}',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: isBuy ? Colors.green : Colors.red,
              ),
            ),
            Text(
              _formatDate(tx.transactionDate),
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAllocationChart(PortfolioProvider provider) {
    if (provider.allocations.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.pie_chart_outline, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text('暫無配置數據', style: TextStyle(color: Colors.grey[600])),
          ],
        ),
      );
    }

    final colors = [
      Colors.blue,
      Colors.red,
      Colors.green,
      Colors.orange,
      Colors.purple,
      Colors.teal,
      Colors.pink,
      Colors.indigo,
    ];

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          SizedBox(
            height: 200,
            child: PieChart(
              PieChartData(
                sections: provider.allocations.asMap().entries.map((entry) {
                  final index = entry.key;
                  final allocation = entry.value;
                  return PieChartSectionData(
                    value: allocation.weight,
                    title: '${allocation.weight.toStringAsFixed(1)}%',
                    color: colors[index % colors.length],
                    radius: 80,
                    titleStyle: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  );
                }).toList(),
                centerSpaceRadius: 40,
                sectionsSpace: 2,
              ),
            ),
          ),
          const SizedBox(height: 24),
          Expanded(
            child: ListView.builder(
              itemCount: provider.allocations.length,
              itemBuilder: (context, index) {
                final allocation = provider.allocations[index];
                return ListTile(
                  leading: Container(
                    width: 16,
                    height: 16,
                    decoration: BoxDecoration(
                      color: colors[index % colors.length],
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  title: Text('${allocation.stockId} ${allocation.stockName}'),
                  trailing: Text(
                    '${allocation.weight.toStringAsFixed(1)}%',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  String _formatNumber(double value) {
    if (value.abs() >= 1000000) {
      return '${(value / 1000000).toStringAsFixed(2)}M';
    } else if (value.abs() >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}K';
    }
    return value.toStringAsFixed(2);
  }

  String _formatDate(DateTime dt) {
    return '${dt.month}/${dt.day}';
  }

  void _showCreatePortfolioDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => const CreatePortfolioSheet(),
    );
  }

  void _showAddTransactionDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => const AddTransactionSheet(),
    );
  }
}

class CreatePortfolioSheet extends StatefulWidget {
  const CreatePortfolioSheet({super.key});

  @override
  State<CreatePortfolioSheet> createState() => _CreatePortfolioSheetState();
}

class _CreatePortfolioSheetState extends State<CreatePortfolioSheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _capitalController = TextEditingController(text: '1000000');
  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _capitalController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Container(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Text(
                    '創建投資組合',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: '組合名稱',
                  hintText: '例如: 主力投資組合',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) return '請輸入組合名稱';
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  labelText: '描述 (選填)',
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _capitalController,
                decoration: const InputDecoration(
                  labelText: '初始資金',
                  border: OutlineInputBorder(),
                  prefixText: '\$ ',
                ),
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) return '請輸入初始資金';
                  if (double.tryParse(value) == null) return '請輸入有效數字';
                  return null;
                },
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _createPortfolio,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('創建'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _createPortfolio() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final request = CreatePortfolioRequest(
        name: _nameController.text,
        description: _descriptionController.text.isEmpty
            ? null
            : _descriptionController.text,
        initialCapital: double.parse(_capitalController.text),
      );

      final portfolio = await context.read<PortfolioProvider>().createPortfolio(request);
      await context.read<PortfolioProvider>().selectPortfolio(portfolio.id);

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('投資組合已創建')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('創建失敗: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }
}

class AddTransactionSheet extends StatefulWidget {
  const AddTransactionSheet({super.key});

  @override
  State<AddTransactionSheet> createState() => _AddTransactionSheetState();
}

class _AddTransactionSheetState extends State<AddTransactionSheet> {
  final _formKey = GlobalKey<FormState>();
  final _stockIdController = TextEditingController();
  final _stockNameController = TextEditingController();
  final _quantityController = TextEditingController();
  final _priceController = TextEditingController();
  TransactionType _transactionType = TransactionType.buy;
  bool _isLoading = false;

  @override
  void dispose() {
    _stockIdController.dispose();
    _stockNameController.dispose();
    _quantityController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Container(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Text(
                    '新增交易',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              SegmentedButton<TransactionType>(
                segments: const [
                  ButtonSegment(
                    value: TransactionType.buy,
                    label: Text('買入'),
                    icon: Icon(Icons.add),
                  ),
                  ButtonSegment(
                    value: TransactionType.sell,
                    label: Text('賣出'),
                    icon: Icon(Icons.remove),
                  ),
                ],
                selected: {_transactionType},
                onSelectionChanged: (set) {
                  setState(() => _transactionType = set.first);
                },
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: TextFormField(
                      controller: _stockIdController,
                      decoration: const InputDecoration(
                        labelText: '股票代碼',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v?.isEmpty ?? true ? '必填' : null,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 3,
                    child: TextFormField(
                      controller: _stockNameController,
                      decoration: const InputDecoration(
                        labelText: '股票名稱',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v?.isEmpty ?? true ? '必填' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _quantityController,
                      decoration: const InputDecoration(
                        labelText: '數量 (股)',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                      validator: (v) {
                        if (v?.isEmpty ?? true) return '必填';
                        if (int.tryParse(v!) == null) return '無效';
                        return null;
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _priceController,
                      decoration: const InputDecoration(
                        labelText: '成交價',
                        border: OutlineInputBorder(),
                        prefixText: '\$ ',
                      ),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      validator: (v) {
                        if (v?.isEmpty ?? true) return '必填';
                        if (double.tryParse(v!) == null) return '無效';
                        return null;
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _addTransaction,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: _transactionType == TransactionType.buy
                        ? Colors.green
                        : Colors.red,
                    foregroundColor: Colors.white,
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(_transactionType == TransactionType.buy ? '確認買入' : '確認賣出'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _addTransaction() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final request = CreateTransactionRequest(
        stockId: _stockIdController.text,
        stockName: _stockNameController.text,
        transactionType: _transactionType,
        quantity: int.parse(_quantityController.text),
        price: double.parse(_priceController.text),
      );

      await context.read<PortfolioProvider>().addTransaction(request);

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              '${_transactionType == TransactionType.buy ? '買入' : '賣出'}成功',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('交易失敗: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }
}
