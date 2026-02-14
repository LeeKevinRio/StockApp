import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import '../providers/market_provider.dart';
import '../models/stock.dart';

class StockCompareScreen extends StatefulWidget {
  const StockCompareScreen({super.key});

  @override
  State<StockCompareScreen> createState() => _StockCompareScreenState();
}

class _StockCompareScreenState extends State<StockCompareScreen> {
  final List<String> _selectedStocks = [];
  final Map<String, List<Map<String, dynamic>>> _priceData = {};
  final Map<String, Map<String, dynamic>> _stockInfo = {};
  bool _isLoading = false;
  String? _error;
  final _searchController = TextEditingController();
  List<Stock> _searchResults = [];
  bool _isSearching = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _searchStocks(String query) async {
    if (query.isEmpty) {
      setState(() => _searchResults = []);
      return;
    }

    setState(() => _isSearching = true);
    try {
      final api = context.read<ApiService>();
      final market = context.read<MarketProvider>().marketCode;
      final results = await api.searchStocks(query, market: market);
      if (mounted) {
        setState(() {
          _searchResults = results;
          _isSearching = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isSearching = false);
    }
  }

  Future<void> _addStock(String stockId, String stockName) async {
    if (_selectedStocks.contains(stockId) || _selectedStocks.length >= 4) {
      return;
    }

    setState(() {
      _selectedStocks.add(stockId);
      _searchController.clear();
      _searchResults = [];
    });

    await _loadStockData(stockId, stockName);
  }

  void _removeStock(String stockId) {
    setState(() {
      _selectedStocks.remove(stockId);
      _priceData.remove(stockId);
      _stockInfo.remove(stockId);
    });
  }

  Future<void> _loadStockData(String stockId, String stockName) async {
    setState(() => _isLoading = true);

    try {
      final api = context.read<ApiService>();
      final market = context.read<MarketProvider>().marketCode;

      final history =
          await api.getStockHistory(stockId, days: 60, market: market);

      if (mounted) {
        setState(() {
          _priceData[stockId] = history
              .map((h) => {
                    "date": h.date,
                    "close": h.close,
                  })
              .toList();
          _stockInfo[stockId] = {
            "name": stockName,
            "latest_price":
                history.isNotEmpty ? history.last.close : 0,
          };
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
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('個股比較'),
      ),
      body: Column(
        children: [
          // 搜尋列
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: '搜尋股票代碼加入比較 (最多4支)',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12)),
                suffixIcon: _isSearching
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: Padding(
                          padding: EdgeInsets.all(12),
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      )
                    : null,
              ),
              onChanged: _searchStocks,
            ),
          ),

          // 搜尋結果
          if (_searchResults.isNotEmpty)
            Container(
              constraints: const BoxConstraints(maxHeight: 200),
              margin: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(8),
                boxShadow: [
                  BoxShadow(color: Colors.black12, blurRadius: 4),
                ],
              ),
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: _searchResults.length,
                itemBuilder: (context, index) {
                  final stock = _searchResults[index];
                  final alreadyAdded =
                      _selectedStocks.contains(stock.stockId);
                  return ListTile(
                    title: Text('${stock.stockId} ${stock.name}'),
                    trailing: alreadyAdded
                        ? const Icon(Icons.check, color: Colors.green)
                        : const Icon(Icons.add),
                    enabled: !alreadyAdded && _selectedStocks.length < 4,
                    onTap: () => _addStock(stock.stockId, stock.name),
                  );
                },
              ),
            ),

          // 已選股票 chips
          if (_selectedStocks.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Wrap(
                spacing: 8,
                children: _selectedStocks.map((id) {
                  final info = _stockInfo[id];
                  return Chip(
                    label: Text('$id ${info?["name"] ?? ""}'),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    onDeleted: () => _removeStock(id),
                    backgroundColor: _getStockColor(
                            _selectedStocks.indexOf(id))
                        .withValues(alpha: 0.15),
                  );
                }).toList(),
              ),
            ),

          // 比較內容
          Expanded(
            child: _selectedStocks.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.compare_arrows,
                            size: 64, color: Colors.grey),
                        SizedBox(height: 16),
                        Text('請搜尋並加入 2-4 支股票進行比較',
                            style: TextStyle(color: Colors.grey)),
                      ],
                    ),
                  )
                : _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : SingleChildScrollView(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          children: [
                            if (_selectedStocks.length >= 2)
                              _buildNormalizedChart(),
                            const SizedBox(height: 16),
                            _buildComparisonTable(),
                          ],
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  /// 正規化走勢圖（以第一天為基準 = 100%）
  Widget _buildNormalizedChart() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('正規化走勢比較（基準 = 100%）',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            // 圖例
            Wrap(
              spacing: 12,
              children: _selectedStocks.asMap().entries.map((entry) {
                final color = _getStockColor(entry.key);
                final name = _stockInfo[entry.value]?["name"] ?? "";
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(width: 16, height: 3, color: color),
                    const SizedBox(width: 4),
                    Text('${entry.value} $name',
                        style: const TextStyle(fontSize: 12)),
                  ],
                );
              }).toList(),
            ),
            const Divider(),
            SizedBox(
              height: 250,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: Colors.grey.shade200,
                      strokeWidth: 1,
                    ),
                  ),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 45,
                        getTitlesWidget: (value, _) => Text(
                          '${value.toStringAsFixed(0)}%',
                          style: const TextStyle(
                              fontSize: 10, color: Colors.grey),
                        ),
                      ),
                    ),
                    bottomTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  lineBarsData: _selectedStocks
                      .asMap()
                      .entries
                      .map((entry) {
                    final data = _priceData[entry.value] ?? [];
                    if (data.isEmpty) return null;

                    final basePrice = (data[0]['close'] as num).toDouble();
                    if (basePrice == 0) return null;

                    final spots = data.asMap().entries.map((e) {
                      final price =
                          (e.value['close'] as num).toDouble();
                      return FlSpot(
                          e.key.toDouble(), (price / basePrice) * 100);
                    }).toList();

                    return LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      curveSmoothness: 0.2,
                      color: _getStockColor(entry.key),
                      barWidth: 2,
                      dotData: const FlDotData(show: false),
                    );
                  })
                      .whereType<LineChartBarData>()
                      .toList(),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 指標對比表
  Widget _buildComparisonTable() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('指標對比',
                style: Theme.of(context).textTheme.titleMedium),
            const Divider(),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: [
                  const DataColumn(label: Text('指標')),
                  ..._selectedStocks.map((id) {
                    final name = _stockInfo[id]?["name"] ?? "";
                    return DataColumn(
                      label: Text('$id\n$name',
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 12)),
                    );
                  }),
                ],
                rows: _buildDataRows(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<DataRow> _buildDataRows() {
    final rows = <DataRow>[];

    // 最新價格
    rows.add(DataRow(cells: [
      const DataCell(Text('最新價格')),
      ..._selectedStocks.map((id) {
        final info = _stockInfo[id];
        return DataCell(
            Text('${info?["latest_price"]?.toStringAsFixed(2) ?? "N/A"}'));
      }),
    ]));

    // 漲跌幅（整段期間）
    rows.add(DataRow(cells: [
      const DataCell(Text('60日漲跌幅')),
      ..._selectedStocks.map((id) {
        final data = _priceData[id] ?? [];
        if (data.length < 2) return const DataCell(Text('N/A'));
        final first = (data[0]['close'] as num).toDouble();
        final last = (data.last['close'] as num).toDouble();
        final change = ((last - first) / first * 100);
        return DataCell(Text(
          '${change >= 0 ? "+" : ""}${change.toStringAsFixed(2)}%',
          style: TextStyle(
            color: change >= 0 ? Colors.red : Colors.green,
            fontWeight: FontWeight.bold,
          ),
        ));
      }),
    ]));

    // 波動度
    rows.add(DataRow(cells: [
      const DataCell(Text('波動度')),
      ..._selectedStocks.map((id) {
        final data = _priceData[id] ?? [];
        if (data.length < 5) return const DataCell(Text('N/A'));
        final changes = <double>[];
        for (int i = 1; i < data.length; i++) {
          final prev = (data[i - 1]['close'] as num).toDouble();
          final curr = (data[i]['close'] as num).toDouble();
          if (prev > 0) changes.add((curr - prev) / prev * 100);
        }
        if (changes.isEmpty) return const DataCell(Text('N/A'));
        final mean = changes.reduce((a, b) => a + b) / changes.length;
        final variance = changes.map((c) => (c - mean) * (c - mean)).reduce((a, b) => a + b) / changes.length;
        final stdDev = variance > 0 ? _sqrt(variance) : 0.0;
        return DataCell(
            Text('${stdDev.toStringAsFixed(2)}%'));
      }),
    ]));

    // 最高價
    rows.add(DataRow(cells: [
      const DataCell(Text('60日最高')),
      ..._selectedStocks.map((id) {
        final data = _priceData[id] ?? [];
        if (data.isEmpty) return const DataCell(Text('N/A'));
        final maxPrice = data
            .map((d) => (d['close'] as num).toDouble())
            .reduce((a, b) => a > b ? a : b);
        return DataCell(Text(maxPrice.toStringAsFixed(2)));
      }),
    ]));

    // 最低價
    rows.add(DataRow(cells: [
      const DataCell(Text('60日最低')),
      ..._selectedStocks.map((id) {
        final data = _priceData[id] ?? [];
        if (data.isEmpty) return const DataCell(Text('N/A'));
        final minPrice = data
            .map((d) => (d['close'] as num).toDouble())
            .reduce((a, b) => a < b ? a : b);
        return DataCell(Text(minPrice.toStringAsFixed(2)));
      }),
    ]));

    return rows;
  }

  double _sqrt(double value) {
    if (value <= 0) return 0;
    double guess = value / 2;
    for (int i = 0; i < 20; i++) {
      guess = (guess + value / guess) / 2;
    }
    return guess;
  }

  Color _getStockColor(int index) {
    const colors = [
      Colors.blue,
      Colors.red,
      Colors.green,
      Colors.orange,
    ];
    return colors[index % colors.length];
  }
}
