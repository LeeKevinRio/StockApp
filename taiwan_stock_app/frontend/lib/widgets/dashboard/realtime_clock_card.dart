import 'dart:async';
import 'package:flutter/material.dart';

/// 即時時間顯示卡片，附帶資料更新時間說明
class RealtimeClockCard extends StatefulWidget {
  final DateTime? lastDataRefresh;

  const RealtimeClockCard({super.key, this.lastDataRefresh});

  @override
  State<RealtimeClockCard> createState() => _RealtimeClockCardState();
}

class _RealtimeClockCardState extends State<RealtimeClockCard> {
  late Timer _timer;
  DateTime _now = DateTime.now();

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        _now = DateTime.now();
      });
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  /// 判斷台股是否在交易時段
  bool get _isTWMarketOpen {
    final twNow = _now.toUtc().add(const Duration(hours: 8));
    final weekday = twNow.weekday;
    if (weekday > 5) return false; // 週末
    final hour = twNow.hour;
    final minute = twNow.minute;
    final timeVal = hour * 60 + minute;
    return timeVal >= 540 && timeVal <= 810; // 09:00 ~ 13:30
  }

  String get _marketStatusText {
    if (_isTWMarketOpen) return '開盤中';
    return '已收盤';
  }

  static const _weekdays = ['', '週一', '週二', '週三', '週四', '週五', '週六', '週日'];

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:'
        '${dt.minute.toString().padLeft(2, '0')}:'
        '${dt.second.toString().padLeft(2, '0')}';
  }

  String _formatDate(DateTime dt) {
    return '${dt.year}/${dt.month.toString().padLeft(2, '0')}/'
        '${dt.day.toString().padLeft(2, '0')} ${_weekdays[dt.weekday]}';
  }

  Color _marketStatusColor(BuildContext context) {
    if (_isTWMarketOpen) return Colors.green;
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final timeStr = _formatTime(_now);
    final dateStr = _formatDate(_now);

    final lastRefreshStr = widget.lastDataRefresh != null
        ? _formatTime(widget.lastDataRefresh!)
        : '--:--:--';

    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 第一行：即時時間 + 市場狀態
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Icon(Icons.access_time, size: 18, color: theme.colorScheme.primary),
                const SizedBox(width: 6),
                Text(
                  timeStr,
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    fontFamily: 'monospace',
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _marketStatusColor(context).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: _marketStatusColor(context),
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _marketStatusText,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: _marketStatusColor(context),
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                // 最後更新時間
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '資料更新',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.textTheme.bodySmall?.color,
                      ),
                    ),
                    Text(
                      lastRefreshStr,
                      style: theme.textTheme.bodySmall?.copyWith(
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 4),

            // 第二行：日期
            Text(
              dateStr,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.textTheme.bodySmall?.color?.withValues(alpha: 0.7),
              ),
            ),

            const Divider(height: 16),

            // 第三行：資料讀取時間說明
            _buildScheduleInfo(context),
          ],
        ),
      ),
    );
  }

  Widget _buildScheduleInfo(BuildContext context) {
    final theme = Theme.of(context);
    final labelStyle = theme.textTheme.labelSmall?.copyWith(
      color: theme.textTheme.bodySmall?.color?.withValues(alpha: 0.8),
      height: 1.5,
    );

    final items = [
      ('即時報價', '盤中每 30 秒 / 收盤後每 5 分鐘'),
      ('自選股', '每次進入首頁時讀取'),
      ('AI 建議', '首頁載入後非同步讀取'),
      ('市場熱力圖', '快取 5 分鐘，下拉可刷新'),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.info_outline, size: 13, color: theme.colorScheme.primary.withValues(alpha: 0.7)),
            const SizedBox(width: 4),
            Text(
              '資料讀取頻率',
              style: theme.textTheme.labelSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.primary.withValues(alpha: 0.9),
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        ...items.map((item) => Padding(
          padding: const EdgeInsets.only(left: 2, bottom: 1),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 80,
                child: Text(item.$1, style: labelStyle?.copyWith(fontWeight: FontWeight.w600)),
              ),
              Expanded(
                child: Text(item.$2, style: labelStyle),
              ),
            ],
          ),
        )),
      ],
    );
  }
}
