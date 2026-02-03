import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/indicator_data.dart';
import '../../services/api_service.dart';
import 'rsi_chart.dart';
import 'macd_chart.dart';
import 'bollinger_chart.dart';
import 'kd_chart.dart';

class IndicatorsTabView extends StatefulWidget {
  final String stockId;
  final String market;

  const IndicatorsTabView({super.key, required this.stockId, this.market = 'TW'});

  @override
  State<IndicatorsTabView> createState() => _IndicatorsTabViewState();
}

class _IndicatorsTabViewState extends State<IndicatorsTabView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  AllIndicatorsData? _data;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
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
    });

    try {
      final apiService = context.read<ApiService>();
      final data = await apiService.getAllIndicators(widget.stockId, market: widget.market);
      setState(() {
        _data = data;
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
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('載入失敗: $_error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadData,
              child: const Text('重試'),
            ),
          ],
        ),
      );
    }

    if (_data == null) {
      return const Center(child: Text('無數據'));
    }

    return Column(
      children: [
        TabBar(
          controller: _tabController,
          labelColor: Theme.of(context).primaryColor,
          unselectedLabelColor: Colors.grey,
          indicatorColor: Theme.of(context).primaryColor,
          tabs: const [
            Tab(text: 'RSI'),
            Tab(text: 'MACD'),
            Tab(text: '布林'),
            Tab(text: 'KD'),
          ],
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              RSIChart(data: _data!.rsi),
              MACDChart(data: _data!.macd),
              BollingerChart(data: _data!.bollinger),
              KDChart(data: _data!.kd),
            ],
          ),
        ),
        // 最新指標摘要
        _buildLatestIndicatorsSummary(),
      ],
    );
  }

  Widget _buildLatestIndicatorsSummary() {
    if (_data?.latest == null || _data!.latest.isEmpty) {
      return const SizedBox.shrink();
    }

    final latest = _data!.latest;

    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '最新技術指標',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 16,
            runSpacing: 8,
            children: [
              _buildIndicatorChip('RSI', latest['rsi'], _getRSIColor(latest['rsi'])),
              _buildIndicatorChip('K', latest['k'], _getKDColor(latest['k'])),
              _buildIndicatorChip('D', latest['d'], _getKDColor(latest['d'])),
              _buildIndicatorChip('MACD', latest['macd'], _getMACDColor(latest['macd'])),
              if (latest['ma5'] != null)
                _buildIndicatorChip('MA5', latest['ma5'], Colors.blue),
              if (latest['ma20'] != null)
                _buildIndicatorChip('MA20', latest['ma20'], Colors.orange),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildIndicatorChip(String label, dynamic value, Color color) {
    final displayValue = value != null
        ? (value is double ? value.toStringAsFixed(2) : value.toString())
        : '-';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withAlpha(77)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$label: ',
            style: const TextStyle(fontSize: 12, color: Colors.grey),
          ),
          Text(
            displayValue,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color),
          ),
        ],
      ),
    );
  }

  Color _getRSIColor(dynamic value) {
    if (value == null) return Colors.grey;
    final v = value is double ? value : double.tryParse(value.toString()) ?? 50;
    if (v >= 70) return Colors.red;
    if (v <= 30) return Colors.green;
    return Colors.purple;
  }

  Color _getKDColor(dynamic value) {
    if (value == null) return Colors.grey;
    final v = value is double ? value : double.tryParse(value.toString()) ?? 50;
    if (v >= 80) return Colors.red;
    if (v <= 20) return Colors.green;
    return Colors.blue;
  }

  Color _getMACDColor(dynamic value) {
    if (value == null) return Colors.grey;
    final v = value is double ? value : double.tryParse(value.toString()) ?? 0;
    return v >= 0 ? Colors.red : Colors.green;
  }
}
