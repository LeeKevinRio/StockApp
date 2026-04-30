import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../services/api_service.dart';

/// 即時時間顯示卡片，附帶資料更新時間說明
class RealtimeClockCard extends StatefulWidget {
  final DateTime? lastDataRefresh;
  final String market; // 'TW' or 'US'

  const RealtimeClockCard({super.key, this.lastDataRefresh, this.market = 'TW'});

  @override
  State<RealtimeClockCard> createState() => _RealtimeClockCardState();
}

class _RealtimeClockCardState extends State<RealtimeClockCard> {
  late Timer _timer;
  DateTime _now = DateTime.now();
  Map<String, dynamic>? _tradingStatus; // 後端傳回的交易日狀態（含國定假日）

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        _now = DateTime.now();
      });
    });
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadTradingStatus());
  }

  @override
  void didUpdateWidget(covariant RealtimeClockCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.market != widget.market) {
      _loadTradingStatus();
    }
  }

  Future<void> _loadTradingStatus() async {
    try {
      final api = context.read<ApiService>();
      final status = await api.getTradingStatus(market: widget.market);
      if (mounted) {
        setState(() => _tradingStatus = status);
      }
    } catch (_) {
      // 後端無法取得不影響顯示，fallback 為僅看 weekday/hour
    }
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  bool get _isUS => widget.market == 'US';

  /// 取得該市場的當地時間
  DateTime get _marketLocalTime {
    final utcNow = _now.toUtc();
    if (_isUS) {
      // 美東時間 UTC-4（夏令） / UTC-5（冬令）
      // 簡化：3月第2個週日 ~ 11月第1個週日 為夏令
      final isDST = _isDaylightSaving(utcNow);
      return utcNow.add(Duration(hours: isDST ? -4 : -5));
    }
    // 台灣 UTC+8
    return utcNow.add(const Duration(hours: 8));
  }

  /// 判斷是否為美國夏令時間
  bool _isDaylightSaving(DateTime utc) {
    final year = utc.year;
    // 3月第2個週日
    var marchStart = DateTime.utc(year, 3, 8);
    while (marchStart.weekday != DateTime.sunday) {
      marchStart = marchStart.add(const Duration(days: 1));
    }
    // 11月第1個週日
    var novEnd = DateTime.utc(year, 11, 1);
    while (novEnd.weekday != DateTime.sunday) {
      novEnd = novEnd.add(const Duration(days: 1));
    }
    return utc.isAfter(marchStart) && utc.isBefore(novEnd);
  }

  /// 後端 is_trading_day（包含國定假日判斷），未取得則 null
  bool? get _backendIsTradingDay {
    final s = _tradingStatus;
    if (s == null) return null;
    final v = s['is_trading_day'];
    if (v is bool) return v;
    return null;
  }

  /// 是否為國定假日（透過後端 is_trading_day=false 但今日非週末判斷）
  bool get _isHoliday {
    final isTd = _backendIsTradingDay;
    if (isTd == null) return false;
    final localTime = _marketLocalTime;
    final isWeekend = localTime.weekday > 5;
    return !isTd && !isWeekend;
  }

  /// 判斷市場是否在交易時段（國定假日一律 false）
  bool get _isMarketOpen {
    // 後端說今天不是交易日 → 直接 closed
    final isTd = _backendIsTradingDay;
    if (isTd == false) return false;

    final localTime = _marketLocalTime;
    final weekday = localTime.weekday;
    if (weekday > 5) return false; // 週末

    final timeVal = localTime.hour * 60 + localTime.minute;

    if (_isUS) {
      // 美股：09:30 ~ 16:00 (ET)
      return timeVal >= 570 && timeVal <= 960;
    }
    // 台股：09:00 ~ 13:30
    return timeVal >= 540 && timeVal <= 810;
  }

  String get _marketStatusText {
    if (_isHoliday) {
      return _isUS ? 'Market Holiday' : '國定假日休市';
    }
    if (_isUS) {
      return _isMarketOpen ? 'Market Open' : 'Market Closed';
    }
    return _isMarketOpen ? '開盤中' : '已收盤';
  }

  static const _weekdays = ['', '週一', '週二', '週三', '週四', '週五', '週六', '週日'];
  static const _weekdaysEN = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:'
        '${dt.minute.toString().padLeft(2, '0')}:'
        '${dt.second.toString().padLeft(2, '0')}';
  }

  String _formatDate(DateTime dt, {bool english = false}) {
    final wd = english ? _weekdaysEN[dt.weekday] : _weekdays[dt.weekday];
    return '${dt.year}/${dt.month.toString().padLeft(2, '0')}/'
        '${dt.day.toString().padLeft(2, '0')} $wd';
  }

  Color _marketStatusColor(BuildContext context) {
    if (_isHoliday) return Colors.orange;
    if (_isMarketOpen) return Colors.green;
    return Colors.grey;
  }

  /// 提示「下個交易日為 X，跨假期 N 天」（國定假日或長假時顯示）
  String? get _nextTradingHint {
    final s = _tradingStatus;
    if (s == null) return null;
    final next = s['next_trading_date'] as String?;
    final gap = s['gap_days'];
    final longGap = s['long_gap'] == true;
    if (next == null) return null;
    if (!_isHoliday && !longGap) return null;
    try {
      final dt = DateTime.parse(next);
      const weekdayTw = ['一', '二', '三', '四', '五', '六', '日'];
      final w = '週${weekdayTw[dt.weekday - 1]}';
      if (_isHoliday) {
        return '下個交易日：${dt.month}/${dt.day} ($w)${gap != null ? "，跨 $gap 天" : ""}';
      }
      return '長假後開盤：${dt.month}/${dt.day} ($w)${gap != null ? "，跨 $gap 天波動可能放大" : ""}';
    } catch (_) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final marketLocal = _marketLocalTime;
    final timeStr = _formatTime(marketLocal);
    final dateStr = _formatDate(marketLocal, english: _isUS);

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
                      _isUS ? 'Updated' : '資料更新',
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

            // 第二行：日期 + 時區
            Text(
              '$dateStr  ${_isUS ? (_isDaylightSaving(_now.toUtc()) ? "美東 EDT (UTC-4)" : "美東 EST (UTC-5)") : "台灣 TST (UTC+8)"}',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.textTheme.bodySmall?.color?.withValues(alpha: 0.7),
              ),
            ),

            // 國定假日 / 長假後開盤提示
            if (_nextTradingHint != null) ...[
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.orange.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.orange.withValues(alpha: 0.4)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.event_busy,
                        size: 13, color: Colors.orange.shade800),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        _nextTradingHint!,
                        style: TextStyle(
                          fontSize: 11.5,
                          color: Colors.orange.shade900,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

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

    final items = _isUS
        ? [
            ('Quotes', 'Refresh every 30s (open) / 5min (closed)'),
            ('Watchlist', 'Loaded on each visit'),
            ('AI Tips', 'Loaded async after dashboard'),
            ('Heatmap', 'Cached 5 min, pull to refresh'),
          ]
        : [
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
              _isUS ? 'Data Refresh Rate' : '資料讀取頻率',
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
