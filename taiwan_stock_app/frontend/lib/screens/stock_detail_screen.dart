import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/stock.dart';
import '../models/stock_history.dart';
import '../widgets/candlestick_chart.dart';
import '../widgets/indicator_charts/indicators_tab_view.dart';
import '../widgets/news_card.dart';
import '../widgets/sentiment_view.dart';
import '../widgets/fundamental_card.dart';
import '../widgets/dividend_history.dart';
import '../widgets/institutional_chart.dart';
import '../widgets/margin_chart.dart';

class StockDetailScreen extends StatefulWidget {
  final String stockId;
  final String market;  // 'TW' or 'US'

  const StockDetailScreen({
    super.key,
    required this.stockId,
    this.market = 'TW',
  });

  @override
  State<StockDetailScreen> createState() => _StockDetailScreenState();
}

class _StockDetailScreenState extends State<StockDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Stock? _stock;
  bool _isLoading = true;
  String? _error;

  bool get isUSStock => widget.market.toUpperCase() == 'US';
  String get currencySymbol => isUSStock ? '\$' : 'NT\$';

  @override
  void initState() {
    super.initState();
    // 8 tabs for TW stocks (with 籌碼), 7 tabs for US stocks (without 籌碼)
    _tabController = TabController(length: isUSStock ? 7 : 8, vsync: this);
    _loadStockData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadStockData() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final apiService = Provider.of<ApiService>(context, listen: false);
      // Use stock detail API with market parameter
      final response = await apiService.getStockDetail(widget.stockId, market: widget.market);

      setState(() {
        _stock = Stock(
          stockId: response['stock_id'] ?? response['symbol'] ?? widget.stockId,
          name: response['name'] ?? widget.stockId,
          market: response['market'] ?? response['exchange'],
          industry: response['industry'],
          marketRegion: response['market_region'] ?? widget.market,
          sector: response['sector'],
          exchange: response['exchange'],
        );
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = '加載失敗：$e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_stock?.name ?? widget.stockId),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: [
            const Tab(text: '概覽'),
            const Tab(text: 'K線'),
            const Tab(text: '技術分析'),
            const Tab(text: '基本面'),
            if (!isUSStock) const Tab(text: '籌碼'),
            const Tab(text: 'AI建議'),
            const Tab(text: '新聞'),
            const Tab(text: '社群'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 64, color: Colors.grey),
                      const SizedBox(height: 16),
                      Text(_error!),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadStockData,
                        child: const Text('重試'),
                      ),
                    ],
                  ),
                )
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildOverviewTab(),
                    _buildKLineTab(),
                    _buildTechnicalAnalysisTab(),
                    _buildFundamentalTab(),
                    if (!isUSStock) _buildChipAnalysisTab(),
                    _buildAISuggestionTab(),
                    _buildNewsTab(),
                    _buildSocialTab(),
                  ],
                ),
    );
  }

  Widget _buildOverviewTab() {
    if (_stock == null) return const SizedBox();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildInfoCard(
            '基本資訊',
            [
              _buildInfoRow('股票代碼', _stock!.stockId),
              _buildInfoRow('公司名稱', _stock!.name),
              _buildInfoRow('市場類別', _stock!.market ?? '-'),
              if (_stock!.industry != null)
                _buildInfoRow('產業類別', _stock!.industry!),
            ],
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '⚠️ 投資風險警告',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.orange,
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    '本系統提供的投資建議、價格預測、技術分析及社群輿論資訊僅供參考，'
                    '不構成任何投資決策建議。投資有風險，過去的績效不代表未來表現。',
                    style: TextStyle(fontSize: 14, height: 1.5),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    '請務必：',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  _buildBulletPoint('進行獨立研究和盡職調查'),
                  _buildBulletPoint('諮詢專業財務顧問'),
                  _buildBulletPoint('評估個人風險承受能力'),
                  _buildBulletPoint('謹慎使用槓桿和衍生品'),
                  const SizedBox(height: 12),
                  const Text(
                    '您須自行承擔所有投資決策的責任和後果。',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.red,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard(String title, List<Widget> children) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const Divider(),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 14,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBulletPoint(String text) {
    return Padding(
      padding: const EdgeInsets.only(left: 16, bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('• ', style: TextStyle(fontSize: 16)),
          Expanded(
            child: Text(text, style: const TextStyle(fontSize: 14)),
          ),
        ],
      ),
    );
  }

  Widget _buildKLineTab() {
    return _KLineTabContent(stockId: widget.stockId, market: widget.market);
  }

  Widget _buildTechnicalAnalysisTab() {
    return IndicatorsTabView(stockId: widget.stockId, market: widget.market);
  }

  Widget _buildAISuggestionTab() {
    return _StockAISuggestionView(stockId: widget.stockId, market: widget.market);
  }

  Widget _buildNewsTab() {
    return NewsListView(stockId: widget.stockId, market: widget.market);
  }

  Widget _buildSocialTab() {
    return SentimentView(stockId: widget.stockId, market: widget.market);
  }

  Widget _buildFundamentalTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          FundamentalCard(stockId: widget.stockId, market: widget.market),
          const SizedBox(height: 16),
          DividendHistory(stockId: widget.stockId, market: widget.market),
        ],
      ),
    );
  }

  Widget _buildChipAnalysisTab() {
    // 籌碼分析 - 僅限台股
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          InstitutionalChart(stockId: widget.stockId),
          const SizedBox(height: 16),
          MarginChart(stockId: widget.stockId),
        ],
      ),
    );
  }
}

/// Stateful widget for K-line tab with period selection
class _KLineTabContent extends StatefulWidget {
  final String stockId;
  final String market;

  const _KLineTabContent({required this.stockId, this.market = 'TW'});

  @override
  State<_KLineTabContent> createState() => _KLineTabContentState();
}

class _KLineTabContentState extends State<_KLineTabContent> {
  String _selectedPeriod = 'day';
  int _days = 60;
  Future<List<StockHistory>>? _dataFuture;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void _loadData() {
    final apiService = Provider.of<ApiService>(context, listen: false);
    _dataFuture = apiService.getStockHistory(
      widget.stockId,
      days: _days,
      period: _selectedPeriod,
      market: widget.market,
    );
  }

  void _onPeriodChanged(String period) {
    setState(() {
      _selectedPeriod = period;
      // Adjust days based on period
      switch (period) {
        case 'day':
          _days = 60;
          break;
        case 'week':
          _days = 52; // ~1 year
          break;
        case 'month':
          _days = 24; // 2 years
          break;
      }
      _loadData();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Period selector
        _buildPeriodSelector(context),
        // Chart content
        Expanded(
          child: FutureBuilder<List<StockHistory>>(
            future: _dataFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }

              if (snapshot.hasError) {
                String errorMsg = '載入K線數據失敗';
                String errorDetail = '';

                if (snapshot.error is ApiException) {
                  final apiError = snapshot.error as ApiException;
                  errorMsg = '載入失敗 (${apiError.statusCode})';
                  errorDetail = apiError.message;
                } else {
                  errorDetail = snapshot.error.toString();
                }

                return Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.error_outline,
                          size: 64,
                          color: Theme.of(context).colorScheme.error,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          errorMsg,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          errorDetail,
                          style: TextStyle(
                            fontSize: 14,
                            color: Theme.of(context).textTheme.bodySmall?.color,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          onPressed: () => setState(() => _loadData()),
                          icon: const Icon(Icons.refresh),
                          label: const Text('重新載入'),
                        ),
                      ],
                    ),
                  ),
                );
              }

              if (!snapshot.hasData || snapshot.data!.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.show_chart,
                        size: 64,
                        color: Theme.of(context).disabledColor,
                      ),
                      const SizedBox(height: 16),
                      const Text('暫無K線數據'),
                    ],
                  ),
                );
              }

              return CandlestickChart(
                data: snapshot.data!,
                showVolume: true,
                enableZoom: true,
                enableCrosshair: true,
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildPeriodSelector(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildPeriodButton(context, 'day', '日K'),
          const SizedBox(width: 8),
          _buildPeriodButton(context, 'week', '週K'),
          const SizedBox(width: 8),
          _buildPeriodButton(context, 'month', '月K'),
        ],
      ),
    );
  }

  Widget _buildPeriodButton(BuildContext context, String period, String label) {
    final isSelected = _selectedPeriod == period;
    return GestureDetector(
      onTap: () => _onPeriodChanged(period),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected
              ? Theme.of(context).primaryColor
              : Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected
                ? Theme.of(context).primaryColor
                : Theme.of(context).dividerColor,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected
                ? Colors.white
                : Theme.of(context).textTheme.bodyMedium?.color,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

/// Widget for displaying AI suggestion for a specific stock
class _StockAISuggestionView extends StatefulWidget {
  final String stockId;
  final String market;

  const _StockAISuggestionView({required this.stockId, this.market = 'TW'});

  @override
  State<_StockAISuggestionView> createState() => _StockAISuggestionViewState();
}

class _StockAISuggestionViewState extends State<_StockAISuggestionView> {
  Map<String, dynamic>? _suggestion;
  bool _isLoading = true;
  String? _error;

  bool get isUSStock => widget.market.toUpperCase() == 'US';
  String get currencySymbol => isUSStock ? '\$' : 'NT\$';

  @override
  void initState() {
    super.initState();
    _loadSuggestion();
  }

  Future<void> _loadSuggestion() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final suggestion = await apiService.getStockSuggestion(widget.stockId, market: widget.market);

      setState(() {
        _suggestion = {
          'stock_id': suggestion.stockId,
          'name': suggestion.name,
          'suggestion': suggestion.suggestion,
          'confidence': suggestion.confidence,
          'reasoning': suggestion.reasoning,
          'target_price': suggestion.targetPrice,
          'stop_loss_price': suggestion.stopLossPrice,
          'key_factors': suggestion.keyFactors,
          'report_date': suggestion.reportDate,
        };
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
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('AI 正在分析這支股票...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.grey),
              const SizedBox(height: 16),
              Text('無法獲取AI建議', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadSuggestion,
                icon: const Icon(Icons.refresh),
                label: const Text('重試'),
              ),
            ],
          ),
        ),
      );
    }

    if (_suggestion == null) {
      return const Center(child: Text('暫無AI建議'));
    }

    final suggestion = _suggestion!['suggestion'] as String? ?? 'HOLD';
    final confidence = (_suggestion!['confidence'] as num? ?? 0).toDouble();
    final reasoning = _suggestion!['reasoning'] as String? ?? '';
    final targetPrice = _suggestion!['target_price'] as num?;
    final stopLossPrice = _suggestion!['stop_loss_price'] as num?;

    final suggestionColor = _getSuggestionColor(suggestion);
    final suggestionIcon = _getSuggestionIcon(suggestion);

    return RefreshIndicator(
      onRefresh: _loadSuggestion,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // AI 建議卡片
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Icon(suggestionIcon, size: 64, color: suggestionColor),
                    const SizedBox(height: 12),
                    Text(
                      _getSuggestionText(suggestion),
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: suggestionColor,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        const Text('信心度：'),
                        Expanded(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: confidence,
                              backgroundColor: Colors.grey[300],
                              valueColor: AlwaysStoppedAnimation<Color>(suggestionColor),
                              minHeight: 8,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '${(confidence * 100).toStringAsFixed(0)}%',
                          style: TextStyle(fontWeight: FontWeight.bold, color: suggestionColor),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // 價格目標
            if (targetPrice != null || stopLossPrice != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      if (targetPrice != null)
                        Expanded(
                          child: Column(
                            children: [
                              const Text('目標價', style: TextStyle(color: Colors.grey)),
                              const SizedBox(height: 4),
                              Text(
                                '$currencySymbol${targetPrice.toStringAsFixed(2)}',
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.green,
                                ),
                              ),
                            ],
                          ),
                        ),
                      if (stopLossPrice != null)
                        Expanded(
                          child: Column(
                            children: [
                              const Text('停損價', style: TextStyle(color: Colors.grey)),
                              const SizedBox(height: 4),
                              Text(
                                '$currencySymbol${stopLossPrice.toStringAsFixed(2)}',
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.red,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 16),
            // 分析理由
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'AI 分析理由',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      reasoning,
                      style: TextStyle(color: Colors.grey[700], height: 1.6),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // 風險警告
            Card(
              color: Colors.orange.withAlpha(26),
              child: const Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber, color: Colors.orange),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        '以上為 AI 分析結果，僅供參考，不構成投資建議。投資有風險，請自行評估。',
                        style: TextStyle(fontSize: 12, color: Colors.orange),
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

  Color _getSuggestionColor(String suggestion) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return Colors.red;
      case 'SELL':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  IconData _getSuggestionIcon(String suggestion) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return Icons.trending_up;
      case 'SELL':
        return Icons.trending_down;
      default:
        return Icons.trending_flat;
    }
  }

  String _getSuggestionText(String suggestion) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return '建議買進';
      case 'SELL':
        return '建議賣出';
      default:
        return '建議持有';
    }
  }
}
