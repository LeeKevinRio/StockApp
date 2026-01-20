import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ai_provider.dart';
import '../models/ai_suggestion.dart';

class AISuggestionsScreen extends StatefulWidget {
  const AISuggestionsScreen({super.key});

  @override
  State<AISuggestionsScreen> createState() => _AISuggestionsScreenState();
}

class _AISuggestionsScreenState extends State<AISuggestionsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AIProvider>().loadSuggestions();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 每日建議'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<AIProvider>().refreshSuggestions(),
          ),
        ],
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
                    'AI 正在分析您的自選股...',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                  ),
                  SizedBox(height: 8),
                  Text(
                    '首次生成需要 30-60 秒',
                    style: TextStyle(fontSize: 14, color: Colors.grey),
                  ),
                  SizedBox(height: 4),
                  Text(
                    '請耐心等候，不要關閉頁面',
                    style: TextStyle(fontSize: 12, color: Colors.orange),
                  ),
                ],
              ),
            );
          }

          if (provider.suggestionsError != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text('錯誤：${provider.suggestionsError}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.loadSuggestions(),
                    child: const Text('重試'),
                  ),
                ],
              ),
            );
          }

          if (provider.suggestions.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.lightbulb_outline,
                      size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text(
                    '尚無 AI 建議',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '請先新增自選股，然後點擊重新整理按鈕',
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () => provider.loadSuggestions(),
                    icon: const Icon(Icons.refresh),
                    label: const Text('立即生成 AI 建議'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => provider.refreshSuggestions(),
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: provider.suggestions.length,
              itemBuilder: (context, index) {
                final suggestion = provider.suggestions[index];
                return SuggestionCard(suggestion: suggestion);
              },
            ),
          );
        },
      ),
    );
  }
}

class SuggestionCard extends StatelessWidget {
  final AISuggestion suggestion;

  const SuggestionCard({super.key, required this.suggestion});

  @override
  Widget build(BuildContext context) {
    final suggestionColor = _getSuggestionColor(suggestion.suggestion);
    final suggestionIcon = _getSuggestionIcon(suggestion.suggestion);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 標頭：股票資訊
            Row(
              children: [
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
                // 建議標籤
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
                        _getSuggestionText(suggestion.suggestion),
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
            // 信心度
            Row(
              children: [
                const Text('信心度：'),
                Expanded(
                  child: LinearProgressIndicator(
                    value: suggestion.confidence,
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(suggestionColor),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '${(suggestion.confidence * 100).toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: suggestionColor,
                  ),
                ),
              ],
            ),
            if (suggestion.targetPrice != null ||
                suggestion.stopLossPrice != null) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  if (suggestion.targetPrice != null)
                    Expanded(
                      child: _buildPriceInfo(
                        '目標價',
                        suggestion.targetPrice!,
                        Colors.green,
                      ),
                    ),
                  if (suggestion.targetPrice != null &&
                      suggestion.stopLossPrice != null)
                    const SizedBox(width: 16),
                  if (suggestion.stopLossPrice != null)
                    Expanded(
                      child: _buildPriceInfo(
                        '停損價',
                        suggestion.stopLossPrice!,
                        Colors.red,
                      ),
                    ),
                ],
              ),
            ],
            const SizedBox(height: 12),
            // 分析理由
            const Text(
              '分析理由',
              style: TextStyle(
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
              const Text(
                '關鍵因素',
                style: TextStyle(
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

  Widget _buildPriceInfo(String label, double price, Color color) {
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
            price.toStringAsFixed(2),
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
        return Icons.remove;
    }
  }

  String _getSuggestionText(String suggestion) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return '買進';
      case 'SELL':
        return '賣出';
      default:
        return '持有';
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
