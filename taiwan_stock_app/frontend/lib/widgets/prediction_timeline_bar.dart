import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

/// AI 預測戰績時間軸
///
/// 放在 K 線圖上方，顯示：
/// 1. 過去 N 天 AI 在這支股票的命中率（信任指標）
/// 2. 每個預測點的時間軸（綠↑命中、紅↓未中、灰圓 pending）
/// 3. 點擊預測點查看當時預測 vs 實際
class PredictionTimelineBar extends StatefulWidget {
  final String stockId;
  final int days;

  const PredictionTimelineBar({
    super.key,
    required this.stockId,
    this.days = 90,
  });

  @override
  State<PredictionTimelineBar> createState() => _PredictionTimelineBarState();
}

class _PredictionTimelineBarState extends State<PredictionTimelineBar> {
  Map<String, dynamic>? _data;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final data = await api.getStockPredictionTimeline(widget.stockId, days: widget.days);
      if (!mounted) return;
      setState(() {
        _data = data;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const SizedBox(
        height: 56,
        child: Center(
          child: SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 1.5),
          ),
        ),
      );
    }

    if (_error != null || _data == null) {
      return const SizedBox.shrink();
    }

    final data = _data!;
    final total = (data['total'] as num? ?? 0).toInt();
    final verified = (data['verified'] as num? ?? 0).toInt();
    final correct = (data['correct'] as num? ?? 0).toInt();
    final accuracy = (data['accuracy'] as num? ?? 0).toDouble();
    final avgError = (data['avg_error'] as num? ?? 0).toDouble();
    final marks = (data['marks'] as List?) ?? [];

    if (total == 0) {
      return Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.grey.withAlpha(30),
          borderRadius: BorderRadius.circular(6),
        ),
        child: const Row(
          children: [
            Icon(Icons.history, size: 14, color: Colors.grey),
            SizedBox(width: 8),
            Text(
              'AI 尚未對這支股票做過預測',
              style: TextStyle(fontSize: 11, color: Colors.grey),
            ),
          ],
        ),
      );
    }

    final accuracyColor = accuracy >= 60
        ? Colors.green.shade400
        : accuracy >= 50
            ? Colors.amber.shade600
            : Colors.red.shade400;

    return Container(
      margin: const EdgeInsets.fromLTRB(12, 8, 12, 4),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF1E272E),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: accuracyColor.withAlpha(80), width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.psychology_alt, size: 14, color: Colors.amber),
              const SizedBox(width: 6),
              const Text(
                'AI 戰績',
                style: TextStyle(fontSize: 11, color: Colors.white70, fontWeight: FontWeight.w600),
              ),
              const SizedBox(width: 8),
              if (verified > 0) ...[
                Text(
                  '${accuracy.toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontSize: 14,
                    color: accuracyColor,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  '($correct/$verified 命中)',
                  style: const TextStyle(fontSize: 10, color: Colors.white54),
                ),
                const SizedBox(width: 8),
                Text(
                  '誤差 ±${avgError.toStringAsFixed(2)}%',
                  style: const TextStyle(fontSize: 10, color: Colors.white54),
                ),
              ] else ...[
                Text(
                  '$total 筆預測',
                  style: const TextStyle(fontSize: 10, color: Colors.white54),
                ),
                const SizedBox(width: 6),
                const Text(
                  '（待驗證）',
                  style: TextStyle(fontSize: 10, color: Colors.white38),
                ),
              ],
              const Spacer(),
              const Text(
                '近 90 天',
                style: TextStyle(fontSize: 10, color: Colors.white38),
              ),
            ],
          ),
          const SizedBox(height: 6),
          SizedBox(
            height: 28,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              reverse: true, // 最新的在右邊
              child: Row(
                children: marks.map<Widget>((m) => _MarkChip(mark: m)).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MarkChip extends StatelessWidget {
  final dynamic mark;
  const _MarkChip({required this.mark});

  @override
  Widget build(BuildContext context) {
    final dir = mark['predicted_direction'] as String? ?? '';
    final correct = mark['correct'] as bool?;
    final dateStr = mark['date'] as String? ?? '';
    final isUp = dir == 'UP';

    Color bg;
    Color fg;
    IconData icon;
    if (correct == null) {
      // 尚未驗證
      bg = Colors.grey.withAlpha(60);
      fg = Colors.white60;
      icon = isUp ? Icons.arrow_upward : Icons.arrow_downward;
    } else if (correct) {
      // 命中
      bg = isUp ? Colors.red.withAlpha(80) : Colors.green.withAlpha(80);
      fg = isUp ? Colors.red.shade300 : Colors.green.shade300;
      icon = Icons.check;
    } else {
      // 未中
      bg = Colors.grey.withAlpha(40);
      fg = Colors.white38;
      icon = Icons.close;
    }

    String shortDate = dateStr;
    try {
      final dt = DateTime.parse(dateStr);
      shortDate = '${dt.month}/${dt.day}';
    } catch (_) {}

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: GestureDetector(
        onTap: () => _showDetail(context),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                isUp ? Icons.arrow_upward : Icons.arrow_downward,
                size: 10,
                color: fg,
              ),
              Icon(icon, size: 10, color: fg),
              const SizedBox(width: 2),
              Text(
                shortDate,
                style: TextStyle(fontSize: 9, color: fg, fontWeight: FontWeight.w500),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showDetail(BuildContext context) {
    final dir = mark['predicted_direction'] as String? ?? '';
    final isUp = dir == 'UP';
    final predicted = (mark['predicted_change'] as num? ?? 0).toDouble();
    final actual = mark['actual_change'] as num?;
    final correct = mark['correct'] as bool?;
    final basePrice = (mark['base_price'] as num? ?? 0).toDouble();
    final actualClose = mark['actual_close'] as num?;
    final probability = ((mark['predicted_probability'] as num? ?? 0).toDouble() * 100);
    final provider = mark['ai_provider'] as String? ?? 'Unknown';
    final dateStr = mark['date'] as String? ?? '';
    final predDateStr = mark['prediction_date'] as String? ?? '';

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('預測詳情 · $dateStr'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _kv('預測產生日', predDateStr),
            _kv('預測方向', isUp ? '上漲 ▲' : '下跌 ▼'),
            _kv('預測幅度', '${predicted >= 0 ? "+" : ""}${predicted.toStringAsFixed(2)}%'),
            _kv('預測機率', '${probability.toStringAsFixed(0)}%'),
            _kv('預測時收盤', basePrice > 0 ? basePrice.toStringAsFixed(2) : '-'),
            const Divider(),
            if (actual != null)
              _kv('實際漲跌', '${actual >= 0 ? "+" : ""}${actual.toStringAsFixed(2)}%')
            else
              _kv('實際結果', '尚未驗證'),
            if (actualClose != null)
              _kv('實際收盤', actualClose.toStringAsFixed(2)),
            if (correct != null)
              _kv(
                '命中與否',
                correct ? '✓ 方向正確' : '✗ 方向錯誤',
                color: correct ? Colors.green : Colors.red,
              ),
            const SizedBox(height: 8),
            Text('AI 提供者：$provider',
                style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('關閉'),
          ),
        ],
      ),
    );
  }

  Widget _kv(String k, String v, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(k, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ),
          Expanded(
            child: Text(
              v,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
