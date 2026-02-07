import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/fundamental.dart';
import '../services/api_service.dart';

/// 法人買賣超圖表 (僅限台股)
class InstitutionalChart extends StatefulWidget {
  final String stockId;
  final int days;

  const InstitutionalChart({
    super.key,
    required this.stockId,
    this.days = 30,
  });

  @override
  State<InstitutionalChart> createState() => _InstitutionalChartState();
}

class _InstitutionalChartState extends State<InstitutionalChart> {
  List<InstitutionalData>? _data;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final data = await apiService.getInstitutional(widget.stockId, days: widget.days);
      if (!mounted) return;
      setState(() {
        _data = data;
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
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    if (_error != null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.grey),
              const SizedBox(height: 8),
              Text('載入失敗', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 4),
              Text(_error!, style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 8),
              TextButton(onPressed: _loadData, child: const Text('重試')),
            ],
          ),
        ),
      );
    }

    if (_data == null || _data!.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: Text('暫無法人買賣超數據')),
        ),
      );
    }

    // Calculate totals
    int totalForeign = 0, totalTrust = 0, totalDealer = 0;
    for (var d in _data!) {
      totalForeign += d.foreignNet;
      totalTrust += d.trustNet;
      totalDealer += d.dealerNet;
    }
    final totalNet = totalForeign + totalTrust + totalDealer;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '法人買賣超',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Text(
                  '近 ${widget.days} 日',
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Summary cards
            Row(
              children: [
                _buildSummaryCard('外資', totalForeign, Colors.blue),
                const SizedBox(width: 8),
                _buildSummaryCard('投信', totalTrust, Colors.orange),
                const SizedBox(width: 8),
                _buildSummaryCard('自營商', totalDealer, Colors.purple),
              ],
            ),
            const SizedBox(height: 8),
            _buildTotalCard('三大法人合計', totalNet),
            const SizedBox(height: 16),
            // Bar chart
            _buildBarChart(),
            const SizedBox(height: 16),
            // Legend
            _buildLegend(),
            const SizedBox(height: 16),
            // Recent data table
            _buildRecentDataTable(),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard(String label, int value, Color color) {
    final isPositive = value >= 0;
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color.withAlpha(26),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withAlpha(77)),
        ),
        child: Column(
          children: [
            Text(label, style: TextStyle(color: color, fontSize: 12)),
            const SizedBox(height: 4),
            Text(
              _formatNumber(value),
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: isPositive ? Colors.red : Colors.green,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTotalCard(String label, int value) {
    final isPositive = value >= 0;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isPositive ? Colors.red.withAlpha(26) : Colors.green.withAlpha(26),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: isPositive ? Colors.red.withAlpha(77) : Colors.green.withAlpha(77)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, style: const TextStyle(fontSize: 14)),
          const SizedBox(width: 12),
          Text(
            _formatNumber(value),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: isPositive ? Colors.red : Colors.green,
            ),
          ),
          const SizedBox(width: 4),
          Icon(
            isPositive ? Icons.trending_up : Icons.trending_down,
            color: isPositive ? Colors.red : Colors.green,
            size: 20,
          ),
        ],
      ),
    );
  }

  Widget _buildBarChart() {
    if (_data == null || _data!.isEmpty) return const SizedBox();

    // Find max value for scaling
    int maxAbs = 1;
    for (var d in _data!) {
      final absTotal = d.totalNet.abs();
      if (absTotal > maxAbs) maxAbs = absTotal;
    }

    // Show last 10 data points for chart
    final displayData = _data!.length > 10 ? _data!.sublist(0, 10) : _data!;

    return SizedBox(
      height: 120,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: displayData.reversed.map((d) {
          final heightRatio = d.totalNet.abs() / maxAbs;
          final height = (80 * heightRatio).clamp(4.0, 80.0);
          final isPositive = d.totalNet >= 0;

          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (!isPositive)
                    Container(
                      height: height,
                      decoration: BoxDecoration(
                        color: Colors.green,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  Container(
                    height: 2,
                    color: Colors.grey[300],
                  ),
                  if (isPositive)
                    Container(
                      height: height,
                      decoration: BoxDecoration(
                        color: Colors.red,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  const SizedBox(height: 4),
                  Text(
                    d.date.substring(5), // MM-DD
                    style: const TextStyle(fontSize: 8, color: Colors.grey),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildLegend() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildLegendItem('買超', Colors.red),
        const SizedBox(width: 16),
        _buildLegendItem('賣超', Colors.green),
      ],
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }

  Widget _buildRecentDataTable() {
    if (_data == null || _data!.isEmpty) return const SizedBox();

    final displayData = _data!.length > 5 ? _data!.sublist(0, 5) : _data!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '近期明細',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Theme.of(context).primaryColor,
          ),
        ),
        const SizedBox(height: 8),
        // Table header
        Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: Theme.of(context).primaryColor.withAlpha(26),
            borderRadius: BorderRadius.circular(4),
          ),
          child: const Row(
            children: [
              Expanded(child: Text('日期', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
              Expanded(child: Text('外資', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
              Expanded(child: Text('投信', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
              Expanded(child: Text('自營', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
              Expanded(child: Text('合計', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
            ],
          ),
        ),
        // Table rows
        ...displayData.map((d) => Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            border: Border(bottom: BorderSide(color: Colors.grey.withAlpha(51))),
          ),
          child: Row(
            children: [
              Expanded(child: Text(d.date.substring(5), textAlign: TextAlign.center, style: const TextStyle(fontSize: 11))),
              Expanded(child: _buildNetCell(d.foreignNet)),
              Expanded(child: _buildNetCell(d.trustNet)),
              Expanded(child: _buildNetCell(d.dealerNet)),
              Expanded(child: _buildNetCell(d.totalNet, bold: true)),
            ],
          ),
        )),
      ],
    );
  }

  Widget _buildNetCell(int value, {bool bold = false}) {
    final isPositive = value >= 0;
    return Text(
      _formatNumber(value),
      textAlign: TextAlign.center,
      style: TextStyle(
        fontSize: 11,
        fontWeight: bold ? FontWeight.bold : FontWeight.normal,
        color: isPositive ? Colors.red : Colors.green,
      ),
    );
  }

  String _formatNumber(int value) {
    final prefix = value > 0 ? '+' : '';
    final absValue = value.abs();
    if (absValue >= 1000000) {
      return '$prefix${(value / 1000000).toStringAsFixed(1)}M';
    } else if (absValue >= 1000) {
      return '$prefix${(value / 1000).toStringAsFixed(0)}K';
    }
    return '$prefix$value';
  }
}
