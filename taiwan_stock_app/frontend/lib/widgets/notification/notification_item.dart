import 'package:flutter/material.dart';
import '../../models/notification.dart';

/// 通知列表項組件
class NotificationItem extends StatelessWidget {
  final AppNotification notification;
  final VoidCallback? onTap;
  final VoidCallback? onDismiss;

  const NotificationItem({
    super.key,
    required this.notification,
    this.onTap,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Dismissible(
      key: Key(notification.id),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => onDismiss?.call(),
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        color: Colors.red,
        child: const Icon(
          Icons.delete,
          color: Colors.white,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: notification.isRead
                ? null
                : (isDark
                    ? Colors.blue.withValues(alpha: 0.1)
                    : Colors.blue.withValues(alpha: 0.05)),
            border: Border(
              bottom: BorderSide(
                color: theme.dividerColor.withValues(alpha: 0.3),
                width: 0.5,
              ),
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 圖標
              _NotificationIcon(
                type: notification.type,
                priority: notification.priority,
              ),
              const SizedBox(width: 12),
              // 內容
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 標題行
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            notification.title,
                            style: TextStyle(
                              fontWeight: notification.isRead
                                  ? FontWeight.normal
                                  : FontWeight.bold,
                              fontSize: 15,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (!notification.isRead)
                          Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: Colors.blue,
                              shape: BoxShape.circle,
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    // 內容
                    Text(
                      notification.body,
                      style: TextStyle(
                        color: theme.textTheme.bodyMedium?.color?.withValues(alpha: 0.7),
                        fontSize: 13,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 6),
                    // 時間和類型
                    Row(
                      children: [
                        _TypeTag(type: notification.type),
                        const Spacer(),
                        Text(
                          _formatTime(notification.createdAt),
                          style: TextStyle(
                            color: theme.textTheme.bodySmall?.color?.withValues(alpha: 0.5),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);

    if (diff.inMinutes < 1) {
      return '剛才';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes} 分鐘前';
    } else if (diff.inHours < 24) {
      return '${diff.inHours} 小時前';
    } else if (diff.inDays < 7) {
      return '${diff.inDays} 天前';
    } else {
      return '${time.month}/${time.day}';
    }
  }
}

/// 通知圖標
class _NotificationIcon extends StatelessWidget {
  final NotificationType type;
  final NotificationPriority priority;

  const _NotificationIcon({
    required this.type,
    required this.priority,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: _getBackgroundColor(context),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Icon(
        _getIcon(),
        color: _getIconColor(),
        size: 22,
      ),
    );
  }

  IconData _getIcon() {
    switch (type) {
      case NotificationType.priceAlert:
        return Icons.trending_up;
      case NotificationType.percentChangeAlert:
        return Icons.percent;
      case NotificationType.volumeAlert:
        return Icons.bar_chart;
      case NotificationType.signalAlert:
        return Icons.notifications_active;
      case NotificationType.aiSuggestion:
        return Icons.psychology;
      case NotificationType.patternDetected:
        return Icons.auto_graph;
      case NotificationType.news:
        return Icons.article;
      case NotificationType.systemMessage:
        return Icons.info_outline;
    }
  }

  Color _getIconColor() {
    switch (type) {
      case NotificationType.priceAlert:
      case NotificationType.percentChangeAlert:
        return Colors.orange;
      case NotificationType.volumeAlert:
        return Colors.blue;
      case NotificationType.signalAlert:
        return Colors.red;
      case NotificationType.aiSuggestion:
        return Colors.purple;
      case NotificationType.patternDetected:
        return Colors.teal;
      case NotificationType.news:
        return Colors.green;
      case NotificationType.systemMessage:
        return Colors.grey;
    }
  }

  Color _getBackgroundColor(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return _getIconColor().withValues(alpha: isDark ? 0.2 : 0.1);
  }
}

/// 類型標籤
class _TypeTag extends StatelessWidget {
  final NotificationType type;

  const _TypeTag({required this.type});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: _getColor().withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        _getText(),
        style: TextStyle(
          color: _getColor(),
          fontSize: 10,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  String _getText() {
    switch (type) {
      case NotificationType.priceAlert:
        return '價格警報';
      case NotificationType.percentChangeAlert:
        return '漲跌幅';
      case NotificationType.volumeAlert:
        return '成交量';
      case NotificationType.signalAlert:
        return '交易信號';
      case NotificationType.aiSuggestion:
        return 'AI 建議';
      case NotificationType.patternDetected:
        return '形態識別';
      case NotificationType.news:
        return '新聞';
      case NotificationType.systemMessage:
        return '系統';
    }
  }

  Color _getColor() {
    switch (type) {
      case NotificationType.priceAlert:
      case NotificationType.percentChangeAlert:
        return Colors.orange;
      case NotificationType.volumeAlert:
        return Colors.blue;
      case NotificationType.signalAlert:
        return Colors.red;
      case NotificationType.aiSuggestion:
        return Colors.purple;
      case NotificationType.patternDetected:
        return Colors.teal;
      case NotificationType.news:
        return Colors.green;
      case NotificationType.systemMessage:
        return Colors.grey;
    }
  }
}
