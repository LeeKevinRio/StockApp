import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../services/api_service.dart';

/// AI 預測準確率小卡（信任背書）
/// 顯示最近 30 天 AI 預測的方向準確率與平均誤差，
/// 點擊跳轉至完整準確度頁面。
class AIAccuracyCard extends StatefulWidget {
  final String? market; // 'TW' / 'US' / null
  final VoidCallback? onTap;

  const AIAccuracyCard({super.key, this.market, this.onTap});

  @override
  State<AIAccuracyCard> createState() => _AIAccuracyCardState();
}

class _AIAccuracyCardState extends State<AIAccuracyCard> {
  Map<String, dynamic>? _stats;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _load());
  }

  @override
  void didUpdateWidget(covariant AIAccuracyCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.market != widget.market) {
      _load();
    }
  }

  Future<void> _load() async {
    if (!mounted) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = context.read<ApiService>();
      final stats = await api.getPredictionStatistics(days: 30, market: widget.market);
      if (!mounted) return;
      setState(() {
        _stats = stats;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Color _accuracyColor(double acc) {
    if (acc >= 80) return const Color(0xFF2E7D32); // 深綠：優異
    if (acc >= 60) return const Color(0xFF66BB6A); // 中綠：可信
    if (acc >= 50) return const Color(0xFFFB8C00); // 橘：中性
    return const Color(0xFFE53935); // 紅：偏低
  }

  String _accuracyLabel(double acc) {
    if (acc >= 80) return '表現優異';
    if (acc >= 60) return '可信';
    if (acc >= 50) return '基準以上';
    return '需更多樣本';
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return _shellCard(
        context,
        child: Row(
          children: const [
            SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Text('載入 AI 準確率…', style: TextStyle(fontSize: 13)),
          ],
        ),
      );
    }

    final stats = _stats;
    if (stats == null || _error != null) {
      return _shellCard(
        context,
        child: const Row(
          children: [
            Icon(Icons.info_outline, size: 18, color: Colors.grey),
            SizedBox(width: 8),
            Expanded(
              child: Text('AI 準確率資料暫不可用',
                  style: TextStyle(fontSize: 13, color: Colors.grey)),
            ),
          ],
        ),
      );
    }

    final total = (stats['total_predictions'] ?? 0) as int;
    final acc = (stats['direction_accuracy'] ?? 0).toDouble();
    final inRange = (stats['within_range_rate'] ?? 0).toDouble();
    final avgErr = (stats['avg_error_percent'] ?? 0).toDouble();

    if (total == 0) {
      return _shellCard(
        context,
        child: const Row(
          children: [
            Icon(Icons.hourglass_top, size: 18, color: Colors.grey),
            SizedBox(width: 8),
            Expanded(
              child: Text('AI 預測樣本累積中（自選股有預測後即會顯示準確率）',
                  style: TextStyle(fontSize: 13, color: Colors.grey)),
            ),
          ],
        ),
      );
    }

    final color = _accuracyColor(acc);
    final label = _accuracyLabel(acc);

    return InkWell(
      onTap: widget.onTap,
      borderRadius: BorderRadius.circular(12),
      child: Card(
        elevation: 1,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: color.withAlpha(30),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.verified, color: color, size: 18),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'AI 預測準確率',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(width: 6),
                  Text('近 30 天',
                      style: TextStyle(
                          fontSize: 11,
                          color: Theme.of(context).hintColor)),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: color.withAlpha(40),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      label,
                      style: TextStyle(
                          fontSize: 11, color: color, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${acc.toStringAsFixed(1)}%',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: color,
                      height: 1,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Text(
                      '方向正確',
                      style: TextStyle(
                          fontSize: 12, color: Theme.of(context).hintColor),
                    ),
                  ),
                  const Spacer(),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text('$total 次預測',
                          style: TextStyle(
                              fontSize: 11,
                              color: Theme.of(context).hintColor)),
                      const SizedBox(height: 2),
                      Text('平均誤差 ${avgErr.toStringAsFixed(2)}%',
                          style: TextStyle(
                              fontSize: 11,
                              color: Theme.of(context).hintColor)),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 10),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: (acc / 100).clamp(0.0, 1.0),
                  minHeight: 6,
                  backgroundColor: color.withAlpha(30),
                  valueColor: AlwaysStoppedAnimation(color),
                ),
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  Icon(Icons.center_focus_strong,
                      size: 12, color: Theme.of(context).hintColor),
                  const SizedBox(width: 4),
                  Text(
                    '預測區間命中率 ${inRange.toStringAsFixed(1)}%',
                    style: TextStyle(
                        fontSize: 11,
                        color: Theme.of(context).hintColor),
                  ),
                  const Spacer(),
                  Text('點擊查看完整統計',
                      style: TextStyle(
                          fontSize: 11,
                          color: Theme.of(context).colorScheme.primary)),
                  const SizedBox(width: 2),
                  Icon(Icons.chevron_right,
                      size: 14, color: Theme.of(context).colorScheme.primary),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _shellCard(BuildContext context, {required Widget child}) {
    return Card(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: child,
      ),
    );
  }
}
