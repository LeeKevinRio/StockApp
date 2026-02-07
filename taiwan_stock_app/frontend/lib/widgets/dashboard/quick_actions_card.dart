import 'package:flutter/material.dart';

/// 快捷操作項目
class QuickActionItem {
  final String label;
  final IconData icon;
  final Color color;
  final String route;
  final Map<String, dynamic>? arguments;

  const QuickActionItem({
    required this.label,
    required this.icon,
    required this.color,
    required this.route,
    this.arguments,
  });
}

/// 快捷操作卡片
class QuickActionsCard extends StatelessWidget {
  final List<QuickActionItem> actions;
  final Function(QuickActionItem)? onActionTap;

  const QuickActionsCard({
    super.key,
    required this.actions,
    this.onActionTap,
  });

  /// 預設快捷操作列表
  static List<QuickActionItem> get defaultActions => const [
    QuickActionItem(
      label: '搜尋股票',
      icon: Icons.search,
      color: Colors.blue,
      route: '/search',
    ),
    QuickActionItem(
      label: 'AI 問答',
      icon: Icons.chat,
      color: Colors.purple,
      route: '/home',
      arguments: {'tab': 2},
    ),
    QuickActionItem(
      label: '投資組合',
      icon: Icons.account_balance_wallet,
      color: Colors.green,
      route: '/portfolio',
    ),
    QuickActionItem(
      label: '模擬交易',
      icon: Icons.trending_up,
      color: Colors.orange,
      route: '/trading',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: actions.map((action) => _QuickActionButton(
            item: action,
            onTap: () => onActionTap?.call(action),
          )).toList(),
        ),
      ),
    );
  }
}

class _QuickActionButton extends StatelessWidget {
  final QuickActionItem item;
  final VoidCallback? onTap;

  const _QuickActionButton({
    required this.item,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: item.color.withAlpha(25),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                item.icon,
                color: item.color,
                size: 24,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              item.label,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 警報狀態組件
class AlertStatusWidget extends StatelessWidget {
  final int activeCount;
  final int triggeredToday;
  final VoidCallback? onTap;

  const AlertStatusWidget({
    super.key,
    required this.activeCount,
    required this.triggeredToday,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: triggeredToday > 0
              ? Colors.red.withAlpha(20)
              : Colors.grey.withAlpha(20),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: triggeredToday > 0
                ? Colors.red.withAlpha(50)
                : Colors.grey.withAlpha(50),
          ),
        ),
        child: Row(
          children: [
            Icon(
              triggeredToday > 0
                  ? Icons.notifications_active
                  : Icons.notifications_outlined,
              color: triggeredToday > 0 ? Colors.red : Colors.grey,
              size: 20,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    triggeredToday > 0
                        ? '今日 $triggeredToday 個警報觸發'
                        : '警報監控中',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: triggeredToday > 0 ? Colors.red : Colors.grey.shade700,
                    ),
                  ),
                  Text(
                    '$activeCount 個警報啟用中',
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.grey.shade600,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.grey, size: 20),
          ],
        ),
      ),
    );
  }
}
