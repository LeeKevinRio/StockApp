import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

/// 趨勢強度分數卡片
///
/// 把多個技術指標濃縮成 0-100 的單一分數 + 白話結論，
/// 解決「看完一堆指標還是不知道要不要買」的痛點。
class TrendScoreCard extends StatefulWidget {
  final String stockId;
  final String market;

  const TrendScoreCard({
    super.key,
    required this.stockId,
    this.market = 'TW',
  });

  @override
  State<TrendScoreCard> createState() => _TrendScoreCardState();
}

class _TrendScoreCardState extends State<TrendScoreCard> {
  Map<String, dynamic>? _data;
  bool _isLoading = true;
  String? _error;
  bool _expanded = false;

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
      final data = await api.getTrendScore(widget.stockId, market: widget.market);
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

  Color _colorForVerdict(String? color) {
    switch (color) {
      case 'strong_bull':
        return const Color(0xFFD32F2F); // 強紅（台股慣例：紅漲）
      case 'bull':
        return const Color(0xFFE53935);
      case 'weak_bull':
        return const Color(0xFFEF5350);
      case 'neutral':
        return const Color(0xFF90A4AE);
      case 'weak_bear':
        return const Color(0xFF66BB6A);
      case 'bear':
        return const Color(0xFF43A047);
      case 'strong_bear':
        return const Color(0xFF2E7D32);
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Center(
            child: Column(
              children: [
                SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                SizedBox(height: 12),
                Text('計算趨勢分數中...', style: TextStyle(fontSize: 12)),
              ],
            ),
          ),
        ),
      );
    }

    if (_error != null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              const Icon(Icons.signal_cellular_off, color: Colors.grey, size: 32),
              const SizedBox(height: 8),
              const Text('無法計算趨勢分數', style: TextStyle(fontSize: 14)),
              Text(_error!,
                  style: const TextStyle(fontSize: 11, color: Colors.grey),
                  textAlign: TextAlign.center),
              TextButton.icon(
                onPressed: _load,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('重試'),
              ),
            ],
          ),
        ),
      );
    }

    final data = _data!;
    final score = (data['score'] as num? ?? 50).toInt();
    final verdict = data['verdict'] as String? ?? '中性';
    final color = data['color'] as String?;
    final summary = data['summary'] as String? ?? '';
    final breakdown = (data['breakdown'] as List?) ?? [];
    final highlights = (data['highlights'] as List?) ?? [];
    final mainColor = _colorForVerdict(color);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.speed, size: 20),
                const SizedBox(width: 8),
                const Text('趨勢強度分數',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.refresh, size: 20),
                  tooltip: '重新計算',
                  onPressed: _load,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                _ScoreGauge(score: score, color: mainColor),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: mainColor,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          verdict,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        summary,
                        style: const TextStyle(fontSize: 13, height: 1.5),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (highlights.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: highlights.map<Widget>((h) {
                  final tone = h['tone'] as String? ?? 'neutral';
                  final text = h['text'] as String? ?? '';
                  final isPos = tone == 'positive';
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: (isPos ? Colors.red : Colors.green).withAlpha(30),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: (isPos ? Colors.red : Colors.green).withAlpha(80),
                        width: 0.5,
                      ),
                    ),
                    child: Text(
                      text,
                      style: TextStyle(
                        fontSize: 11,
                        color: isPos ? Colors.red.shade300 : Colors.green.shade400,
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
            const SizedBox(height: 8),
            InkWell(
              onTap: () => setState(() => _expanded = !_expanded),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      _expanded ? '收起細項' : '查看各指標貢獻',
                      style: const TextStyle(fontSize: 12, color: Colors.blue),
                    ),
                    Icon(
                      _expanded ? Icons.expand_less : Icons.expand_more,
                      size: 16,
                      color: Colors.blue,
                    ),
                  ],
                ),
              ),
            ),
            if (_expanded) ...breakdown.map<Widget>((b) => _BreakdownRow(item: b)),
          ],
        ),
      ),
    );
  }
}

class _ScoreGauge extends StatelessWidget {
  final int score; // 0-100
  final Color color;
  const _ScoreGauge({required this.score, required this.color});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 100,
      height: 100,
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 100,
            height: 100,
            child: CustomPaint(
              painter: _GaugePainter(score: score.toDouble(), color: color),
            ),
          ),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '$score',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const Text('/ 100', style: TextStyle(fontSize: 10, color: Colors.grey)),
            ],
          ),
        ],
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double score; // 0-100
  final Color color;

  _GaugePainter({required this.score, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2 - 6;

    // 背景圓環
    final bgPaint = Paint()
      ..color = Colors.grey.withAlpha(60)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      math.pi * 0.75,
      math.pi * 1.5,
      false,
      bgPaint,
    );

    // 進度弧（依分數比例）
    final progressPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      math.pi * 0.75,
      math.pi * 1.5 * (score / 100),
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _GaugePainter oldDelegate) {
    return oldDelegate.score != score || oldDelegate.color != color;
  }
}

class _BreakdownRow extends StatelessWidget {
  final dynamic item;
  const _BreakdownRow({required this.item});

  @override
  Widget build(BuildContext context) {
    final name = item['name'] as String? ?? '';
    final score = (item['score'] as num? ?? 0).toDouble();
    final max = (item['max'] as num? ?? 1).toDouble();
    final signal = item['signal'] as String? ?? '';
    final ratio = max > 0 ? (score / max).clamp(-1.0, 1.0) : 0.0;
    final isPos = score > 0;
    final isNeg = score < 0;
    final color = isPos ? Colors.red : (isNeg ? Colors.green : Colors.grey);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              SizedBox(
                width: 80,
                child: Text(name,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
              ),
              Expanded(
                child: Stack(
                  children: [
                    Container(
                      height: 6,
                      decoration: BoxDecoration(
                        color: Colors.grey.withAlpha(40),
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                    // 中線分隔（左 = 空，右 = 多）
                    Align(
                      alignment: Alignment.center,
                      child: Container(width: 1, height: 6, color: Colors.grey.withAlpha(120)),
                    ),
                    Align(
                      alignment: ratio >= 0 ? Alignment.centerLeft : Alignment.centerRight,
                      child: FractionallySizedBox(
                        widthFactor: ratio.abs() * 0.5,
                        child: Align(
                          alignment: ratio >= 0 ? Alignment.centerLeft : Alignment.centerRight,
                          child: Container(
                            margin: EdgeInsets.only(
                              left: ratio >= 0 ? MediaQuery.of(context).size.width * 0 : 0,
                            ),
                            height: 6,
                            decoration: BoxDecoration(
                              color: color,
                              borderRadius: BorderRadius.circular(3),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                width: 50,
                child: Text(
                  '${score >= 0 ? "+" : ""}${score.toStringAsFixed(0)} / ${max.toInt()}',
                  style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600),
                  textAlign: TextAlign.right,
                ),
              ),
            ],
          ),
          if (signal.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(left: 80, top: 2),
              child: Text(
                signal,
                style: TextStyle(fontSize: 11, color: Colors.grey.shade400),
              ),
            ),
        ],
      ),
    );
  }
}
