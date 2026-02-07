import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/fundamental.dart';
import '../services/api_service.dart';

/// 融資融券圖表 (僅限台股)
class MarginChart extends StatefulWidget {
  final String stockId;
  final int days;

  const MarginChart({
    super.key,
    required this.stockId,
    this.days = 30,
  });

  @override
  State<MarginChart> createState() => _MarginChartState();
}

class _MarginChartState extends State<MarginChart> {
  List<MarginData>? _data;
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
      final data = await apiService.getMarginTrading(widget.stockId, days: widget.days);
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
          child: Center(child: Text('暫無融資融券數據')),
        ),
      );
    }

    // Get latest data
    final latest = _data!.first;
    final marginChange = _data!.length > 1
        ? latest.marginBalance - _data![1].marginBalance
        : 0;
    final shortChange = _data!.length > 1
        ? latest.shortBalance - _data![1].shortBalance
        : 0;

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
                  '融資融券',
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
                Expanded(
                  child: _buildSummaryCard(
                    '融資餘額',
                    _formatNumber(latest.marginBalance),
                    marginChange,
                    Colors.red,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildSummaryCard(
                    '融券餘額',
                    _formatNumber(latest.shortBalance),
                    shortChange,
                    Colors.green,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Utilization rate
            if (latest.marginUtilization != null)
              _buildUtilizationCard(latest.marginUtilization!),
            const SizedBox(height: 16),
            // Trend chart
            _buildTrendChart(),
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

  Widget _buildSummaryCard(String label, String value, int change, Color color) {
    final changeColor = change >= 0 ? Colors.red : Colors.green;
    final changePrefix = change > 0 ? '+' : '';

    return Container(
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
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$changePrefix${_formatNumber(change)}',
            style: TextStyle(
              fontSize: 12,
              color: changeColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUtilizationCard(double utilization) {
    Color barColor;
    String levelText;
    if (utilization < 50) {
      barColor = Colors.green;
      levelText = '低';
    } else if (utilization < 70) {
      barColor = Colors.orange;
      levelText = '中';
    } else {
      barColor = Colors.red;
      levelText = '高';
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.withAlpha(26),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('融資使用率', style: TextStyle(fontSize: 12, color: Colors.grey)),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: barColor.withAlpha(51),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      levelText,
                      style: TextStyle(fontSize: 10, color: barColor, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${utilization.toStringAsFixed(1)}%',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: barColor,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: utilization / 100,
              backgroundColor: Colors.grey[300],
              valueColor: AlwaysStoppedAnimation<Color>(barColor),
              minHeight: 8,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTrendChart() {
    if (_data == null || _data!.isEmpty) return const SizedBox();

    // Find max value for scaling
    int maxMargin = 1;
    int maxShort = 1;
    for (var d in _data!) {
      if (d.marginBalance > maxMargin) maxMargin = d.marginBalance;
      if (d.shortBalance > maxShort) maxShort = d.shortBalance;
    }

    // Show last 15 data points for chart
    final displayData = _data!.length > 15 ? _data!.sublist(0, 15) : _data!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '餘額趨勢',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Theme.of(context).primaryColor,
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 100,
          child: CustomPaint(
            size: const Size(double.infinity, 100),
            painter: _TrendChartPainter(
              data: displayData.reversed.toList(),
              maxMargin: maxMargin,
              maxShort: maxShort,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildLegend() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildLegendItem('融資餘額', Colors.red),
        const SizedBox(width: 16),
        _buildLegendItem('融券餘額', Colors.green),
      ],
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 16,
          height: 3,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(1),
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
              Expanded(flex: 2, child: Text('日期', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
              Expanded(flex: 2, child: Text('融資餘額', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
              Expanded(flex: 2, child: Text('融券餘額', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
              Expanded(flex: 2, child: Text('使用率', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
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
              Expanded(flex: 2, child: Text(d.date.substring(5), textAlign: TextAlign.center, style: const TextStyle(fontSize: 11))),
              Expanded(flex: 2, child: Text(_formatNumber(d.marginBalance), textAlign: TextAlign.center, style: const TextStyle(fontSize: 11, color: Colors.red))),
              Expanded(flex: 2, child: Text(_formatNumber(d.shortBalance), textAlign: TextAlign.center, style: const TextStyle(fontSize: 11, color: Colors.green))),
              Expanded(flex: 2, child: Text(
                d.marginUtilization != null ? '${d.marginUtilization!.toStringAsFixed(1)}%' : '-',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 11, color: _getUtilizationColor(d.marginUtilization)),
              )),
            ],
          ),
        )),
      ],
    );
  }

  String _formatNumber(int value) {
    final absValue = value.abs();
    if (absValue >= 1000000) {
      return '${(value / 1000000).toStringAsFixed(1)}M';
    } else if (absValue >= 1000) {
      return '${(value / 1000).toStringAsFixed(0)}K';
    }
    return value.toString();
  }

  Color? _getUtilizationColor(double? utilization) {
    if (utilization == null) return null;
    if (utilization < 50) return Colors.green;
    if (utilization < 70) return Colors.orange;
    return Colors.red;
  }
}

/// Custom painter for trend chart
class _TrendChartPainter extends CustomPainter {
  final List<MarginData> data;
  final int maxMargin;
  final int maxShort;

  _TrendChartPainter({
    required this.data,
    required this.maxMargin,
    required this.maxShort,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;

    final marginPaint = Paint()
      ..color = Colors.red
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final shortPaint = Paint()
      ..color = Colors.green
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final marginPath = Path();
    final shortPath = Path();

    final dx = size.width / (data.length - 1);

    for (var i = 0; i < data.length; i++) {
      final x = dx * i;
      final marginY = size.height - (data[i].marginBalance / maxMargin * size.height * 0.9);
      final shortY = size.height - (data[i].shortBalance / maxShort * size.height * 0.9);

      if (i == 0) {
        marginPath.moveTo(x, marginY);
        shortPath.moveTo(x, shortY);
      } else {
        marginPath.lineTo(x, marginY);
        shortPath.lineTo(x, shortY);
      }
    }

    canvas.drawPath(marginPath, marginPaint);
    canvas.drawPath(shortPath, shortPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
