import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../providers/market_provider.dart';
import '../providers/locale_provider.dart';
import '../models/stock.dart';

class BacktestScreen extends StatefulWidget {
  const BacktestScreen({super.key});

  @override
  State<BacktestScreen> createState() => _BacktestScreenState();
}

class _BacktestScreenState extends State<BacktestScreen> {
  // 設定狀態
  final _searchController = TextEditingController();
  List<Stock> _searchResults = [];
  bool _isSearching = false;
  String? _selectedStockId;
  String? _selectedStockName;

  List<Map<String, dynamic>> _strategies = [];
  String? _selectedStrategy;
  Map<String, dynamic> _strategyParams = {};

  DateTime _startDate = DateTime.now().subtract(const Duration(days: 365));
  DateTime _endDate = DateTime.now();
  final _capitalController = TextEditingController(text: '1000000');

  // 結果狀態
  bool _isLoading = false;
  bool _isLoadingStrategies = true;
  Map<String, dynamic>? _result;
  String? _error;
  int _selectedTab = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadStrategies());
  }

  @override
  void dispose() {
    _searchController.dispose();
    _capitalController.dispose();
    super.dispose();
  }

  Future<void> _loadStrategies() async {
    try {
      final api = context.read<ApiService>();
      final strategies = await api.getBacktestStrategies();
      if (mounted) {
        setState(() {
          _strategies = strategies;
          _isLoadingStrategies = false;
          if (strategies.isNotEmpty) {
            _selectedStrategy = strategies[0]['name'] as String?;
            _strategyParams = Map<String, dynamic>.from(
              strategies[0]['default_params'] as Map? ?? {},
            );
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingStrategies = false;
          _error = '載入策略失敗: $e';
        });
      }
    }
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

  void _selectStock(Stock stock) {
    setState(() {
      _selectedStockId = stock.stockId;
      _selectedStockName = '${stock.stockId} ${stock.name}';
      _searchResults = [];
      _searchController.clear();
    });
  }

  void _onStrategyChanged(String? name) {
    if (name == null) return;
    final strat = _strategies.firstWhere((s) => s['name'] == name);
    setState(() {
      _selectedStrategy = name;
      _strategyParams = Map<String, dynamic>.from(
        strat['default_params'] as Map? ?? {},
      );
    });
  }

  Future<void> _pickDateRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2010),
      lastDate: DateTime.now(),
      initialDateRange: DateTimeRange(start: _startDate, end: _endDate),
      locale: const Locale('zh', 'TW'),
    );
    if (picked != null) {
      setState(() {
        _startDate = picked.start;
        _endDate = picked.end;
      });
    }
  }

  Future<void> _runBacktest() async {
    if (_selectedStockId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請先選擇股票')),
      );
      return;
    }
    if (_selectedStrategy == null) return;

    setState(() {
      _isLoading = true;
      _error = null;
      _result = null;
    });

    try {
      final api = context.read<ApiService>();
      final market = context.read<MarketProvider>().marketCode;
      final capital = double.tryParse(_capitalController.text) ?? 1000000;
      final fmt = DateFormat('yyyy-MM-dd');

      final result = await api.runBacktest(
        stockId: _selectedStockId!,
        strategy: _selectedStrategy!,
        startDate: fmt.format(_startDate),
        endDate: fmt.format(_endDate),
        market: market,
        params: _strategyParams,
        initialCapital: capital,
      );

      if (mounted) {
        setState(() {
          _result = result;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = '回測失敗: $e';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // isEn 由「語系」決定（系統級設定），與市場無關
    final isEn = context.watch<LocaleProvider>().isEnglish;

    return Scaffold(
      appBar: AppBar(
        title: Text(isEn ? 'Strategy Backtest' : '策略回測'),
      ),
      body: _isLoadingStrategies
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _buildSettingsSection(isEn),
                  if (_isLoading)
                    const Padding(
                      padding: EdgeInsets.all(32),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: Card(
                        color: Colors.red.shade50,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Text(_error!,
                              style: TextStyle(color: Colors.red.shade700)),
                        ),
                      ),
                    ),
                  if (_result != null) ...[
                    const SizedBox(height: 16),
                    _buildResultTabs(isEn),
                  ],
                ],
              ),
            ),
    );
  }

  // ---- 設定區 ----

  Widget _buildSettingsSection(bool isEn) {
    // 幣別前綴是市場決定的資料，不隨語系變動
    final currencyPrefix = context.watch<MarketProvider>().currencySymbol;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(isEn ? 'Backtest Settings' : '回測設定',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),

            // 股票搜尋
            TextField(
              controller: _searchController,
              decoration: InputDecoration(
                labelText: isEn ? 'Search Stock' : '搜尋股票',
                hintText: isEn ? 'Stock ID or name' : '輸入股票代碼或名稱',
                prefixIcon: const Icon(Icons.search),
                border: const OutlineInputBorder(),
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

            // 搜尋結果下拉
            if (_searchResults.isNotEmpty)
              Container(
                constraints: const BoxConstraints(maxHeight: 200),
                margin: const EdgeInsets.only(top: 4),
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: const [
                    BoxShadow(color: Colors.black12, blurRadius: 4)
                  ],
                ),
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: _searchResults.length,
                  itemBuilder: (context, index) {
                    final stock = _searchResults[index];
                    return ListTile(
                      dense: true,
                      title: Text('${stock.stockId} ${stock.name}'),
                      onTap: () => _selectStock(stock),
                    );
                  },
                ),
              ),

            // 已選股票
            if (_selectedStockName != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Chip(
                  label: Text(_selectedStockName!),
                  deleteIcon: const Icon(Icons.close, size: 18),
                  onDeleted: () => setState(() {
                    _selectedStockId = null;
                    _selectedStockName = null;
                  }),
                  backgroundColor: Colors.blue.withAlpha(30),
                ),
              ),

            const SizedBox(height: 12),

            // 策略選擇
            DropdownButtonFormField<String>(
              initialValue: _selectedStrategy,
              decoration: InputDecoration(
                labelText: isEn ? 'Strategy' : '策略',
                border: const OutlineInputBorder(),
              ),
              items: _strategies.map((s) {
                return DropdownMenuItem<String>(
                  value: s['name'] as String,
                  child: Text(isEn
                      ? (s['name'] as String)
                      : (s['display_name'] as String? ?? s['name'] as String)),
                );
              }).toList(),
              onChanged: _onStrategyChanged,
            ),

            // 策略參數
            if (_strategyParams.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(isEn ? 'Parameters' : '參數',
                  style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 8),
              Wrap(
                spacing: 12,
                runSpacing: 8,
                children: _strategyParams.entries.map((e) {
                  return SizedBox(
                    width: 140,
                    child: TextFormField(
                      initialValue: e.value.toString(),
                      decoration: InputDecoration(
                        labelText: e.key,
                        border: const OutlineInputBorder(),
                        isDense: true,
                      ),
                      keyboardType: TextInputType.number,
                      onChanged: (v) {
                        final numVal = num.tryParse(v);
                        if (numVal != null) {
                          _strategyParams[e.key] = numVal;
                        }
                      },
                    ),
                  );
                }).toList(),
              ),
            ],

            const SizedBox(height: 12),

            // 日期範圍
            InkWell(
              onTap: _pickDateRange,
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: isEn ? 'Date Range' : '日期範圍',
                  border: const OutlineInputBorder(),
                  suffixIcon: const Icon(Icons.calendar_today),
                ),
                child: Text(
                  '${DateFormat('yyyy-MM-dd').format(_startDate)} ~ ${DateFormat('yyyy-MM-dd').format(_endDate)}',
                ),
              ),
            ),

            const SizedBox(height: 12),

            // 初始資金（幣別跟隨「市場」，文字標籤跟隨「語系」）
            TextField(
              controller: _capitalController,
              decoration: InputDecoration(
                labelText: isEn ? 'Initial Capital' : '初始資金',
                border: const OutlineInputBorder(),
                prefixText: '$currencyPrefix ',
              ),
              keyboardType: TextInputType.number,
            ),

            const SizedBox(height: 16),

            // 開始回測按鈕
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _runBacktest,
                icon: const Icon(Icons.speed),
                label: Text(isEn ? 'Run Backtest' : '開始回測'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---- 結果區 ----

  Widget _buildResultTabs(bool isEn) {
    final tabLabels = isEn
        ? ['Overview', 'Equity Curve', 'Trades']
        : ['總覽', '權益曲線', '交易紀錄'];

    return Column(
      children: [
        // Tab 選擇
        Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            children: List.generate(3, (i) {
              final selected = _selectedTab == i;
              return Expanded(
                child: InkWell(
                  onTap: () => setState(() => _selectedTab = i),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(
                      border: Border(
                        bottom: BorderSide(
                          color: selected ? Colors.blue : Colors.transparent,
                          width: 2,
                        ),
                      ),
                    ),
                    child: Text(
                      tabLabels[i],
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontWeight:
                            selected ? FontWeight.bold : FontWeight.normal,
                        color: selected ? Colors.blue : null,
                      ),
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
        const SizedBox(height: 8),

        // Tab 內容
        if (_selectedTab == 0) _buildOverviewTab(isEn),
        if (_selectedTab == 1) _buildEquityCurveTab(isEn),
        if (_selectedTab == 2) _buildTradesTab(isEn),
      ],
    );
  }

  // ---- Tab 1: 總覽 ----

  Widget _buildOverviewTab(bool isEn) {
    final metrics = _result!['metrics'] as Map<String, dynamic>? ?? {};
    final stockName = _result!['stock_name'] ?? _result!['stock_id'] ?? '';
    final stratName = _result!['strategy'] ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 標題
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                const Icon(Icons.analytics, color: Colors.blue),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '$stockName — $stratName',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),

        // 績效指標卡片
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
          childAspectRatio: 2.2,
          children: [
            _metricCard(
              isEn ? 'Total Return' : '總報酬率',
              '${metrics['total_return'] ?? 0}%',
              (metrics['total_return'] ?? 0) >= 0
                  ? Colors.green
                  : Colors.red,
            ),
            _metricCard(
              isEn ? 'Annualized' : '年化報酬',
              '${metrics['annualized_return'] ?? 0}%',
              (metrics['annualized_return'] ?? 0) >= 0
                  ? Colors.green
                  : Colors.red,
            ),
            _metricCard(
              isEn ? 'Max Drawdown' : '最大回撤',
              '${metrics['max_drawdown'] ?? 0}%',
              Colors.orange,
            ),
            _metricCard(
              isEn ? 'Sharpe Ratio' : 'Sharpe',
              '${metrics['sharpe_ratio'] ?? 0}',
              (metrics['sharpe_ratio'] ?? 0) >= 1
                  ? Colors.green
                  : Colors.grey,
            ),
            _metricCard(
              isEn ? 'Win Rate' : '勝率',
              '${metrics['win_rate'] ?? 0}%',
              (metrics['win_rate'] ?? 0) >= 50
                  ? Colors.green
                  : Colors.red,
            ),
            _metricCard(
              isEn ? 'Profit Factor' : '獲利因子',
              '${metrics['profit_factor'] ?? 0}',
              (metrics['profit_factor'] ?? 0) >= 1
                  ? Colors.green
                  : Colors.red,
            ),
            _metricCard(
              isEn ? 'Total Trades' : '交易次數',
              '${metrics['total_trades'] ?? 0}',
              Colors.blue,
            ),
            _metricCard(
              isEn ? 'Avg Holding' : '平均持倉',
              '${metrics['avg_holding_days'] ?? 0} ${isEn ? "days" : "天"}',
              Colors.blueGrey,
            ),
          ],
        ),
      ],
    );
  }

  Widget _metricCard(String label, String value, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style: Theme.of(context).textTheme.bodySmall,
                overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: color,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  // ---- Tab 2: 權益曲線 ----

  Widget _buildEquityCurveTab(bool isEn) {
    final curve = (_result!['equity_curve'] as List<dynamic>?)
            ?.cast<Map<String, dynamic>>() ??
        [];
    if (curve.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(32),
        child: Center(child: Text('無權益曲線資料')),
      );
    }

    // 準備圖表資料
    final spots = <FlSpot>[];
    final dates = <String>[];
    for (int i = 0; i < curve.length; i++) {
      final eq = (curve[i]['equity'] as num?)?.toDouble() ?? 0;
      spots.add(FlSpot(i.toDouble(), eq));
      dates.add(curve[i]['date'] as String? ?? '');
    }

    final minY = spots.map((s) => s.y).reduce((a, b) => a < b ? a : b);
    final maxY = spots.map((s) => s.y).reduce((a, b) => a > b ? a : b);
    final padding = (maxY - minY) * 0.1;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(isEn ? 'Equity Curve' : '權益曲線',
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 16),
            SizedBox(
              height: 300,
              child: LineChart(
                LineChartData(
                  gridData: const FlGridData(show: true),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 60,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            _formatNumber(value),
                            style: const TextStyle(fontSize: 10),
                          );
                        },
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: (spots.length / 5).ceilToDouble(),
                        getTitlesWidget: (value, meta) {
                          final idx = value.toInt();
                          if (idx < 0 || idx >= dates.length) {
                            return const SizedBox.shrink();
                          }
                          final d = dates[idx];
                          return Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Text(
                              d.length >= 7 ? d.substring(5) : d,
                              style: const TextStyle(fontSize: 9),
                            ),
                          );
                        },
                      ),
                    ),
                    topTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: true),
                  minX: 0,
                  maxX: (spots.length - 1).toDouble(),
                  minY: minY - padding,
                  maxY: maxY + padding,
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: false,
                      color: Colors.blue,
                      barWidth: 2,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        color: Colors.blue.withAlpha(30),
                      ),
                    ),
                  ],
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (spots) {
                        return spots.map((s) {
                          final idx = s.x.toInt();
                          final date =
                              idx >= 0 && idx < dates.length ? dates[idx] : '';
                          return LineTooltipItem(
                            '$date\n${_formatNumber(s.y)}',
                            const TextStyle(
                                color: Colors.white, fontSize: 12),
                          );
                        }).toList();
                      },
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---- Tab 3: 交易紀錄 ----

  Widget _buildTradesTab(bool isEn) {
    final trades = (_result!['trades'] as List<dynamic>?)
            ?.cast<Map<String, dynamic>>() ??
        [];

    if (trades.isEmpty) {
      return Padding(
        padding: const EdgeInsets.all(32),
        child: Center(child: Text(isEn ? 'No trades' : '無交易紀錄')),
      );
    }

    return Card(
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: trades.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final t = trades[index];
          final pnl = (t['pnl'] as num?)?.toDouble() ?? 0;
          final returnPct = (t['return_pct'] as num?)?.toDouble() ?? 0;
          final isProfit = pnl >= 0;

          return ListTile(
            leading: CircleAvatar(
              backgroundColor:
                  isProfit ? Colors.green.shade50 : Colors.red.shade50,
              child: Icon(
                isProfit ? Icons.trending_up : Icons.trending_down,
                color: isProfit ? Colors.green : Colors.red,
                size: 20,
              ),
            ),
            title: Row(
              children: [
                Text('${t['entry_date']}',
                    style: const TextStyle(fontSize: 13)),
                const Icon(Icons.arrow_forward, size: 14),
                Text('${t['exit_date']}',
                    style: const TextStyle(fontSize: 13)),
              ],
            ),
            subtitle: Text(
              '${isEn ? "Entry" : "買"} ${t['entry_price']} → '
              '${isEn ? "Exit" : "賣"} ${t['exit_price']}  '
              '(${t['holding_days']} ${isEn ? "days" : "天"})',
              style: const TextStyle(fontSize: 12),
            ),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${returnPct >= 0 ? "+" : ""}${returnPct.toStringAsFixed(2)}%',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: isProfit ? Colors.green : Colors.red,
                  ),
                ),
                Text(
                  '${pnl >= 0 ? "+" : ""}${_formatNumber(pnl)}',
                  style: TextStyle(
                    fontSize: 11,
                    color: isProfit ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  // ---- 工具 ----

  String _formatNumber(double value) {
    if (value.abs() >= 1e8) {
      return '${(value / 1e8).toStringAsFixed(1)}億';
    } else if (value.abs() >= 1e4) {
      return '${(value / 1e4).toStringAsFixed(1)}萬';
    }
    return NumberFormat('#,##0').format(value.round());
  }
}
