import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ai_provider.dart';
import '../models/industry_trend.dart';

class IndustryTrendsScreen extends StatefulWidget {
  const IndustryTrendsScreen({super.key});

  @override
  State<IndustryTrendsScreen> createState() => _IndustryTrendsScreenState();
}

class _IndustryTrendsScreenState extends State<IndustryTrendsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<AIProvider>();
      if (provider.industryTrends == null && !provider.isLoadingTrends) {
        provider.loadIndustryTrends();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('產業趨勢分析'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<AIProvider>().refreshIndustryTrends(),
          ),
        ],
      ),
      body: Consumer<AIProvider>(
        builder: (context, provider, child) {
          if (provider.isLoadingTrends) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text(
                    'AI 正在分析產業趨勢...',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                  ),
                  SizedBox(height: 8),
                  Text(
                    '分析需要 30-60 秒，請耐心等候',
                    style: TextStyle(fontSize: 14, color: Colors.grey),
                  ),
                ],
              ),
            );
          }

          if (provider.trendsError != null) {
            final err = provider.trendsError!;
            final isQuota = err.contains('429') || err.contains('quota') || err.contains('配額');
            final isNetwork = err.contains('Failed to fetch') || err.contains('SocketException');
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
                      isQuota ? 'AI 額度已用完' : isNetwork ? '無法連線' : '載入失敗',
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      isQuota
                          ? 'AI 服務免費額度已耗盡，請稍後再試。'
                          : isNetwork
                              ? '請檢查網路連線或後端服務狀態。'
                              : '伺服器發生錯誤，請稍後再試。',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () => provider.loadIndustryTrends(),
                      icon: const Icon(Icons.refresh),
                      label: const Text('重試'),
                    ),
                  ],
                ),
              ),
            );
          }

          final trends = provider.industryTrends;
          if (trends == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.analytics_outlined, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('尚無產業趨勢分析'),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: () => provider.loadIndustryTrends(),
                    icon: const Icon(Icons.refresh),
                    label: const Text('立即分析'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => provider.refreshIndustryTrends(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // 分析日期
                Text(
                  '分析日期：${trends.analysisDate}',
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
                const SizedBox(height: 16),

                // 市場概況
                _buildSectionCard(
                  title: '市場概況',
                  icon: Icons.public,
                  color: Colors.blue,
                  child: Text(
                    trends.marketOverview,
                    style: const TextStyle(height: 1.6),
                  ),
                ),
                const SizedBox(height: 16),

                // 看漲產業
                _buildSectionTitle('看漲產業', Icons.trending_up, Colors.red),
                const SizedBox(height: 8),
                ...trends.bullishIndustries.map((industry) =>
                    _buildBullishCard(industry)),

                const SizedBox(height: 24),

                // 看跌產業
                _buildSectionTitle('看跌產業', Icons.trending_down, Colors.green),
                const SizedBox(height: 8),
                ...trends.bearishIndustries.map((industry) =>
                    _buildBearishCard(industry)),

                const SizedBox(height: 24),

                // 投資建議
                _buildSectionCard(
                  title: '投資建議',
                  icon: Icons.lightbulb,
                  color: Colors.orange,
                  child: Text(
                    trends.investmentSuggestions,
                    style: const TextStyle(height: 1.6),
                  ),
                ),

                const SizedBox(height: 16),

                // 免責聲明
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    trends.disclaimer,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[400],
                      height: 1.5,
                    ),
                  ),
                ),
                const SizedBox(height: 32),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSectionTitle(String title, IconData icon, Color color) {
    return Row(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(width: 8),
        Text(
          title,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required Color color,
    required Widget child,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            child,
          ],
        ),
      ),
    );
  }

  Widget _buildBullishCard(BullishIndustry industry) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    industry.industry,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.red.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.red),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.arrow_upward, color: Colors.red, size: 16),
                      const SizedBox(width: 4),
                      Text(
                        '${(industry.probability * 100).toStringAsFixed(0)}%',
                        style: const TextStyle(
                          color: Colors.red,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              industry.reasoning,
              style: TextStyle(color: Colors.grey[700], height: 1.5),
            ),
            const SizedBox(height: 12),
            _buildTagList('關鍵因素', industry.keyFactors, Colors.blue),
            const SizedBox(height: 8),
            _buildTagList('代表股票', industry.representativeStocks, Colors.purple),
            const SizedBox(height: 8),
            _buildTagList('風險因素', industry.riskFactors, Colors.orange),
          ],
        ),
      ),
    );
  }

  Widget _buildBearishCard(BearishIndustry industry) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    industry.industry,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.green.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.green),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.arrow_downward, color: Colors.green, size: 16),
                      const SizedBox(width: 4),
                      Text(
                        '${(industry.probability * 100).toStringAsFixed(0)}%',
                        style: const TextStyle(
                          color: Colors.green,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              industry.reasoning,
              style: TextStyle(color: Colors.grey[700], height: 1.5),
            ),
            const SizedBox(height: 12),
            _buildTagList('關鍵因素', industry.keyFactors, Colors.blue),
            const SizedBox(height: 8),
            _buildTagList('代表股票', industry.representativeStocks, Colors.purple),
            const SizedBox(height: 8),
            _buildTagList('避開理由', industry.avoidReasons, Colors.red),
          ],
        ),
      ),
    );
  }

  Widget _buildTagList(String label, List<String> tags, Color color) {
    if (tags.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: tags.map((tag) => Chip(
            label: Text(
              tag,
              style: TextStyle(fontSize: 12, color: color),
            ),
            backgroundColor: color.withValues(alpha: 0.1),
            padding: EdgeInsets.zero,
            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
          )).toList(),
        ),
      ],
    );
  }
}
