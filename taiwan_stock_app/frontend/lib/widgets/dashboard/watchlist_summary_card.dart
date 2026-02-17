import 'package:flutter/material.dart';
import '../../models/dashboard_data.dart';
import '../../config/app_theme.dart';

/// 自選股摘要卡片
class WatchlistSummaryCard extends StatelessWidget {
  final WatchlistSummary data;
  final VoidCallback? onTap;
  final VoidCallback? onStockTap;

  const WatchlistSummaryCard({
    super.key,
    required this.data,
    this.onTap,
    this.onStockTap,
  });

  @override
  Widget build(BuildContext context) {
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
                    Icons.star,
                    color: Colors.amber,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    '自選股摘要',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const Spacer(),
                  if (data.alertTriggered > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.red.withAlpha(25),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.notifications_active, size: 12, color: Colors.red),
                          const SizedBox(width: 4),
                          Text(
                            '${data.alertTriggered} 警報',
                            style: const TextStyle(
                              fontSize: 11,
                              color: Colors.red,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  const Icon(Icons.chevron_right, color: Colors.grey),
                ],
              ),
              const SizedBox(height: 16),

              // 統計數據
              Row(
                children: [
                  _CircularStat(
                    total: data.totalStocks,
                    upCount: data.upCount,
                    downCount: data.downCount,
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      children: [
                        _StatRow(
                          label: '上漲',
                          value: data.upCount,
                          color: AppTheme.stockRise,
                        ),
                        const SizedBox(height: 8),
                        _StatRow(
                          label: '下跌',
                          value: data.downCount,
                          color: AppTheme.stockFall,
                        ),
                        const SizedBox(height: 8),
                        _StatRow(
                          label: '平盤',
                          value: data.flatCount,
                          color: AppTheme.stockFlat,
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              if (data.topGainers.isNotEmpty || data.topLosers.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Divider(height: 1),
                const SizedBox(height: 12),

                // 漲幅/跌幅排行
                Row(
                  children: [
                    if (data.topGainers.isNotEmpty)
                      Expanded(
                        child: _TopMoversSection(
                          title: '漲幅前三',
                          movers: data.topGainers,
                          isGainers: true,
                        ),
                      ),
                    if (data.topGainers.isNotEmpty && data.topLosers.isNotEmpty)
                      const SizedBox(width: 16),
                    if (data.topLosers.isNotEmpty)
                      Expanded(
                        child: _TopMoversSection(
                          title: '跌幅前三',
                          movers: data.topLosers,
                          isGainers: false,
                        ),
                      ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// 圓形統計圖
class _CircularStat extends StatelessWidget {
  final int total;
  final int upCount;
  final int downCount;

  const _CircularStat({
    required this.total,
    required this.upCount,
    required this.downCount,
  });

  @override
  Widget build(BuildContext context) {
    final upPercent = total > 0 ? upCount / total : 0.0;
    final downPercent = total > 0 ? downCount / total : 0.0;

    return SizedBox(
      width: 80,
      height: 80,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 背景圓
          SizedBox(
            width: 80,
            height: 80,
            child: CircularProgressIndicator(
              value: 1,
              strokeWidth: 8,
              backgroundColor: const Color(0xFF2C3A47),
              valueColor: const AlwaysStoppedAnimation(Color(0xFF2C3A47)),
            ),
          ),
          // 下跌部分
          SizedBox(
            width: 80,
            height: 80,
            child: CircularProgressIndicator(
              value: upPercent + downPercent,
              strokeWidth: 8,
              backgroundColor: Colors.transparent,
              valueColor: const AlwaysStoppedAnimation(AppTheme.stockFall),
            ),
          ),
          // 上漲部分
          SizedBox(
            width: 80,
            height: 80,
            child: CircularProgressIndicator(
              value: upPercent,
              strokeWidth: 8,
              backgroundColor: Colors.transparent,
              valueColor: const AlwaysStoppedAnimation(AppTheme.stockRise),
            ),
          ),
          // 中心文字
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                total.toString(),
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '檔',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// 統計行
class _StatRow extends StatelessWidget {
  final String label;
  final int value;
  final Color color;

  const _StatRow({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(
            fontSize: 13,
            color: Colors.grey.shade700,
          ),
        ),
        const Spacer(),
        Text(
          value.toString(),
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: color,
          ),
        ),
      ],
    );
  }
}

/// 漲跌排行區塊
class _TopMoversSection extends StatelessWidget {
  final String title;
  final List<TopMover> movers;
  final bool isGainers;

  const _TopMoversSection({
    required this.title,
    required this.movers,
    required this.isGainers,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        ...movers.map((mover) => Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  mover.name,
                  style: const TextStyle(fontSize: 12),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text(
                '${mover.changePercent >= 0 ? '+' : ''}${mover.changePercent.toStringAsFixed(2)}%',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isGainers ? AppTheme.stockRise : AppTheme.stockFall,
                ),
              ),
            ],
          ),
        )),
      ],
    );
  }
}
