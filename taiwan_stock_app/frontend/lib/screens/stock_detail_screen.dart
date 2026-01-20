import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/stock.dart';
import '../models/stock_history.dart';
import '../widgets/candlestick_chart.dart';

class StockDetailScreen extends StatefulWidget {
  final String stockId;

  const StockDetailScreen({
    super.key,
    required this.stockId,
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

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
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
      // 暫時使用搜尋API獲取股票資訊
      final response = await apiService.searchStocks(widget.stockId);

      if (response.isNotEmpty) {
        setState(() {
          _stock = response.first;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = '找不到股票資訊';
          _isLoading = false;
        });
      }
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
          tabs: const [
            Tab(text: '概覽'),
            Tab(text: 'K線'),
            Tab(text: '技術分析'),
            Tab(text: 'AI建議'),
            Tab(text: '新聞'),
            Tab(text: '社群'),
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
              _buildInfoRow('市場類別', _stock!.market),
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
    return FutureBuilder<List<StockHistory>>(
      future: Provider.of<ApiService>(context, listen: false)
          .getStockHistory(widget.stockId, days: 60),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          // 改進錯誤訊息顯示
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
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
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
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.grey,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    '可能原因：',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '• 網路連線不穩定\n'
                    '• 後端服務暫時無法使用\n'
                    '• 股票代碼不存在或無歷史數據',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () => setState(() {}),
                    icon: const Icon(Icons.refresh),
                    label: const Text('重新載入'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.show_chart, size: 64, color: Colors.grey),
                SizedBox(height: 16),
                Text('暫無K線數據'),
              ],
            ),
          );
        }

        return Column(
          children: [
            // 圖例說明
            Container(
              padding: const EdgeInsets.all(12),
              color: Colors.grey.shade100,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildLegendItem('MA5', Colors.blue),
                  const SizedBox(width: 16),
                  _buildLegendItem('MA10', Colors.orange),
                  const SizedBox(width: 16),
                  _buildLegendItem('MA20', Colors.purple),
                ],
              ),
            ),
            // K線圖
            Expanded(
              child: CandlestickChart(
                data: snapshot.data!,
                showVolume: true,
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 24,
          height: 2,
          color: color,
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        ),
      ],
    );
  }

  Widget _buildTechnicalAnalysisTab() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.analytics, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text('技術分析功能開發中...'),
          SizedBox(height: 8),
          Text(
            '即將提供 MACD、布林通道、RSI 等技術指標',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildAISuggestionTab() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.lightbulb_outline, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text('個股AI建議功能開發中...'),
          SizedBox(height: 8),
          Text(
            '即將提供高風險型經紀人的專業分析',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildNewsTab() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.newspaper, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text('新聞資訊功能開發中...'),
          SizedBox(height: 8),
          Text(
            '即將整合全球財經新聞及情感分析',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildSocialTab() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.forum, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text('社群討論功能開發中...'),
          SizedBox(height: 8),
          Text(
            '即將整合 PTT、Dcard 等社群平台',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
    );
  }
}
