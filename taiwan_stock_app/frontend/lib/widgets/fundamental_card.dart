import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/fundamental.dart';
import '../services/api_service.dart';

/// 基本面數據卡片
class FundamentalCard extends StatefulWidget {
  final String stockId;
  final String market;

  const FundamentalCard({
    super.key,
    required this.stockId,
    this.market = 'TW',
  });

  @override
  State<FundamentalCard> createState() => _FundamentalCardState();
}

class _FundamentalCardState extends State<FundamentalCard> {
  FundamentalData? _data;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final data = await apiService.getFundamental(widget.stockId, market: widget.market);
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

    if (_data == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: Text('暫無基本面數據')),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '基本面數據',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                if (_data!.reportDate != null)
                  Text(
                    '更新: ${_data!.reportDate}',
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
              ],
            ),
            const Divider(),
            // 估值指標
            _buildSectionTitle('估值指標'),
            _buildMetricRow([
              _MetricItem('本益比', _formatValue(_data!.peRatio), _getPEColor(_data!.peRatio)),
              _MetricItem('股價淨值比', _formatValue(_data!.pbRatio), _getPBColor(_data!.pbRatio)),
            ]),
            _buildMetricRow([
              _MetricItem('EPS', _formatValue(_data!.eps), null),
              _MetricItem('殖利率', _formatPercent(_data!.dividendYield), _getYieldColor(_data!.dividendYield)),
            ]),
            const SizedBox(height: 12),
            // 獲利能力
            _buildSectionTitle('獲利能力'),
            _buildMetricRow([
              _MetricItem('ROE', _formatPercent(_data!.roe), _getROEColor(_data!.roe)),
              _MetricItem('ROA', _formatPercent(_data!.roa), null),
            ]),
            _buildMetricRow([
              _MetricItem('毛利率', _formatPercent(_data!.grossMargin), null),
              _MetricItem('營業利益率', _formatPercent(_data!.operatingMargin), null),
            ]),
            const SizedBox(height: 12),
            // 市值相關
            _buildSectionTitle('市值相關'),
            _buildMetricRow([
              _MetricItem('市值', _data!.formattedMarketCap, null),
              _MetricItem('營收', _data!.formattedRevenue, null),
            ]),
            if (_data!.week52High != null || _data!.week52Low != null)
              _buildMetricRow([
                _MetricItem('52週高', _formatPrice(_data!.week52High), null),
                _MetricItem('52週低', _formatPrice(_data!.week52Low), null),
              ]),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: Theme.of(context).primaryColor,
        ),
      ),
    );
  }

  Widget _buildMetricRow(List<_MetricItem> items) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: items.map((item) {
          return Expanded(
            child: _buildMetricCell(item.label, item.value, item.color),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildMetricCell(String label, String value, Color? color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: color,
          ),
        ),
      ],
    );
  }

  String _formatValue(double? value) {
    if (value == null) return '-';
    return value.toStringAsFixed(2);
  }

  String _formatPercent(double? value) {
    if (value == null) return '-';
    return '${value.toStringAsFixed(2)}%';
  }

  String _formatPrice(double? value) {
    if (value == null) return '-';
    return value.toStringAsFixed(2);
  }

  Color? _getPEColor(double? pe) {
    if (pe == null) return null;
    if (pe < 10) return Colors.green;
    if (pe > 30) return Colors.red;
    return null;
  }

  Color? _getPBColor(double? pb) {
    if (pb == null) return null;
    if (pb < 1) return Colors.green;
    if (pb > 3) return Colors.red;
    return null;
  }

  Color? _getYieldColor(double? yield_) {
    if (yield_ == null) return null;
    if (yield_ > 5) return Colors.green;
    if (yield_ > 3) return Colors.orange;
    return null;
  }

  Color? _getROEColor(double? roe) {
    if (roe == null) return null;
    if (roe > 15) return Colors.green;
    if (roe < 5) return Colors.red;
    return null;
  }
}

class _MetricItem {
  final String label;
  final String value;
  final Color? color;

  _MetricItem(this.label, this.value, this.color);
}
