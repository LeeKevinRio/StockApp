import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ai_provider.dart';
import '../providers/market_provider.dart';
import '../models/ai_suggestion.dart';
import '../widgets/market_switcher.dart';

class AISuggestionsScreen extends StatefulWidget {
  const AISuggestionsScreen({super.key});

  @override
  State<AISuggestionsScreen> createState() => _AISuggestionsScreenState();
}

class _AISuggestionsScreenState extends State<AISuggestionsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AIProvider>().loadSuggestions();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Daily Suggestions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<AIProvider>().refreshSuggestions(),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(
              icon: Icon(Icons.flag),
              text: 'Taiwan Stocks',
            ),
            Tab(
              icon: Icon(Icons.public),
              text: 'US Stocks',
            ),
          ],
        ),
      ),
      body: Consumer<AIProvider>(
        builder: (context, provider, child) {
          if (provider.isLoadingSuggestions) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text(
                    'AI is analyzing your watchlist...',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'First generation takes 30-60 seconds',
                    style: TextStyle(fontSize: 14, color: Colors.grey),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Please wait, do not close this page',
                    style: TextStyle(fontSize: 12, color: Colors.orange),
                  ),
                ],
              ),
            );
          }

          if (provider.suggestionsError != null) {
            final err = provider.suggestionsError!;
            final isQuota = err.contains('429') || err.contains('quota') || err.contains('配額');
            final isNetwork = err.contains('Failed to fetch') || err.contains('SocketException') || err.contains('Connection');

            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      isQuota ? Icons.hourglass_empty : isNetwork ? Icons.wifi_off : Icons.error_outline,
                      size: 64,
                      color: isQuota ? Colors.orange : Colors.red,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      isQuota
                          ? 'AI 服務額度已用完'
                          : isNetwork
                              ? '無法連線到伺服器'
                              : 'AI 服務暫時不可用',
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      isQuota
                          ? 'Gemini 與 Groq 的免費額度已耗盡，請稍後再試或升級方案。'
                          : isNetwork
                              ? '請檢查網路連線或確認後端服務是否已啟動。'
                              : '伺服器發生錯誤，請稍後再試。',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () => provider.loadSuggestions(),
                      icon: const Icon(Icons.refresh),
                      label: const Text('重試'),
                    ),
                  ],
                ),
              ),
            );
          }

          // Separate suggestions by market
          final twSuggestions = provider.suggestions
              .where((s) => _isTaiwanStock(s.stockId))
              .toList();
          final usSuggestions = provider.suggestions
              .where((s) => !_isTaiwanStock(s.stockId))
              .toList();

          return TabBarView(
            controller: _tabController,
            children: [
              // Taiwan Stocks Tab
              _buildSuggestionsList(
                twSuggestions,
                provider,
                isTaiwan: true,
              ),
              // US Stocks Tab
              _buildSuggestionsList(
                usSuggestions,
                provider,
                isTaiwan: false,
              ),
            ],
          );
        },
      ),
    );
  }

  bool _isTaiwanStock(String stockId) {
    // 台股代碼：純數字(2330)或數字開頭含英文後綴(00631L, 00878)
    return RegExp(r'^\d').hasMatch(stockId);
  }

  Widget _buildSuggestionsList(
    List<AISuggestion> suggestions,
    AIProvider provider, {
    required bool isTaiwan,
  }) {
    if (suggestions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              isTaiwan ? Icons.flag : Icons.public,
              size: 64,
              color: Colors.grey,
            ),
            const SizedBox(height: 16),
            Text(
              isTaiwan ? '尚無 AI 建議' : 'No AI Suggestions',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            Text(
              isTaiwan
                  ? '點擊下方按鈕為自選股生成 AI 分析'
                  : 'Click below to generate AI analysis for your watchlist',
              style: const TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              isTaiwan
                  ? '（首次生成需要 30-60 秒）'
                  : '(First generation takes 30-60 seconds)',
              style: const TextStyle(color: Colors.orange, fontSize: 12),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => provider.refreshSuggestions(),
              icon: const Icon(Icons.auto_awesome),
              label: Text(isTaiwan ? '生成 AI 建議' : 'Generate AI Suggestions'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.refreshSuggestions(),
      child: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: suggestions.length,
        itemBuilder: (context, index) {
          final suggestion = suggestions[index];
          return SuggestionCard(
            suggestion: suggestion,
            isTaiwan: isTaiwan,
          );
        },
      ),
    );
  }
}

class SuggestionCard extends StatelessWidget {
  final AISuggestion suggestion;
  final bool isTaiwan;

  const SuggestionCard({
    super.key,
    required this.suggestion,
    this.isTaiwan = true,
  });

  @override
  Widget build(BuildContext context) {
    final suggestionColor = _getSuggestionColor(suggestion.suggestion);
    final suggestionIcon = _getSuggestionIcon(suggestion.suggestion);
    final currencySymbol = isTaiwan ? 'NT\$' : '\$';

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with stock info and market badge
            Row(
              children: [
                // Market badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: isTaiwan ? Colors.red.shade50 : Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    isTaiwan ? 'TW' : 'US',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: isTaiwan ? Colors.red.shade700 : Colors.blue.shade700,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${suggestion.stockId} ${suggestion.name}',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        suggestion.reportDate.toString().substring(0, 10),
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
                // Suggestion badge
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: suggestionColor.withAlpha(25),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: suggestionColor),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(suggestionIcon, color: suggestionColor, size: 20),
                      const SizedBox(width: 4),
                      Text(
                        _getSuggestionText(suggestion.suggestion, isTaiwan),
                        style: TextStyle(
                          color: suggestionColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            // Bullish Probability (看漲機率) - 更直覺的指標
            Row(
              children: [
                Text(isTaiwan ? '看漲機率：' : 'Bullish: '),
                Expanded(
                  child: LinearProgressIndicator(
                    value: suggestion.bullishProbability ??
                        (suggestion.suggestion == 'BUY'
                            ? suggestion.confidence
                            : 1 - suggestion.confidence),
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      _getBullishColor(suggestion.bullishProbability ??
                          (suggestion.suggestion == 'BUY'
                              ? suggestion.confidence
                              : 1 - suggestion.confidence)),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '${((suggestion.bullishProbability ?? (suggestion.suggestion == 'BUY' ? suggestion.confidence : 1 - suggestion.confidence)) * 100).toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: _getBullishColor(suggestion.bullishProbability ??
                        (suggestion.suggestion == 'BUY'
                            ? suggestion.confidence
                            : 1 - suggestion.confidence)),
                  ),
                ),
              ],
            ),
            // 隔天漲跌預測區塊
            if (suggestion.nextDayPrediction != null) ...[
              const SizedBox(height: 12),
              _buildNextDayPrediction(suggestion.nextDayPrediction!, currencySymbol, isTaiwan),
            ],
            if (suggestion.currentPrice != null ||
                suggestion.targetPrice != null ||
                suggestion.stopLossPrice != null) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  if (suggestion.currentPrice != null)
                    Expanded(
                      child: _buildPriceInfo(
                        isTaiwan ? '現價' : 'Current',
                        suggestion.currentPrice!,
                        Colors.blueGrey,
                        currencySymbol,
                      ),
                    ),
                  if (suggestion.currentPrice != null &&
                      (suggestion.targetPrice != null || suggestion.stopLossPrice != null))
                    const SizedBox(width: 8),
                  if (suggestion.targetPrice != null)
                    Expanded(
                      child: _buildPriceInfo(
                        isTaiwan ? '目標價' : 'Target',
                        suggestion.targetPrice!,
                        Colors.green,
                        currencySymbol,
                      ),
                    ),
                  if (suggestion.targetPrice != null &&
                      suggestion.stopLossPrice != null)
                    const SizedBox(width: 8),
                  if (suggestion.stopLossPrice != null)
                    Expanded(
                      child: _buildPriceInfo(
                        isTaiwan ? '停損價' : 'Stop Loss',
                        suggestion.stopLossPrice!,
                        Colors.red,
                        currencySymbol,
                      ),
                    ),
                ],
              ),
            ],
            const SizedBox(height: 12),
            // Reasoning
            Text(
              isTaiwan ? '分析理由' : 'Analysis',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              suggestion.reasoning,
              style: TextStyle(
                color: Colors.grey[700],
                height: 1.5,
              ),
            ),
            if (suggestion.keyFactors.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                isTaiwan ? '關鍵因素' : 'Key Factors',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 8),
              ...suggestion.keyFactors.map((factor) {
                final impactColor = _getImpactColor(factor.impact);
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        _getImpactIcon(factor.impact),
                        size: 16,
                        color: impactColor,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              factor.category,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                            Text(
                              factor.factor,
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[700],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPriceInfo(String label, double price, Color color, String currency) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: color,
            ),
          ),
          Text(
            '$currency${price.toStringAsFixed(2)}',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  /// 建構隔天預測區塊
  Widget _buildNextDayPrediction(NextDayPrediction prediction, String currency, bool isTaiwan) {
    final isUp = prediction.direction == 'UP';
    final directionColor = isUp ? Colors.red : Colors.green;
    final directionIcon = isUp ? Icons.arrow_upward : Icons.arrow_downward;
    final directionText = isUp
        ? (isTaiwan ? '預測上漲' : 'Predicted UP')
        : (isTaiwan ? '預測下跌' : 'Predicted DOWN');

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            directionColor.withAlpha(20),
            directionColor.withAlpha(10),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: directionColor.withAlpha(80)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 標題
          Row(
            children: [
              Icon(Icons.schedule, size: 16, color: directionColor),
              const SizedBox(width: 4),
              Text(
                isTaiwan ? '明日漲跌預測' : 'Tomorrow Prediction',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: directionColor,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: directionColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(directionIcon, size: 14, color: Colors.white),
                    const SizedBox(width: 2),
                    Text(
                      directionText,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // 預測數據
          Row(
            children: [
              // 預測漲跌幅
              Expanded(
                child: Column(
                  children: [
                    Text(
                      isTaiwan ? '預測漲跌幅' : 'Change',
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${prediction.predictedChangePercent >= 0 ? '+' : ''}${prediction.predictedChangePercent.toStringAsFixed(2)}%',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: directionColor,
                      ),
                    ),
                  ],
                ),
              ),
              // 預測準確率
              Expanded(
                child: Column(
                  children: [
                    Text(
                      isTaiwan ? '預測信心度' : 'Confidence',
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${(prediction.probability * 100).toStringAsFixed(0)}%',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.orange.shade700,
                      ),
                    ),
                  ],
                ),
              ),
              // 預測價格區間
              if (prediction.priceRangeLow != null && prediction.priceRangeHigh != null)
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        isTaiwan ? '預測區間' : 'Range',
                        style: const TextStyle(fontSize: 11, color: Colors.grey),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${prediction.priceRangeLow!.toStringAsFixed(1)}-${prediction.priceRangeHigh!.toStringAsFixed(1)}',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.blueGrey.shade700,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          // 預測依據
          if (prediction.reasoning.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              prediction.reasoning,
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey.shade600,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
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

  Color _getBullishColor(double probability) {
    // 看漲機率高 = 紅色(台股看多), 看漲機率低 = 綠色(看空)
    if (probability >= 0.6) {
      return Colors.red;
    } else if (probability <= 0.4) {
      return Colors.green;
    } else {
      return Colors.orange;
    }
  }

  IconData _getSuggestionIcon(String suggestion) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return Icons.trending_up;
      case 'SELL':
        return Icons.trending_down;
      default:
        return Icons.remove;
    }
  }

  String _getSuggestionText(String suggestion, bool isTaiwan) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return isTaiwan ? '買進' : 'BUY';
      case 'SELL':
        return isTaiwan ? '賣出' : 'SELL';
      default:
        return isTaiwan ? '持有' : 'HOLD';
    }
  }

  Color _getImpactColor(String impact) {
    switch (impact.toLowerCase()) {
      case 'positive':
        return Colors.green;
      case 'negative':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData _getImpactIcon(String impact) {
    switch (impact.toLowerCase()) {
      case 'positive':
        return Icons.arrow_upward;
      case 'negative':
        return Icons.arrow_downward;
      default:
        return Icons.horizontal_rule;
    }
  }
}
