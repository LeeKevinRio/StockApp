import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/notification_provider.dart';

/// 通知徽章組件
/// 顯示未讀通知數量
class NotificationBadge extends StatelessWidget {
  final Widget child;
  final Color? badgeColor;
  final Color? textColor;
  final double badgeSize;
  final bool showZero;

  const NotificationBadge({
    super.key,
    required this.child,
    this.badgeColor,
    this.textColor,
    this.badgeSize = 18,
    this.showZero = false,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<NotificationProvider>(
      builder: (context, provider, _) {
        final count = provider.unreadCount;

        if (count == 0 && !showZero) {
          return child;
        }

        return Semantics(
          label: '$count 則未讀通知',
          child: Stack(
            clipBehavior: Clip.none,
            children: [
              child,
              Positioned(
                right: -6,
                top: -6,
                child: ExcludeSemantics(
                  child: _Badge(
                    count: count,
                    color: badgeColor ?? Theme.of(context).colorScheme.error,
                    textColor: textColor ?? Colors.white,
                    size: badgeSize,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _Badge extends StatelessWidget {
  final int count;
  final Color color;
  final Color textColor;
  final double size;

  const _Badge({
    required this.count,
    required this.color,
    required this.textColor,
    required this.size,
  });

  @override
  Widget build(BuildContext context) {
    final displayCount = count > 99 ? '99+' : count.toString();
    final isWide = displayCount.length > 2;

    return Container(
      constraints: BoxConstraints(
        minWidth: size,
        minHeight: size,
      ),
      padding: EdgeInsets.symmetric(
        horizontal: isWide ? 4 : 0,
      ),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(size / 2),
        border: Border.all(
          color: Theme.of(context).scaffoldBackgroundColor,
          width: 1.5,
        ),
      ),
      child: Center(
        child: Text(
          displayCount,
          style: TextStyle(
            color: textColor,
            fontSize: size * 0.6,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}

/// 通知圖標按鈕（帶徽章）
class NotificationIconButton extends StatelessWidget {
  final VoidCallback onPressed;
  final Color? iconColor;
  final double iconSize;

  const NotificationIconButton({
    super.key,
    required this.onPressed,
    this.iconColor,
    this.iconSize = 24,
  });

  @override
  Widget build(BuildContext context) {
    return NotificationBadge(
      child: IconButton(
        icon: Icon(
          Icons.notifications_outlined,
          color: iconColor,
          size: iconSize,
        ),
        onPressed: onPressed,
        tooltip: '通知',
      ),
    );
  }
}
