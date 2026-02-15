import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/fundamental.dart';

class FinancialStatementsView extends StatefulWidget {
  final String stockId;
  final String market;

  const FinancialStatementsView({
    super.key,
    required this.stockId,
    this.market = 'TW',
  });

  @override
  State<FinancialStatementsView> createState() => _FinancialStatementsViewState();
}

class _FinancialStatementsViewState extends State<FinancialStatementsView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  FinancialStatements? _data;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() { _isLoading = true; _error = null; });
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final data = await api.getFinancialStatements(widget.stockId, market: widget.market);
      if (mounted) setState(() { _data = data; _isLoading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _isLoading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.grey),
            const SizedBox(height: 8),
            Text('載入財報失敗', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            ElevatedButton(onPressed: _loadData, child: const Text('重試')),
          ],
        ),
      );
    }
    if (_data == null) return const Center(child: Text('無財報資料'));

    return Column(
      children: [
        TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '損益表'),
            Tab(text: '資產負債'),
            Tab(text: '現金流'),
          ],
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildIncomeStatementList(_data!.incomeStatement),
              _buildBalanceSheetList(_data!.balanceSheet),
              _buildCashFlowList(_data!.cashFlow),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildIncomeStatementList(List<IncomeStatementItem> items) {
    if (items.isEmpty) return const Center(child: Text('暫無資料'));
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.period, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                _buildRow('營收', item.revenue),
                _buildRow('營業成本', item.costOfRevenue),
                _buildRow('毛利', item.grossProfit),
                _buildRow('營業費用', item.operatingExpense),
                _buildRow('營業利益', item.operatingIncome),
                _buildRow('淨利', item.netIncome),
                _buildRow('EBITDA', item.ebitda),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildBalanceSheetList(List<BalanceSheetItem> items) {
    if (items.isEmpty) return const Center(child: Text('暫無資料'));
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.period, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                _buildRow('總資產', item.totalAssets),
                _buildRow('總負債', item.totalLiabilities),
                _buildRow('股東權益', item.totalEquity),
                _buildRow('流動資產', item.currentAssets),
                _buildRow('流動負債', item.currentLiabilities),
                _buildRow('現金', item.cash),
                _buildRow('總負債', item.totalDebt),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildCashFlowList(List<CashFlowItem> items) {
    if (items.isEmpty) return const Center(child: Text('暫無資料'));
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.period, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                _buildRow('營業現金流', item.operatingCashFlow),
                _buildRow('投資現金流', item.investingCashFlow),
                _buildRow('融資現金流', item.financingCashFlow),
                _buildRow('自由現金流', item.freeCashFlow),
                _buildRow('資本支出', item.capitalExpenditure),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildRow(String label, double? value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Text(
              label,
              style: TextStyle(fontSize: 13, color: Colors.grey[700]),
            ),
          ),
          Text(
            _formatValue(value),
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  String _formatValue(dynamic value) {
    if (value == null) return '-';
    if (value is num) {
      if (value.abs() >= 1e9) return '${(value / 1e9).toStringAsFixed(1)}B';
      if (value.abs() >= 1e6) return '${(value / 1e6).toStringAsFixed(1)}M';
      if (value.abs() >= 1e3) return '${(value / 1e3).toStringAsFixed(1)}K';
      return value.toStringAsFixed(2);
    }
    return value.toString();
  }
}
