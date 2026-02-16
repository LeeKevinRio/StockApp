import 'package:flutter/material.dart';
import '../../models/dashboard_data.dart';
import '../../config/app_theme.dart';

/// AI 精選推薦卡片
class AIPicksCard extends StatelessWidget {
  final List<AIPick> picks;
  final bool isLoading;
  final VoidCallback? onViewAll;
  final Function(AIPick)? onPickTap;

  const AIPicksCard({
    super.key,
    required this.picks,
    this.isLoading = false,
    this.onViewAll,
    this.onPickTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
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
                    color: Colors.purple.withAlpha(25),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.psychology,
                    color: Colors.purple,
                    size: 18,
                  ),
                ),
                const SizedBox(width: 10),
                const Text(
                  'AI 精選推薦',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const Spacer(),
                if (onViewAll != null)
                  TextButton(
                    onPressed: onViewAll,
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('查看全部', style: TextStyle(fontSize: 12)),
                        Icon(Icons.chevron_right, size: 16),
                      ],
                    ),
                  ),
              ],
            ),

            if (isLoading && picks.isEmpty) ...[
              const SizedBox(height: 24),
              Center(
                child: Column(
                  children: [
                    const SizedBox(
                      width: 32,
                      height: 32,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.purple,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'AI 分析中...',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ] else if (picks.isEmpty) ...[
              const SizedBox(height: 24),
              Center(
                child: Column(
                  children: [
                    Icon(
                      Icons.lightbulb_outline,
                      size: 40,
                      color: Colors.grey.shade400,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '請先新增自選股，AI 將自動分析推薦',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ] else ...[
              const SizedBox(height: 12),
              ...picks.map((pick) => _AIPickItem(
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

class _AIPickItem extends StatelessWidget {
  final AIPick pick;
  final VoidCallback? onTap;

  const _AIPickItem({
    required this.pick,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final suggestionColor = _getSuggestionColor(pick.suggestion);

    return Semantics(
      label: '${pick.stockId} ${pick.name}，建議${pick.suggestionText}，信心度${(pick.confidence * 100).toInt()}%',
      button: true,
      child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: Colors.grey.shade200,
              width: 0.5,
            ),
          ),
        ),
        child: Row(
          children: [
            // 左側 - 股票信息
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${pick.stockId} ${pick.name}',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    pick.shortReason,
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontSize: 12,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),

            // 右側 - 建議和信心度
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: suggestionColor.withAlpha(25),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    pick.suggestionText,
                    style: TextStyle(
                      color: suggestionColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _ConfidenceBar(confidence: pick.confidence),
                    const SizedBox(width: 4),
                    Text(
                      '${(pick.confidence * 100).toInt()}%',
                      style: TextStyle(
                        color: Colors.grey.shade600,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    ),
    );
  }

  Color _getSuggestionColor(String suggestion) {
    switch (suggestion.toUpperCase()) {
      case 'BUY':
        return AppTheme.stockRise;
      case 'SELL':
        return AppTheme.stockFall;
      case 'HOLD':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}

class _ConfidenceBar extends StatelessWidget {
  final double confidence;

  const _ConfidenceBar({required this.confidence});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 4,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(2),
      ),
      child: FractionallySizedBox(
        alignment: Alignment.centerLeft,
        widthFactor: confidence,
        child: Container(
          decoration: BoxDecoration(
            color: _getConfidenceColor(confidence),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
      ),
    );
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.8) return Colors.green;
    if (confidence >= 0.6) return Colors.orange;
    return Colors.red;
  }
}
