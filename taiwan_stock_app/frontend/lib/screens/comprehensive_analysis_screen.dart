import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:math';
import '../services/api_service.dart';
import '../models/comprehensive_analysis.dart';

class ComprehensiveAnalysisView extends StatefulWidget {
  final String stockId;
  final String market;

  const ComprehensiveAnalysisView({
    super.key,
    required this.stockId,
    this.market = 'TW',
  });

  @override
  State<ComprehensiveAnalysisView> createState() =>
      _ComprehensiveAnalysisViewState();
}

class _ComprehensiveAnalysisViewState extends State<ComprehensiveAnalysisView> {
  ComprehensiveAnalysis? _analysis;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadAnalysis();
  }

  Future<void> _loadAnalysis() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final data = await apiService.getComprehensiveAnalysis(
        widget.stockId,
        market: widget.market,
      );
      setState(() {
        _analysis = ComprehensiveAnalysis.fromJson(data);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('正在進行綜合分析...', style: TextStyle(color: Colors.grey)),
            SizedBox(height: 8),
            Text('分析6維度數據中，請稍候',
                style: TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
      );
    }

    if (_error != null) {
      final isQuota = _error!.contains('429') || _error!.contains('quota') || _error!.contains('配額');
      final isNetwork = _error!.contains('Failed to fetch') || _error!.contains('SocketException');
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isQuota ? Icons.hourglass_empty : isNetwork ? Icons.wifi_off : Icons.error_outline,
                size: 48,
                color: isQuota ? Colors.orange : Colors.red,
              ),
              const SizedBox(height: 16),
              Text(
                isQuota ? 'AI 額度已用完' : isNetwork ? '無法連線' : '分析失敗',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                isQuota
                    ? 'AI 服務免費額度已耗盡，請稍後再試。'
                    : isNetwork
                        ? '請檢查網路連線或後端服務狀態。'
                        : '伺服器發生錯誤，請稍後再試。',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadAnalysis,
                icon: const Icon(Icons.refresh),
                label: const Text('重試'),
              ),
            ],
          ),
        ),
      );
    }

    if (_analysis == null) return const SizedBox();

    return RefreshIndicator(
      onRefresh: _loadAnalysis,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildHealthScoreCard(),
            const SizedBox(height: 16),
            _buildRadarChartCard(),
            const SizedBox(height: 16),
            _buildAISummaryCard(),
            const SizedBox(height: 16),
            ..._buildDimensionCards(),
            const SizedBox(height: 100), // 留給 FAB 按鈕的空間
          ],
        ),
      ),
    );
  }

  // ============ 健康分數圓形量表 ============

  Widget _buildHealthScoreCard() {
    final a = _analysis!;
    final grade = a.healthGrade;
    final score = a.totalScore;
    final color = _gradeColor(grade);

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Text('${a.stockName} (${a.stockId})',
                style: const TextStyle(
                    fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(
              '${a.market == "US" ? "\$" : "NT\$"}${a.latestPrice.toStringAsFixed(2)}'
              '  5日 ${a.priceChange5d >= 0 ? "+" : ""}${a.priceChange5d.toStringAsFixed(2)}%'
              '  20日 ${a.priceChange20d >= 0 ? "+" : ""}${a.priceChange20d.toStringAsFixed(2)}%',
              style: TextStyle(
                fontSize: 13,
                color: a.priceChange5d >= 0 ? Colors.red : Colors.green,
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: 160,
              height: 160,
              child: CustomPaint(
                painter: _HealthGaugePainter(
                  score: score,
                  grade: grade,
                  color: color,
                ),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              '健康等級 $grade',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '綜合評分 ${score.toStringAsFixed(1)}',
              style: const TextStyle(fontSize: 14, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  // ============ 雷達圖 ============

  Widget _buildRadarChartCard() {
    final radar = _analysis!.radar;
    if (radar.labels.isEmpty) return const SizedBox();

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text('多維度分析雷達圖',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            SizedBox(
              height: 280,
              child: RadarChart(
                RadarChartData(
                  dataSets: [
                    RadarDataSet(
                      dataEntries: radar.values
                          .map((v) => RadarEntry(value: v.toDouble()))
                          .toList(),
                      fillColor: Colors.blue.withAlpha(40),
                      borderColor: Colors.blue,
                      borderWidth: 2,
                      entryRadius: 3,
                    ),
                  ],
                  radarBackgroundColor: Colors.transparent,
                  borderData: FlBorderData(show: false),
                  radarBorderData:
                      const BorderSide(color: Colors.grey, width: 0.5),
                  gridBorderData:
                      const BorderSide(color: Colors.grey, width: 0.3),
                  tickCount: 4,
                  ticksTextStyle: const TextStyle(
                      fontSize: 10, color: Colors.grey),
                  tickBorderData:
                      const BorderSide(color: Colors.grey, width: 0.3),
                  getTitle: (index, angle) {
                    if (index >= radar.labels.length) {
                      return RadarChartTitle(text: '');
                    }
                    final label = radar.labels[index];
                    final value = radar.values[index];
                    return RadarChartTitle(
                      text: '$label\n$value',
                      angle: 0,
                    );
                  },
                  titleTextStyle: const TextStyle(
                      fontSize: 12, fontWeight: FontWeight.w600),
                  titlePositionPercentageOffset: 0.2,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============ AI 摘要 ============

  Widget _buildAISummaryCard() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.auto_awesome, color: Colors.blue.shade700, size: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('AI 綜合分析',
                      style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.blue.shade700)),
                  const SizedBox(height: 4),
                  Text(_analysis!.aiSummary,
                      style: const TextStyle(fontSize: 14, height: 1.4)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============ 維度卡片 ============

  List<Widget> _buildDimensionCards() {
    final dims = _analysis!.dimensions;
    final order = _analysis!.market == 'TW'
        ? ['technical', 'chip', 'fundamental', 'news', 'social', 'macro']
        : ['technical', 'fundamental', 'news', 'social', 'macro'];

    return order.where((k) => dims.containsKey(k)).map((key) {
      final dim = dims[key]!;
      if (dim.score == null) return const SizedBox.shrink();
      return _buildSingleDimensionCard(key, dim);
    }).toList();
  }

  Widget _buildSingleDimensionCard(String key, DimensionScore dim) {
    final color = _dimensionColor(key);
    final icon = _dimensionIcon(key);
    final normalized = dim.normalized ?? 50;

    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: color.withAlpha(30),
          child: Icon(icon, color: color, size: 20),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(dim.label,
                  style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: _scoreColor(dim.score ?? 0).withAlpha(25),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '${dim.score?.toStringAsFixed(1) ?? "N/A"}',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: _scoreColor(dim.score ?? 0),
                ),
              ),
            ),
          ],
        ),
        subtitle: Row(
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: normalized / 100,
                  backgroundColor: const Color(0xFF2C3A47),
                  valueColor: AlwaysStoppedAnimation(color),
                  minHeight: 6,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text('${(dim.weight * 100).toStringAsFixed(0)}%',
                style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildDetailRow('信號', _signalText(dim.signal)),
                ...dim.details.entries
                    .where((e) => e.value != null && e.value.toString().isNotEmpty && e.value.toString() != 'N/A')
                    .map((e) => _buildDetailRow(
                        _detailLabel(e.key),
                        _cleanDetailValue(e.value))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          Flexible(
            child: Text(value,
                style: const TextStyle(fontSize: 13),
                textAlign: TextAlign.end,
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }

  // ============ 輔助方法 ============

  Color _gradeColor(String grade) {
    switch (grade) {
      case 'A':
        return Colors.green.shade700;
      case 'B':
        return Colors.lightGreen.shade700;
      case 'C':
        return Colors.amber.shade700;
      case 'D':
        return Colors.orange.shade700;
      case 'E':
        return Colors.deepOrange.shade700;
      case 'F':
        return Colors.red.shade700;
      default:
        return Colors.grey;
    }
  }

  Color _scoreColor(double score) {
    if (score > 30) return Colors.green.shade700;
    if (score > 0) return Colors.lightGreen.shade700;
    if (score > -30) return Colors.orange.shade700;
    return Colors.red.shade700;
  }

  Color _dimensionColor(String key) {
    switch (key) {
      case 'technical':
        return Colors.blue;
      case 'chip':
        return Colors.purple;
      case 'fundamental':
        return Colors.teal;
      case 'news':
        return Colors.orange;
      case 'social':
        return Colors.indigo;
      case 'macro':
        return Colors.brown;
      default:
        return Colors.grey;
    }
  }

  IconData _dimensionIcon(String key) {
    switch (key) {
      case 'technical':
        return Icons.show_chart;
      case 'chip':
        return Icons.groups;
      case 'fundamental':
        return Icons.account_balance;
      case 'news':
        return Icons.newspaper;
      case 'social':
        return Icons.forum;
      case 'macro':
        return Icons.public;
      default:
        return Icons.analytics;
    }
  }

  String _signalText(String signal) {
    const map = {
      'very_positive': '非常正面',
      'positive': '正面',
      'neutral': '中性',
      'negative': '負面',
      'very_negative': '非常負面',
      'bullish': '偏多',
      'bearish': '偏空',
      'no_data': '無數據',
      'strong_buy': '強力買進',
      'buy': '買進',
      'sell': '賣出',
      'strong_sell': '強力賣出',
      'N/A': '無數據',
    };
    // 先精確匹配
    if (map.containsKey(signal)) return map[signal]!;
    // 處理複合信號如 "very_positive_消息面利多"、"neutral_Neutral"
    // 取底線分隔後的中文部分，或映射英文部分
    for (final entry in map.entries) {
      if (signal.startsWith(entry.key)) {
        // 如果後面有中文說明，優先取中文
        final rest = signal.substring(entry.key.length).replaceAll('_', ' ').trim();
        if (rest.isNotEmpty && RegExp(r'[\u4e00-\u9fff]').hasMatch(rest)) {
          return rest;
        }
        return entry.value;
      }
    }
    // 最後兜底：把底線換成空格
    return signal.replaceAll('_', ' ');
  }

  /// 清理詳細值（移除底線混合文字如 "above_upper_危險超買" → "危險超買"）
  String _cleanDetailValue(dynamic value) {
    if (value == null) return '';
    final s = value is List ? (value as List<dynamic>).join(', ') : value.toString();
    if (s.isEmpty || s == 'null' || s == 'N/A') return '';
    // 如果包含底線且有中文，只取中文部分
    if (s.contains('_') && RegExp(r'[\u4e00-\u9fff]').hasMatch(s)) {
      final parts = s.split('_');
      final chineseParts = parts.where((p) => RegExp(r'[\u4e00-\u9fff]').hasMatch(p)).toList();
      if (chineseParts.isNotEmpty) return chineseParts.join(' ');
    }
    // 英文信號直接翻譯
    const valueMap = {
      'bullish': '偏多',
      'bearish': '偏空',
      'neutral': '中性',
      'above_middle': '中軌之上',
      'below_middle': '中軌之下',
    };
    if (valueMap.containsKey(s)) return valueMap[s]!;
    return s.replaceAll('_', ' ');
  }

  String _detailLabel(String key) {
    const map = {
      'rsi': 'RSI',
      'macd_status': 'MACD',
      'ma_trend': '均線趨勢',
      'bb_position': '布林通道',
      'foreign_trend': '外資趨勢',
      'trust_trend': '投信趨勢',
      'margin_trend': '融資趨勢',
      'per': '本益比',
      'eps': 'EPS',
      'roe': 'ROE',
      'dividend_yield': '殖利率',
      'news_count': '新聞數',
      'positive_news': '正面新聞',
      'negative_news': '負面新聞',
      'total_mentions': '總提及',
      'positive': '正面聲量',
      'negative': '負面聲量',
      'platforms': '來源平台',
    };
    return map[key] ?? key;
  }
}

// ============ 健康分數量表繪製器 ============

class _HealthGaugePainter extends CustomPainter {
  final double score;
  final String grade;
  final Color color;

  _HealthGaugePainter({
    required this.score,
    required this.grade,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 10;

    // 背景弧
    final bgPaint = Paint()
      ..color = const Color(0xFF2C3A47)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 14
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      pi * 0.75,
      pi * 1.5,
      false,
      bgPaint,
    );

    // 前景弧（分數映射到 0~270 度）
    // score 範圍 -100 ~ +100，映射到 0 ~ 1.5*pi
    final normalized = ((score + 100) / 200).clamp(0.0, 1.0);
    final sweepAngle = normalized * pi * 1.5;

    final fgPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 14
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      pi * 0.75,
      sweepAngle,
      false,
      fgPaint,
    );

    // 中間文字 - 等級
    final textPainter = TextPainter(
      text: TextSpan(
        text: grade,
        style: TextStyle(
          fontSize: 48,
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(
        center.dx - textPainter.width / 2,
        center.dy - textPainter.height / 2 + 5,
      ),
    );
  }

  @override
  bool shouldRepaint(covariant _HealthGaugePainter oldDelegate) {
    return oldDelegate.score != score || oldDelegate.grade != grade;
  }
}
