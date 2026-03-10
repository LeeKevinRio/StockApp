import 'package:flutter/material.dart';
import '../../config/app_theme.dart';

/// AI 潛力股推薦數據模型
class AIDiscoveryPick {
  final String stockId;
  final String name;
  final double currentPrice;
  final double predictedChangePct;
  final double probability;
  final double targetPrice;
  final double stopLossPrice;
  final String riskLevel;
  final String reasoning;
  final List<String> keySignals;
  final int technicalScore;
  final String market;

  AIDiscoveryPick({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.predictedChangePct,
    required this.probability,
    required this.targetPrice,
    required this.stopLossPrice,
    required this.riskLevel,
    required this.reasoning,
    required this.keySignals,
    required this.technicalScore,
    required this.market,
  });

  factory AIDiscoveryPick.fromJson(Map<String, dynamic> json) {
    return AIDiscoveryPick(
      stockId: json['stock_id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      currentPrice: (json['current_price'] as num?)?.toDouble() ?? 0,
      predictedChangePct: (json['predicted_change_pct'] as num?)?.toDouble() ?? 0,
      probability: (json['probability'] as num?)?.toDouble() ?? 0,
      targetPrice: (json['target_price'] as num?)?.toDouble() ?? 0,
      stopLossPrice: (json['stop_loss_price'] as num?)?.toDouble() ?? 0,
      riskLevel: json['risk_level'] as String? ?? 'MEDIUM',
      reasoning: json['reasoning'] as String? ?? '',
      keySignals: (json['key_signals'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      technicalScore: (json['technical_score'] as num?)?.toInt() ?? 0,
      market: json['market'] as String? ?? 'TW',
    );
  }
}

/// AI 潛力股掃描卡片
class AIDiscoveryCard extends StatelessWidget {
  final List<AIDiscoveryPick> picks;
  final String marketSummary;
  final bool isLoading;
  final bool hasScanned;
  final VoidCallback? onScan;
  final VoidCallback? onRefresh;
  final Function(AIDiscoveryPick)? onPickTap;

  const AIDiscoveryCard({
    super.key,
    required this.picks,
    this.marketSummary = '',
    this.isLoading = false,
    this.hasScanned = false,
    this.onScan,
    this.onRefresh,
    this.onPickTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 標題行
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFFF6B35), Color(0xFFFF8F00)],
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.rocket_launch,
                    color: Colors.white,
                    size: 18,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'AI 潛力股掃描',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        '短期 5 天上漲預測',
                        style: TextStyle(
                          fontSize: 11,
                          color: theme.textTheme.bodySmall?.color,
                        ),
                      ),
                    ],
                  ),
                ),
                if (hasScanned && onRefresh != null)
                  IconButton(
                    onPressed: isLoading ? null : onRefresh,
                    icon: Icon(
                      Icons.refresh,
                      size: 20,
                      color: isLoading ? Colors.grey : const Color(0xFFFF6B35),
                    ),
                    tooltip: '重新掃描',
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
              ],
            ),

            const SizedBox(height: 12),

            // 市場摘要
            if (marketSummary.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFFFF6B35).withAlpha(15),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: const Color(0xFFFF6B35).withAlpha(40),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.insights, size: 16, color: Color(0xFFFF6B35)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        marketSummary,
                        style: const TextStyle(fontSize: 12, color: Color(0xFFFF6B35)),
                      ),
                    ),
                  ],
                ),
              ),

            if (marketSummary.isNotEmpty) const SizedBox(height: 12),

            // 內容區域
            if (isLoading && picks.isEmpty) ...[
              const SizedBox(height: 16),
              Center(
                child: Column(
                  children: [
                    const SizedBox(
                      width: 36,
                      height: 36,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Color(0xFFFF6B35),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'AI 正在掃描市場中...',
                      style: TextStyle(
                        color: theme.textTheme.bodySmall?.color,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '分析技術指標、量價關係、市場動能',
                      style: TextStyle(
                        color: theme.textTheme.bodySmall?.color?.withAlpha(150),
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ] else if (!hasScanned) ...[
              // 尚未掃描，顯示啟動按鈕
              const SizedBox(height: 12),
              Center(
                child: Column(
                  children: [
                    Icon(
                      Icons.radar,
                      size: 48,
                      color: theme.disabledColor,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '點擊掃描，AI 將自動分析全市場',
                      style: TextStyle(
                        color: theme.textTheme.bodySmall?.color,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ElevatedButton.icon(
                      onPressed: onScan,
                      icon: const Icon(Icons.rocket_launch, size: 18),
                      label: const Text('開始 AI 掃描'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFFF6B35),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ] else if (picks.isEmpty) ...[
              const SizedBox(height: 16),
              Center(
                child: Text(
                  '目前未發現高機率潛力股',
                  style: TextStyle(
                    color: theme.textTheme.bodySmall?.color,
                    fontSize: 13,
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ] else ...[
              ...picks.map((pick) => _DiscoveryPickItem(
                    pick: pick,
                    onTap: () => onPickTap?.call(pick),
                  )),
            ],
          ],
        ),
      ),
    );
  }
}

class _DiscoveryPickItem extends StatelessWidget {
  final AIDiscoveryPick pick;
  final VoidCallback? onTap;

  const _DiscoveryPickItem({
    required this.pick,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final probColor = pick.probability >= 0.75
        ? AppTheme.stockRise
        : pick.probability >= 0.6
            ? Colors.orange
            : Colors.grey;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: theme.dividerTheme.color ?? Colors.grey.shade200,
              width: 0.5,
            ),
          ),
        ),
        child: Row(
          children: [
            // 左側：排名圓標 + 股票資訊
            _ProbabilityBadge(probability: pick.probability),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        '${pick.stockId} ',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      Flexible(
                        child: Text(
                          pick.name,
                          style: TextStyle(
                            fontSize: 12,
                            color: theme.textTheme.bodySmall?.color,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    pick.reasoning,
                    style: TextStyle(
                      fontSize: 11,
                      color: theme.textTheme.bodySmall?.color?.withAlpha(180),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  // 訊號標籤
                  Wrap(
                    spacing: 4,
                    children: pick.keySignals.take(3).map((signal) {
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                        decoration: BoxDecoration(
                          color: probColor.withAlpha(20),
                          borderRadius: BorderRadius.circular(3),
                        ),
                        child: Text(
                          signal,
                          style: TextStyle(fontSize: 9, color: probColor),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),

            // 右側：預測漲幅 + 目標價
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppTheme.stockRise.withAlpha(20),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '+${pick.predictedChangePct.toStringAsFixed(1)}%',
                    style: TextStyle(
                      color: AppTheme.stockRise,
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${pick.market == "US" ? "\$" : ""}${pick.currentPrice.toStringAsFixed(pick.currentPrice > 100 ? 0 : 2)}',
                  style: TextStyle(
                    fontSize: 11,
                    color: theme.textTheme.bodySmall?.color,
                  ),
                ),
                Text(
                  '→ ${pick.market == "US" ? "\$" : ""}${pick.targetPrice.toStringAsFixed(pick.targetPrice > 100 ? 0 : 2)}',
                  style: const TextStyle(
                    fontSize: 10,
                    color: Color(0xFFFF6B35),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// 機率圓形標記
class _ProbabilityBadge extends StatelessWidget {
  final double probability;

  const _ProbabilityBadge({required this.probability});

  @override
  Widget build(BuildContext context) {
    final pct = (probability * 100).toInt();
    final color = probability >= 0.75
        ? AppTheme.stockRise
        : probability >= 0.6
            ? Colors.orange
            : Colors.grey;

    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withAlpha(20),
        border: Border.all(color: color, width: 1.5),
      ),
      child: Center(
        child: Text(
          '$pct%',
          style: TextStyle(
            color: color,
            fontSize: 11,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
