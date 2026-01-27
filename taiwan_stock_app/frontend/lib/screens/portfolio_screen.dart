import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/portfolio.dart';
import 'portfolio_detail_screen.dart';

class PortfolioScreen extends StatefulWidget {
  const PortfolioScreen({super.key});

  @override
  State<PortfolioScreen> createState() => _PortfolioScreenState();
}

class _PortfolioScreenState extends State<PortfolioScreen> {
  List<PortfolioSummary> _portfolios = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPortfolios();
  }

  Future<void> _loadPortfolios() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final response = await apiService.getPortfolios();
      setState(() {
        _portfolios = response;
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
        title: const Text('投資組合'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadPortfolios,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateDialog,
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
              onPressed: _loadPortfolios,
              child: const Text('重試'),
            ),
          ],
        ),
      );
    }

    if (_portfolios.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.pie_chart_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text('尚無投資組合'),
            const SizedBox(height: 8),
            const Text(
              '點擊右下角按鈕建立您的第一個投資組合',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadPortfolios,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _portfolios.length,
        itemBuilder: (context, index) {
          return _buildPortfolioCard(_portfolios[index]);
        },
      ),
    );
  }

  Widget _buildPortfolioCard(PortfolioSummary portfolio) {
    final isProfit = portfolio.totalPnl >= 0;
    final pnlColor = isProfit ? Colors.green : Colors.red;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _navigateToDetail(portfolio),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    portfolio.name,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: pnlColor.withAlpha(26),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      '${isProfit ? '+' : ''}${portfolio.totalPnlPercent.toStringAsFixed(2)}%',
                      style: TextStyle(
                        color: pnlColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildInfoColumn('總成本', _formatCurrency(portfolio.totalCost)),
                  _buildInfoColumn('市值', _formatCurrency(portfolio.totalValue)),
                  _buildInfoColumn(
                    '損益',
                    '${isProfit ? '+' : ''}${_formatCurrency(portfolio.totalPnl)}',
                    valueColor: pnlColor,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.list, size: 16, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    '${portfolio.holdingsCount} 檔持股',
                    style: const TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoColumn(String label, String value, {Color? valueColor}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.grey,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: valueColor,
          ),
        ),
      ],
    );
  }

  String _formatCurrency(double value) {
    if (value >= 10000) {
      return '\$${(value / 10000).toStringAsFixed(2)}萬';
    }
    return '\$${value.toStringAsFixed(0)}';
  }

  void _navigateToDetail(PortfolioSummary portfolio) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PortfolioDetailScreen(portfolioId: portfolio.id),
      ),
    ).then((_) => _loadPortfolios());
  }

  void _showCreateDialog() {
    final nameController = TextEditingController();
    final descController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('建立投資組合'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(
                labelText: '組合名稱',
                hintText: '例如：長期投資組合',
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: descController,
              decoration: const InputDecoration(
                labelText: '描述 (選填)',
                hintText: '組合的投資目標或策略',
              ),
              maxLines: 2,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (nameController.text.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('請輸入組合名稱')),
                );
                return;
              }

              try {
                final apiService =
                    Provider.of<ApiService>(context, listen: false);
                await apiService.createPortfolio(
                  nameController.text,
                  descController.text.isEmpty ? null : descController.text,
                );
                if (context.mounted) {
                  Navigator.pop(context);
                  _loadPortfolios();
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('建立失敗: $e')),
                  );
                }
              }
            },
            child: const Text('建立'),
          ),
        ],
      ),
    );
  }
}
