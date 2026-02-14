import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';

class PredictionStatsScreen extends StatefulWidget {
  const PredictionStatsScreen({super.key});

  @override
  State<PredictionStatsScreen> createState() => _PredictionStatsScreenState();
}

class _PredictionStatsScreenState extends State<PredictionStatsScreen> {
  Map<String, dynamic>? _statistics;
  Map<String, dynamic>? _yesterdayData;
  Map<String, dynamic>? _todayData;
  Map<String, dynamic>? _allStocksData;
  bool _isLoading = true;
  String? _error;
  int _selectedDays = 30;
  int _selectedTab = 0; // 0: 概覽, 1: 依股票

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
      final apiService = context.read<ApiService>();
      final results = await Future.wait([
        apiService.getPredictionStatistics(days: _selectedDays),
        apiService.getYesterdayPredictions(),
        apiService.getTodayPredictions(),
        apiService.getAllStocksPredictionStats(days: _selectedDays),
      ]);

      if (mounted) {
        setState(() {
          _statistics = results[0];
          _yesterdayData = results[1];
          _todayData = results[2];
          _allStocksData = results[3];
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
        title: const Text('AI 預測準確度'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildError()
              : _buildContent(),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          Text('載入失敗', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _loadData,
            icon: const Icon(Icons.refresh),
            label: const Text('重試'),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    return Column(
      children: [
        // Tab 選擇器
        Container(
          color: Theme.of(context).cardColor,
          child: Row(
            children: [
              Expanded(
                child: InkWell(
                  onTap: () => setState(() => _selectedTab = 0),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(
                      border: Border(
                        bottom: BorderSide(
                          color: _selectedTab == 0 ? Colors.blue : Colors.transparent,
                          width: 2,
                        ),
                      ),
                    ),
                    child: Text(
                      '概覽',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontWeight: _selectedTab == 0 ? FontWeight.bold : FontWeight.normal,
                        color: _selectedTab == 0 ? Colors.blue : Colors.grey,
                      ),
                    ),
                  ),
                ),
              ),
              Expanded(
                child: InkWell(
                  onTap: () => setState(() => _selectedTab = 1),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(
                      border: Border(
                        bottom: BorderSide(
                          color: _selectedTab == 1 ? Colors.blue : Colors.transparent,
                          width: 2,
                        ),
                      ),
                    ),
                    child: Text(
                      '依股票統計',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontWeight: _selectedTab == 1 ? FontWeight.bold : FontWeight.normal,
                        color: _selectedTab == 1 ? Colors.blue : Colors.grey,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        // 內容區域
        Expanded(
          child: RefreshIndicator(
            onRefresh: _loadData,
            child: _selectedTab == 0 ? _buildOverviewTab() : _buildStocksTab(),
          ),
        ),
      ],
    );
  }

  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildTodayResultsSection(),
          const SizedBox(height: 24),
          _buildPeriodSelector(),
          const SizedBox(height: 16),
          _buildOverallStats(),
          const SizedBox(height: 24),
          _buildAccuracyTrendChart(),
          const SizedBox(height: 24),
          _buildPredictedVsActualChart(),
          const SizedBox(height: 24),
          _buildYesterdaySection(),
          const SizedBox(height: 24),
          _buildRecentRecords(),
        ],
      ),
    );
  }

  Widget _buildStocksTab() {
    final data = _allStocksData;
    if (data == null) {
      return const Center(child: Text('載入中...'));
    }

    final stocks = (data['stocks'] as List?) ?? [];
    final overallAccuracy = data['overall_accuracy'] ?? 0.0;
    final overallError = data['overall_avg_error'] ?? 0.0;
    final totalPredictions = data['total_predictions'] ?? 0;

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildPeriodSelector(),
          const SizedBox(height: 16),
          // 整體統計卡片
          Card(
            color: Colors.green.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      children: [
                        Text(
                          '${overallAccuracy.toStringAsFixed(1)}%',
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: overallAccuracy >= 50 ? Colors.green : Colors.red,
                          ),
                        ),
                        const Text('整體準確率', style: TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Column(
                      children: [
                        Text(
                          '${overallError.toStringAsFixed(2)}%',
                          style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                        ),
                        const Text('平均誤差', style: TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Column(
                      children: [
                        Text(
                          '$totalPredictions',
                          style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                        ),
                        const Text('總預測數', style: TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            '各股票統計 (${stocks.length} 支)',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          if (stocks.isEmpty)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Text('尚無預測記錄'),
              ),
            )
          else
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: stocks.length,
              itemBuilder: (context, index) {
                final stock = stocks[index];
                return _buildStockStatsCard(stock);
              },
            ),
        ],
      ),
    );
  }

  Widget _buildStockStatsCard(Map<String, dynamic> stock) {
    final stockId = stock['stock_id'] ?? '';
    final stockName = stock['stock_name'] ?? '';
    final market = stock['market'] ?? 'TW';
    final totalPredictions = stock['total_predictions'] ?? 0;
    final accuracy = (stock['direction_accuracy'] ?? 0.0).toDouble();
    final avgError = (stock['avg_error_percent'] ?? 0.0).toDouble();
    final correctCount = stock['correct_count'] ?? 0;
    final predictions = (stock['predictions'] as List?) ?? [];

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: accuracy >= 50 ? Colors.green.shade100 : Colors.red.shade100,
          child: Text(
            '${accuracy.toInt()}%',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: accuracy >= 50 ? Colors.green.shade700 : Colors.red.shade700,
            ),
          ),
        ),
        title: Row(
          children: [
            Text(
              '$stockId $stockName',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: market == 'US' ? Colors.blue.shade100 : Colors.orange.shade100,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                market,
                style: TextStyle(
                  fontSize: 10,
                  color: market == 'US' ? Colors.blue.shade700 : Colors.orange.shade700,
                ),
              ),
            ),
          ],
        ),
        subtitle: Text(
          '預測 $totalPredictions 次 · 正確 $correctCount 次 · 平均誤差 ${avgError.toStringAsFixed(2)}%',
          style: const TextStyle(fontSize: 12),
        ),
        children: [
          if (predictions.isEmpty)
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('無歷史記錄'),
            )
          else
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: predictions.length,
              itemBuilder: (context, index) {
                final pred = predictions[index];
                return _buildStockPredictionRow(pred);
              },
            ),
        ],
      ),
    );
  }

  Widget _buildStockPredictionRow(Map<String, dynamic> pred) {
    final targetDate = pred['target_date'] ?? '';
    final predictedDir = pred['predicted_direction'] ?? '';
    final predictedChange = (pred['predicted_change'] ?? 0.0).toDouble();
    final actualDir = pred['actual_direction'] ?? '';
    final actualChange = (pred['actual_change'] ?? 0.0).toDouble();
    final directionCorrect = pred['direction_correct'] ?? false;
    final errorPercent = (pred['error_percent'] ?? 0.0).toDouble();

    final isPredictUp = predictedDir == 'UP';
    final isActualUp = actualDir == 'UP';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Row(
        children: [
          // 日期
          SizedBox(
            width: 80,
            child: Text(
              targetDate.substring(5), // MM-DD
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ),
          // 預測
          Expanded(
            child: Row(
              children: [
                Icon(
                  isPredictUp ? Icons.arrow_upward : Icons.arrow_downward,
                  size: 14,
                  color: isPredictUp ? Colors.red : Colors.green,
                ),
                Text(
                  '${predictedChange >= 0 ? '+' : ''}${predictedChange.toStringAsFixed(1)}%',
                  style: TextStyle(
                    fontSize: 12,
                    color: isPredictUp ? Colors.red : Colors.green,
                  ),
                ),
              ],
            ),
          ),
          // 實際
          Expanded(
            child: Row(
              children: [
                Icon(
                  isActualUp ? Icons.arrow_upward : Icons.arrow_downward,
                  size: 14,
                  color: isActualUp ? Colors.red : Colors.green,
                ),
                Text(
                  '${actualChange >= 0 ? '+' : ''}${actualChange.toStringAsFixed(1)}%',
                  style: TextStyle(
                    fontSize: 12,
                    color: isActualUp ? Colors.red : Colors.green,
                  ),
                ),
              ],
            ),
          ),
          // 誤差
          SizedBox(
            width: 50,
            child: Text(
              '${errorPercent.toStringAsFixed(1)}%',
              style: TextStyle(
                fontSize: 12,
                color: errorPercent <= 2 ? Colors.green : Colors.orange,
              ),
            ),
          ),
          // 正確標記
          Icon(
            directionCorrect ? Icons.check_circle : Icons.cancel,
            size: 16,
            color: directionCorrect ? Colors.green : Colors.red,
          ),
        ],
      ),
    );
  }

  /// 從 statistics records 中取得排序好的記錄
  List<Map<String, dynamic>> _getSortedRecords() {
    final stats = _statistics;
    if (stats == null) return [];
    final records = (stats['records'] as List?) ?? [];
    final sorted = records
        .map((r) => Map<String, dynamic>.from(r))
        .where((r) => r['actual_change'] != null)
        .toList();
    sorted.sort((a, b) =>
        (a['target_date'] ?? '').compareTo(b['target_date'] ?? ''));
    return sorted;
  }

  /// 累計準確率趨勢折線圖
  Widget _buildAccuracyTrendChart() {
    final records = _getSortedRecords();
    if (records.length < 2) return const SizedBox.shrink();

    // 計算累計準確率
    int correct = 0;
    final spots = <FlSpot>[];
    final dates = <String>[];

    for (int i = 0; i < records.length; i++) {
      if (records[i]['direction_correct'] == true) correct++;
      final accuracy = (correct / (i + 1)) * 100;
      spots.add(FlSpot(i.toDouble(), accuracy));
      dates.add(records[i]['target_date'] ?? '');
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.show_chart, color: Colors.blue),
                const SizedBox(width: 8),
                Text(
                  '累計準確率趨勢',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const Divider(),
            SizedBox(
              height: 200,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: 25,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: Colors.grey.shade200,
                      strokeWidth: 1,
                    ),
                  ),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        interval: 25,
                        getTitlesWidget: (value, _) => Text(
                          '${value.toInt()}%',
                          style: const TextStyle(fontSize: 10, color: Colors.grey),
                        ),
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        interval: (records.length / 4).ceilToDouble().clamp(1, double.infinity),
                        getTitlesWidget: (value, _) {
                          final idx = value.toInt();
                          if (idx < 0 || idx >= dates.length) return const SizedBox.shrink();
                          final d = dates[idx];
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              d.length >= 10 ? d.substring(5) : d,
                              style: const TextStyle(fontSize: 9, color: Colors.grey),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  minY: 0,
                  maxY: 100,
                  borderData: FlBorderData(show: false),
                  extraLinesData: ExtraLinesData(
                    horizontalLines: [
                      HorizontalLine(
                        y: 50,
                        color: Colors.red.shade200,
                        strokeWidth: 1,
                        dashArray: [5, 5],
                        label: HorizontalLineLabel(
                          show: true,
                          alignment: Alignment.topRight,
                          style: TextStyle(fontSize: 9, color: Colors.red.shade300),
                          labelResolver: (_) => '50%',
                        ),
                      ),
                    ],
                  ),
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (spots) => spots.map((s) {
                        final idx = s.spotIndex;
                        final d = idx < dates.length ? dates[idx] : '';
                        return LineTooltipItem(
                          '$d\n準確率 ${s.y.toStringAsFixed(1)}%',
                          const TextStyle(fontSize: 12, color: Colors.white),
                        );
                      }).toList(),
                    ),
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      curveSmoothness: 0.2,
                      color: Colors.blue,
                      barWidth: 2.5,
                      dotData: FlDotData(
                        show: true,
                        getDotPainter: (spot, _, __, ___) => FlDotCirclePainter(
                          radius: records.length > 15 ? 0 : 3,
                          color: Colors.blue,
                          strokeColor: Colors.white,
                          strokeWidth: 1,
                        ),
                      ),
                      belowBarData: BarAreaData(
                        show: true,
                        color: Colors.blue.withValues(alpha: 0.1),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 預測 vs 實際漲跌幅折線圖
  Widget _buildPredictedVsActualChart() {
    final records = _getSortedRecords();
    if (records.length < 2) return const SizedBox.shrink();

    final predictedSpots = <FlSpot>[];
    final actualSpots = <FlSpot>[];
    final dates = <String>[];
    double minY = 0, maxY = 0;

    for (int i = 0; i < records.length; i++) {
      final predicted = (records[i]['predicted_change'] ?? 0.0).toDouble();
      final actual = (records[i]['actual_change'] ?? 0.0).toDouble();
      predictedSpots.add(FlSpot(i.toDouble(), predicted));
      actualSpots.add(FlSpot(i.toDouble(), actual));
      dates.add(records[i]['target_date'] ?? '');

      if (predicted < minY) minY = predicted;
      if (actual < minY) minY = actual;
      if (predicted > maxY) maxY = predicted;
      if (actual > maxY) maxY = actual;
    }

    // 加一點 padding
    minY = (minY - 1).floorToDouble();
    maxY = (maxY + 1).ceilToDouble();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.compare_arrows, color: Colors.deepPurple),
                const SizedBox(width: 8),
                Text(
                  '預測 vs 實際漲跌',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 8),
            // 圖例
            Row(
              children: [
                Container(width: 16, height: 3, color: Colors.orange),
                const SizedBox(width: 4),
                const Text('預測', style: TextStyle(fontSize: 12, color: Colors.grey)),
                const SizedBox(width: 16),
                Container(width: 16, height: 3, color: Colors.blue),
                const SizedBox(width: 4),
                const Text('實際', style: TextStyle(fontSize: 12, color: Colors.grey)),
              ],
            ),
            const Divider(),
            SizedBox(
              height: 200,
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
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        getTitlesWidget: (value, _) => Text(
                          '${value.toStringAsFixed(1)}%',
                          style: const TextStyle(fontSize: 9, color: Colors.grey),
                        ),
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        interval: (records.length / 4).ceilToDouble().clamp(1, double.infinity),
                        getTitlesWidget: (value, _) {
                          final idx = value.toInt();
                          if (idx < 0 || idx >= dates.length) return const SizedBox.shrink();
                          final d = dates[idx];
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              d.length >= 10 ? d.substring(5) : d,
                              style: const TextStyle(fontSize: 9, color: Colors.grey),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  minY: minY,
                  maxY: maxY,
                  borderData: FlBorderData(show: false),
                  extraLinesData: ExtraLinesData(
                    horizontalLines: [
                      HorizontalLine(
                        y: 0,
                        color: Colors.grey.shade400,
                        strokeWidth: 1,
                      ),
                    ],
                  ),
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (spots) => spots.map((s) {
                        final idx = s.spotIndex;
                        final d = idx < dates.length ? dates[idx] : '';
                        final label = s.barIndex == 0 ? '預測' : '實際';
                        final color = s.barIndex == 0 ? Colors.orange : Colors.blue;
                        return LineTooltipItem(
                          '$d\n$label ${s.y >= 0 ? '+' : ''}${s.y.toStringAsFixed(2)}%',
                          TextStyle(fontSize: 11, color: color),
                        );
                      }).toList(),
                    ),
                  ),
                  lineBarsData: [
                    // 預測線
                    LineChartBarData(
                      spots: predictedSpots,
                      isCurved: true,
                      curveSmoothness: 0.2,
                      color: Colors.orange,
                      barWidth: 2,
                      dotData: FlDotData(
                        show: true,
                        getDotPainter: (spot, _, __, ___) => FlDotCirclePainter(
                          radius: records.length > 15 ? 0 : 2.5,
                          color: Colors.orange,
                          strokeColor: Colors.white,
                          strokeWidth: 1,
                        ),
                      ),
                    ),
                    // 實際線
                    LineChartBarData(
                      spots: actualSpots,
                      isCurved: true,
                      curveSmoothness: 0.2,
                      color: Colors.blue,
                      barWidth: 2,
                      dotData: FlDotData(
                        show: true,
                        getDotPainter: (spot, _, __, ___) => FlDotCirclePainter(
                          radius: records.length > 15 ? 0 : 2.5,
                          color: Colors.blue,
                          strokeColor: Colors.white,
                          strokeWidth: 1,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTodayResultsSection() {
    final data = _todayData;
    if (data == null) return const SizedBox.shrink();

    final predictions = (data['predictions'] as List?) ?? [];
    final total = data['total'] ?? 0;
    final accuracy = data['direction_accuracy'];
    final dateStr = data['date'] ?? '';

    // 格式化日期顯示
    String displayDate = dateStr;
    if (dateStr.isNotEmpty) {
      try {
        final dt = DateTime.parse(dateStr);
        displayDate = '${dt.month}/${dt.day}';
      } catch (_) {}
    }

    return Card(
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.today, color: Colors.blue),
                const SizedBox(width: 8),
                Text(
                  '今日預測結果 ($displayDate)',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.blue.shade700,
                  ),
                ),
                const Spacer(),
                if (accuracy != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: accuracy >= 50 ? Colors.green : Colors.red,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '準確率 ${accuracy.toStringAsFixed(1)}%',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  )
                else if (total > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.blue,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '$total 筆',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
              ],
            ),
            const Divider(),
            if (predictions.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Center(
                  child: Column(
                    children: [
                      Icon(Icons.info_outline, color: Colors.grey, size: 32),
                      SizedBox(height: 8),
                      Text('今日無預測記錄'),
                      SizedBox(height: 4),
                      Text(
                        '請先查看股票的 AI 建議，系統會自動記錄預測',
                        style: TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              )
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: predictions.length,
                itemBuilder: (context, index) {
                  final pred = predictions[index];
                  return _buildPredictionItem(pred);
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPeriodSelector() {
    return Row(
      children: [
        const Text('統計區間：'),
        const SizedBox(width: 8),
        SegmentedButton<int>(
          segments: const [
            ButtonSegment(value: 7, label: Text('7天')),
            ButtonSegment(value: 30, label: Text('30天')),
            ButtonSegment(value: 90, label: Text('90天')),
          ],
          selected: {_selectedDays},
          onSelectionChanged: (values) {
            setState(() {
              _selectedDays = values.first;
            });
            _loadData();
          },
        ),
      ],
    );
  }

  Widget _buildOverallStats() {
    final stats = _statistics;
    if (stats == null) return const SizedBox.shrink();

    final total = stats['total_predictions'] ?? 0;
    final directionAccuracy = stats['direction_accuracy'] ?? 0.0;
    final avgError = stats['avg_error_percent'] ?? 0.0;
    final withinRangeRate = stats['within_range_rate'] ?? 0.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.analytics, color: Colors.blue),
                const SizedBox(width: 8),
                Text(
                  '整體統計（近 $_selectedDays 天）',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const Divider(),
            if (total == 0)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Center(child: Text('暫無預測記錄')),
              )
            else
              Column(
                children: [
                  _buildStatRow(
                    '總預測數',
                    '$total 筆',
                    Icons.format_list_numbered,
                  ),
                  _buildStatRow(
                    '方向準確率',
                    '${directionAccuracy.toStringAsFixed(1)}%',
                    Icons.trending_up,
                    valueColor: directionAccuracy >= 50 ? Colors.green : Colors.red,
                  ),
                  _buildStatRow(
                    '平均預測誤差',
                    '${avgError.toStringAsFixed(2)}%',
                    Icons.error_outline,
                    valueColor: avgError <= 2 ? Colors.green : Colors.orange,
                  ),
                  _buildStatRow(
                    '落在預測區間率',
                    '${withinRangeRate.toStringAsFixed(1)}%',
                    Icons.crop_free,
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow(String label, String value, IconData icon, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey),
          const SizedBox(width: 12),
          Expanded(child: Text(label)),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
              color: valueColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildYesterdaySection() {
    final data = _yesterdayData;
    if (data == null) return const SizedBox.shrink();

    final predictions = (data['predictions'] as List?) ?? [];
    final evaluated = data['evaluated'] ?? 0;
    final accuracy = data['direction_accuracy'];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.today, color: Colors.orange),
                const SizedBox(width: 8),
                Text(
                  '昨日預測結果',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const Spacer(),
                if (accuracy != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: accuracy >= 50 ? Colors.green : Colors.red,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '準確率 ${accuracy.toStringAsFixed(1)}%',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                  ),
              ],
            ),
            const Divider(),
            if (predictions.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Center(child: Text('昨日無預測記錄')),
              )
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: predictions.length,
                itemBuilder: (context, index) {
                  final pred = predictions[index];
                  return _buildPredictionItem(pred);
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPredictionItem(Map<String, dynamic> pred) {
    final stockId = pred['stock_id'] ?? '';
    final stockName = pred['stock_name'] ?? '';
    final predictedDir = pred['predicted_direction'] ?? '';
    final predictedChange = pred['predicted_change'] ?? 0.0;
    final actualChange = pred['actual_change'];
    final actualDir = pred['actual_direction'];
    final directionCorrect = pred['direction_correct'];
    final errorPercent = pred['error_percent'] ?? 0.0;

    final hasActual = actualChange != null;
    final isPredictUp = predictedDir == 'UP';
    final isActualUp = actualDir == 'UP';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: hasActual
            ? Border.all(
                color: directionCorrect == true ? Colors.green : Colors.red,
                width: 1.5,
              )
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                '$stockId $stockName',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              if (hasActual && directionCorrect != null)
                Icon(
                  directionCorrect ? Icons.check_circle : Icons.cancel,
                  color: directionCorrect ? Colors.green : Colors.red,
                  size: 20,
                ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('預測', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    Row(
                      children: [
                        Icon(
                          isPredictUp ? Icons.arrow_upward : Icons.arrow_downward,
                          color: isPredictUp ? Colors.red : Colors.green,
                          size: 16,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${predictedChange >= 0 ? '+' : ''}${predictedChange.toStringAsFixed(2)}%',
                          style: TextStyle(
                            color: isPredictUp ? Colors.red : Colors.green,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (hasActual) ...[
                const Icon(Icons.arrow_forward, color: Colors.grey, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('實際', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      Row(
                        children: [
                          Icon(
                            isActualUp ? Icons.arrow_upward : Icons.arrow_downward,
                            color: isActualUp ? Colors.red : Colors.green,
                            size: 16,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '${actualChange >= 0 ? '+' : ''}${actualChange.toStringAsFixed(2)}%',
                            style: TextStyle(
                              color: isActualUp ? Colors.red : Colors.green,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Text('誤差', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      Text(
                        '${errorPercent.toStringAsFixed(2)}%',
                        style: TextStyle(
                          color: errorPercent <= 1.5 ? Colors.green : Colors.orange,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ] else
                const Expanded(
                  child: Text(
                    '等待收盤數據',
                    style: TextStyle(color: Colors.grey, fontStyle: FontStyle.italic),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRecentRecords() {
    final stats = _statistics;
    if (stats == null) return const SizedBox.shrink();

    final records = (stats['records'] as List?) ?? [];
    if (records.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.history, color: Colors.purple),
                const SizedBox(width: 8),
                Text(
                  '最近預測記錄',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const Divider(),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: records.length,
              itemBuilder: (context, index) {
                final record = records[index];
                return _buildPredictionItem(Map<String, dynamic>.from(record));
              },
            ),
          ],
        ),
      ),
    );
  }
}
