import 'package:flutter/material.dart';
import '../../models/dashboard_data.dart';
import '../../config/app_theme.dart';

/// 市場概況卡片
class MarketOverviewCard extends StatelessWidget {
  final MarketOverview data;
  final VoidCallback? onTap;

  const MarketOverviewCard({
    super.key,
    required this.data,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isUp = data.isUp;
    final isDown = data.isDown;
    final changeColor = isUp
        ? AppTheme.stockRise
        : isDown
            ? AppTheme.stockFall
            : AppTheme.stockFlat;

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 標題行
              Row(
                children: [
                  Icon(
                    Icons.show_chart,
                    color: Theme.of(context).primaryColor,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    data.indexName,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    _formatTime(data.updateTime),
                    style: TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).textTheme.bodySmall?.color ?? Colors.grey,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // 指數值或市場平均漲跌
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (data.indexValue > 0)
                    Text(
                      data.indexValue.toStringAsFixed(2),
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: changeColor,
                      ),
                    )
                  else
                    Text(
                      '${isUp ? '+' : ''}${data.changePercent.toStringAsFixed(2)}%',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: changeColor,
                      ),
                    ),
                  const SizedBox(width: 12),
                  if (data.indexValue > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: changeColor.withAlpha(25),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            isUp
                                ? Icons.arrow_drop_up
                                : isDown
                                    ? Icons.arrow_drop_down
                                    : Icons.remove,
                            color: changeColor,
                            size: 20,
                          ),
                          Text(
                            '${isUp ? '+' : ''}${data.indexChange.toStringAsFixed(2)} (${isUp ? '+' : ''}${data.changePercent.toStringAsFixed(2)}%)',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: changeColor,
                            ),
                          ),
                        ],
                      ),
                    )
                  else
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: changeColor.withAlpha(25),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        '平均漲跌幅',
                        style: TextStyle(
                          fontSize: 12,
                          color: changeColor,
                        ),
                      ),
                    ),
                ],
              ),

              const SizedBox(height: 16),
              const Divider(height: 1),
              const SizedBox(height: 12),

              // 漲跌家數
              Row(
                children: [
                  _StatItem(
                    label: '上漲',
                    value: data.upCount.toString(),
                    color: AppTheme.stockRise,
                  ),
                  _StatItem(
                    label: '下跌',
                    value: data.downCount.toString(),
                    color: AppTheme.stockFall,
                  ),
                  _StatItem(
                    label: '平盤',
                    value: data.flatCount.toString(),
                    color: AppTheme.stockFlat,
                  ),
                  if (data.totalVolume > 0)
                    _StatItem(
                      label: '成交量',
                      value: '${data.totalVolume}億',
                      color: Colors.blue,
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatItem({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: Theme.of(context).textTheme.bodySmall?.color ?? Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}
