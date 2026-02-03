import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/fundamental.dart';
import '../services/api_service.dart';

/// 股息歷史表格
class DividendHistory extends StatefulWidget {
  final String stockId;
  final String market;

  const DividendHistory({
    super.key,
    required this.stockId,
    this.market = 'TW',
  });

  @override
  State<DividendHistory> createState() => _DividendHistoryState();
}

class _DividendHistoryState extends State<DividendHistory> {
  List<DividendData>? _data;
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
      final data = await apiService.getDividends(widget.stockId, market: widget.market);
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

    if (_data == null || _data!.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: Text('暫無股息紀錄')),
        ),
      );
    }

    // Calculate average dividend and yield
    double totalDividend = 0;
    int count = 0;
    for (var d in _data!) {
      if (d.totalDividend > 0) {
        totalDividend += d.totalDividend;
        count++;
      }
    }
    final avgDividend = count > 0 ? totalDividend / count : 0.0;

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
                  '股息歷史',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.withAlpha(26),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '平均 ${avgDividend.toStringAsFixed(2)}/年',
                    style: const TextStyle(color: Colors.green, fontSize: 12),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Table header
            Container(
              padding: const EdgeInsets.symmetric(vertical: 8),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor.withAlpha(26),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                children: [
                  _buildTableHeader('年度', 1),
                  _buildTableHeader('現金股利', 1),
                  _buildTableHeader('股票股利', 1),
                  _buildTableHeader('合計', 1),
                  _buildTableHeader('殖利率', 1),
                ],
              ),
            ),
            // Table rows
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _data!.length > 10 ? 10 : _data!.length, // Show max 10 years
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final dividend = _data![index];
                return _buildTableRow(dividend);
              },
            ),
            if (_data!.length > 10)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Center(
                  child: Text(
                    '僅顯示最近 10 年資料',
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildTableHeader(String text, int flex) {
    return Expanded(
      flex: flex,
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 12,
          color: Theme.of(context).primaryColor,
        ),
      ),
    );
  }

  Widget _buildTableRow(DividendData dividend) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          _buildTableCell('${dividend.year}', 1),
          _buildTableCell(
            dividend.cashDividend > 0 ? dividend.cashDividend.toStringAsFixed(2) : '-',
            1,
          ),
          _buildTableCell(
            dividend.stockDividend > 0 ? dividend.stockDividend.toStringAsFixed(2) : '-',
            1,
          ),
          _buildTableCell(
            dividend.totalDividend > 0 ? dividend.totalDividend.toStringAsFixed(2) : '-',
            1,
            color: dividend.totalDividend > 0 ? Colors.green : null,
            bold: true,
          ),
          _buildTableCell(
            dividend.dividendYield != null ? '${dividend.dividendYield!.toStringAsFixed(2)}%' : '-',
            1,
            color: _getYieldColor(dividend.dividendYield),
          ),
        ],
      ),
    );
  }

  Widget _buildTableCell(String text, int flex, {Color? color, bool bold = false}) {
    return Expanded(
      flex: flex,
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(
          fontSize: 14,
          color: color,
          fontWeight: bold ? FontWeight.w600 : FontWeight.normal,
        ),
      ),
    );
  }

  Color? _getYieldColor(double? yield_) {
    if (yield_ == null) return null;
    if (yield_ > 5) return Colors.green;
    if (yield_ > 3) return Colors.orange;
    return null;
  }
}
