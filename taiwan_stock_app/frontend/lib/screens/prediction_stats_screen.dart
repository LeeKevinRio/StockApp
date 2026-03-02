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
  String? _selectedMarket; // null: 全部, 'TW': 台股, 'US': 美股

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
        apiService.getPredictionStatistics(days: _selectedDays, market: _selectedMarket),
        apiService.getYesterdayPredictions(market: _selectedMarket),
        apiService.getTodayPredictions(market: _selectedMarket),
        apiService.getAllStocksPredictionStats(days: _selectedDays, market: _selectedMarket),
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
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (Navigator.of(context).canPop()) {
              Navigator.of(context).pop();
            } else {
              Navigator.of(context).pushReplacementNamed('/home');
            }
          },
        ),
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
        // 市場篩選器
        Container(
          color: Theme.of(context).scaffoldBackgroundColor,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              const Icon(Icons.filter_list, size: 18, color: Colors.grey),
              const SizedBox(width: 8),
              const Text('市場：', style: TextStyle(fontSize: 13, color: Colors.grey)),
              const SizedBox(width: 8),
              Expanded(
                child: SegmentedButton<String?>(
                  segments: const [
                    ButtonSegment(value: null, label: Text('全部')),
                    ButtonSegment(value: 'TW', label: Text('台股')),
                    ButtonSegment(value: 'US', label: Text('美股')),
                  ],
                  selected: {_selectedMarket},
                  onSelectionChanged: (values) {
                    setState(() {
                      _selectedMarket = values.first;
                    });
                    _loadData();
                  },
                  style: ButtonStyle(
                    visualDensity: VisualDensity.compact,
                    textStyle: WidgetStatePropertyAll(
                      const TextStyle(fontSize: 13),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const Divider(height: 1),
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
          _buildAccuracyGauge(),
          const SizedBox(height: 16),
          _buildOverallStats(),
          const SizedBox(height: 16),
          _buildWinRateStats(),
          const SizedBox(height: 24),
          _buildConfusionMatrix(),
          const SizedBox(height: 24),
          _buildErrorDistribution(),
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

  /// 準確度半圓儀表
  Widget _buildAccuracyGauge() {
    final stats = _statistics;
    if (stats == null) return const SizedBox.shrink();
    final accuracy = (stats['direction_accuracy'] ?? 0.0).toDouble();
    final total = stats['total_predictions'] ?? 0;
    if (total == 0) return const SizedBox.shrink();

    final color = accuracy >= 70
        ? Colors.green
        : accuracy >= 50
            ? Colors.orange
            : Colors.red;
    final label = accuracy >= 70
        ? '優秀'
        : accuracy >= 60
            ? '良好'
            : accuracy >= 50
                ? '一般'
                : '待改進';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const Text('方向預測準確率',
                style: TextStyle(fontSize: 14, color: Colors.grey)),
            const SizedBox(height: 16),
            SizedBox(
              width: 200,
              height: 120,
              child: Stack(
                alignment: Alignment.bottomCenter,
                children: [
                  SizedBox(
                    width: 200,
                    height: 120,
                    child: PieChart(
                      PieChartData(
                        startDegreeOffset: 180,
                        sections: [
                          PieChartSectionData(
                            value: accuracy,
                            color: color,
                            radius: 20,
                            showTitle: false,
                          ),
                          PieChartSectionData(
                            value: (100 - accuracy).toDouble(),
                            color: const Color(0xFF2C3A47),
                            radius: 20,
                            showTitle: false,
                          ),
                          // 下半部隱藏
                          PieChartSectionData(
                            value: 100,
                            color: Colors.transparent,
                            radius: 20,
                            showTitle: false,
                          ),
                        ],
                        sectionsSpace: 0,
                        centerSpaceRadius: 50,
                      ),
                    ),
                  ),
                  Positioned(
                    bottom: 0,
                    child: Column(
                      children: [
                        Text(
                          '${accuracy.toStringAsFixed(1)}%',
                          style: TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                        Text(label,
                            style: TextStyle(fontSize: 14, color: color)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 勝率 + 平均盈虧統計
  Widget _buildWinRateStats() {
    final records = _getSortedRecords();
    if (records.isEmpty) return const SizedBox.shrink();

    int upCorrect = 0, upWrong = 0, downCorrect = 0, downWrong = 0;
    double totalGain = 0, totalLoss = 0;
    int gainCount = 0, lossCount = 0;

    for (final r in records) {
      final predictedDir = r['predicted_direction'] ?? '';
      final dirCorrect = r['direction_correct'] ?? false;
      final actualChange = (r['actual_change'] ?? 0.0).toDouble();

      if (predictedDir == 'UP') {
        if (dirCorrect) {
          upCorrect++;
        } else {
          upWrong++;
        }
      } else {
        if (dirCorrect) {
          downCorrect++;
        } else {
          downWrong++;
        }
      }

      // 用「如果跟隨預測建議」的盈虧計算
      if (dirCorrect) {
        totalGain += actualChange.abs();
        gainCount++;
      } else {
        totalLoss += actualChange.abs();
        lossCount++;
      }
    }

    final avgGain = gainCount > 0 ? totalGain / gainCount : 0.0;
    final avgLoss = lossCount > 0 ? totalLoss / lossCount : 0.0;
    final profitFactor = avgLoss > 0 ? avgGain / avgLoss : 0.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.emoji_events, color: Colors.amber),
                const SizedBox(width: 8),
                Text('勝率與盈虧統計',
                    style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const Divider(),
            Row(
              children: [
                Expanded(
                  child: _buildMiniStat('預測漲正確',
                      '$upCorrect', Colors.green),
                ),
                Expanded(
                  child: _buildMiniStat('預測漲錯誤',
                      '$upWrong', Colors.red),
                ),
                Expanded(
                  child: _buildMiniStat('預測跌正確',
                      '$downCorrect', Colors.green),
                ),
                Expanded(
                  child: _buildMiniStat('預測跌錯誤',
                      '$downWrong', Colors.red),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildMiniStat('平均正確盈幅',
                      '+${avgGain.toStringAsFixed(2)}%', Colors.green),
                ),
                Expanded(
                  child: _buildMiniStat('平均錯誤虧幅',
                      '-${avgLoss.toStringAsFixed(2)}%', Colors.red),
                ),
                Expanded(
                  child: _buildMiniStat('盈虧比',
                      profitFactor.toStringAsFixed(2), Colors.blue),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMiniStat(String label, String value, Color color) {
    return Column(
      children: [
        Text(value,
            style: TextStyle(
                fontSize: 18, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 4),
        Text(label,
            style: const TextStyle(fontSize: 11, color: Colors.grey),
            textAlign: TextAlign.center),
      ],
    );
  }

  /// 混淆矩陣（預測 vs 實際方向）
  Widget _buildConfusionMatrix() {
    final records = _getSortedRecords();
    if (records.isEmpty) return const SizedBox.shrink();

    int predUpActUp = 0, predUpActDown = 0;
    int predDownActUp = 0, predDownActDown = 0;

    for (final r in records) {
      final pred = r['predicted_direction'] ?? '';
      final actual = r['actual_direction'] ?? '';
      if (pred == 'UP' && actual == 'UP') predUpActUp++;
      if (pred == 'UP' && actual == 'DOWN') predUpActDown++;
      if (pred == 'DOWN' && actual == 'UP') predDownActUp++;
      if (pred == 'DOWN' && actual == 'DOWN') predDownActDown++;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.grid_on, color: Colors.deepPurple),
                const SizedBox(width: 8),
                Text('混淆矩陣（預測 vs 實際）',
                    style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const Divider(),
            Table(
              border: TableBorder.all(color: const Color(0xFF455A64)),
              children: [
                TableRow(
                  decoration: const BoxDecoration(color: Color(0xFF2C3A47)),
                  children: const [
                    Padding(
                      padding: EdgeInsets.all(8),
                      child: Text('', textAlign: TextAlign.center),
                    ),
                    Padding(
                      padding: EdgeInsets.all(8),
                      child: Text('實際漲',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                    Padding(
                      padding: EdgeInsets.all(8),
                      child: Text('實際跌',
                          textAlign: TextAlign.center,
                          style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
                TableRow(children: [
                  const Padding(
                    padding: EdgeInsets.all(8),
                    child: Text('預測漲',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  _buildMatrixCell(predUpActUp, true),
                  _buildMatrixCell(predUpActDown, false),
                ]),
                TableRow(children: [
                  const Padding(
                    padding: EdgeInsets.all(8),
                    child: Text('預測跌',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  _buildMatrixCell(predDownActUp, false),
                  _buildMatrixCell(predDownActDown, true),
                ]),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMatrixCell(int count, bool isCorrect) {
    return Container(
      padding: const EdgeInsets.all(12),
      color: isCorrect
          ? Colors.green.withValues(alpha: 0.1)
          : Colors.red.withValues(alpha: 0.1),
      child: Text(
        '$count',
        textAlign: TextAlign.center,
        style: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.bold,
          color: isCorrect ? Colors.green : Colors.red,
        ),
      ),
    );
  }

  /// 誤差分布圖（BarChart）
  Widget _buildErrorDistribution() {
    final records = _getSortedRecords();
    if (records.length < 3) return const SizedBox.shrink();

    // 分組統計誤差分布
    final buckets = <String, int>{
      '0-0.5%': 0,
      '0.5-1%': 0,
      '1-2%': 0,
      '2-3%': 0,
      '3-5%': 0,
      '>5%': 0,
    };
    final bucketKeys = buckets.keys.toList();

    for (final r in records) {
      final error = (r['error_percent'] ?? 0.0).toDouble().abs();
      if (error <= 0.5) {
        buckets['0-0.5%'] = buckets['0-0.5%']! + 1;
      } else if (error <= 1) {
        buckets['0.5-1%'] = buckets['0.5-1%']! + 1;
      } else if (error <= 2) {
        buckets['1-2%'] = buckets['1-2%']! + 1;
      } else if (error <= 3) {
        buckets['2-3%'] = buckets['2-3%']! + 1;
      } else if (error <= 5) {
        buckets['3-5%'] = buckets['3-5%']! + 1;
      } else {
        buckets['>5%'] = buckets['>5%']! + 1;
      }
    }

    final maxVal = buckets.values.fold(0, (a, b) => a > b ? a : b).toDouble();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.bar_chart, color: Colors.teal),
                const SizedBox(width: 8),
                Text('預測誤差分布',
                    style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const Divider(),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: maxVal + 1,
                  gridData: const FlGridData(show: false),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        getTitlesWidget: (value, _) => Text(
                          '${value.toInt()}',
                          style: const TextStyle(
                              fontSize: 10, color: Colors.grey),
                        ),
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, _) {
                          final idx = value.toInt();
                          if (idx < 0 || idx >= bucketKeys.length) {
                            return const SizedBox.shrink();
                          }
                          return Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(bucketKeys[idx],
                                style: const TextStyle(
                                    fontSize: 9, color: Colors.grey)),
                          );
                        },
                      ),
                    ),
                  ),
                  barGroups: bucketKeys.asMap().entries.map((entry) {
                    final idx = entry.key;
                    final count = buckets[entry.value]!;
                    final barColor = idx <= 1
                        ? Colors.green
                        : idx <= 2
                            ? Colors.orange
                            : Colors.red;
                    return BarChartGroupData(
                      x: idx,
                      barRods: [
                        BarChartRodData(
                          toY: count.toDouble(),
                          color: barColor,
                          width: 24,
                          borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(4)),
                        ),
                      ],
                    );
                  }).toList(),
                ),
              ),
            ),
          ],
        ),
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
            color: const Color(0xFF1B3A2D),
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
          backgroundColor: accuracy >= 50 ? const Color(0xFF1B3A2D) : const Color(0xFF3A1B1B),
          child: Text(
            '${accuracy.toInt()}%',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: accuracy >= 50 ? Colors.green : Colors.red,
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
                color: market == 'US' ? Colors.blue.withValues(alpha: 0.2) : Colors.orange.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                market,
                style: TextStyle(
                  fontSize: 10,
                  color: market == 'US' ? Colors.blue : Colors.orange,
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
        border: Border(bottom: BorderSide(color: const Color(0xFF455A64))),
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
                      color: const Color(0xFF455A64),
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
                        color: Colors.red.withValues(alpha: 0.5),
                        strokeWidth: 1,
                        dashArray: [5, 5],
                        label: HorizontalLineLabel(
                          show: true,
                          alignment: Alignment.topRight,
                          style: TextStyle(fontSize: 9, color: Colors.red.withValues(alpha: 0.7)),
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
                      color: const Color(0xFF455A64),
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
                        color: const Color(0xFF455A64),
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
    final madeToday = (data['made_today'] as List?) ?? [];
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

    // 沒有任何預測資料時不顯示
    final hasPredictions = predictions.isNotEmpty || madeToday.isNotEmpty;

    return Column(
      children: [
        // 今日產生的預測（pending）
        if (madeToday.isNotEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.auto_awesome, color: Colors.amber),
                      const SizedBox(width: 8),
                      Text(
                        '今日產生的預測',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.blue.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${madeToday.length} 筆',
                          style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                  const Divider(),
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: madeToday.length,
                    itemBuilder: (context, index) {
                      final pred = madeToday[index];
                      return _buildPendingPredictionItem(pred);
                    },
                  ),
                ],
              ),
            ),
          ),
        // 到期的預測結果（已驗證）
        if (predictions.isNotEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.fact_check, color: Colors.green),
                      const SizedBox(width: 8),
                      Text(
                        '今日到期驗證 ($displayDate)',
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
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                        ),
                    ],
                  ),
                  const Divider(),
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
          ),
        // 完全沒有預測時的提示
        if (!hasPredictions)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Center(
                child: Column(
                  children: [
                    const Icon(Icons.info_outline, color: Colors.grey, size: 32),
                    const SizedBox(height: 8),
                    const Text('今日無預測記錄'),
                    const SizedBox(height: 4),
                    Text(
                      '請先查看股票的 AI 建議，系統會自動記錄預測',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildPendingPredictionItem(Map<String, dynamic> pred) {
    final stockId = pred['stock_id'] ?? '';
    final stockName = pred['stock_name'] ?? '';
    final market = pred['market'] ?? 'TW';
    final predictedDir = pred['predicted_direction'] ?? '';
    final predictedChange = (pred['predicted_change'] ?? 0.0).toDouble();
    final targetDate = pred['target_date'] ?? '';
    final status = pred['status'] ?? 'pending';
    final isPredictUp = predictedDir == 'UP';
    final isVerified = status == 'verified';

    // 如果已驗證，用原有的 _buildPredictionItem 顯示
    if (isVerified) return _buildPredictionItem(pred);

    // 格式化目標日期
    String displayTarget = targetDate;
    if (targetDate.isNotEmpty) {
      try {
        final dt = DateTime.parse(targetDate);
        displayTarget = '${dt.month}/${dt.day}';
      } catch (_) {}
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue.withValues(alpha: 0.3), width: 1),
      ),
      child: Row(
        children: [
          // 股票資訊
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      '$stockId $stockName',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: market == 'US' ? Colors.blue.withValues(alpha: 0.2) : Colors.orange.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        market,
                        style: TextStyle(
                          fontSize: 10,
                          color: market == 'US' ? Colors.blue : Colors.orange,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Icon(
                      isPredictUp ? Icons.arrow_upward : Icons.arrow_downward,
                      color: isPredictUp ? Colors.red : Colors.green,
                      size: 16,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '預測${isPredictUp ? "漲" : "跌"} ${predictedChange >= 0 ? "+" : ""}${predictedChange.toStringAsFixed(2)}%',
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
          // 目標日期 + 狀態
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '目標 $displayTarget',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.amber.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  '等待驗證',
                  style: TextStyle(fontSize: 11, color: Colors.amber, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ],
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
