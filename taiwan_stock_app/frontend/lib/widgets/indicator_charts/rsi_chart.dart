import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../models/indicator_data.dart';

class RSIChart extends StatefulWidget {
  final List<IndicatorDataPoint> data;

  const RSIChart({super.key, required this.data});

  @override
  State<RSIChart> createState() => _RSIChartState();
}

class _RSIChartState extends State<RSIChart> {
  bool _showRSI = true;
  bool _showOverbought = true;
  bool _showOversold = true;
  int? _touchedIndex;

  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Center(child: Text('無數據'));
    }

    final validData = widget.data.where((d) => d.value != null).toList();
    if (validData.isEmpty) {
      return const Center(child: Text('無有效數據'));
    }

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'RSI (14)',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              Text(
                '最新: ${validData.last.value?.toStringAsFixed(2) ?? "-"}',
                style: TextStyle(
                  fontSize: 14,
                  color: _getRSIColor(validData.last.value),
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          _buildLegend(context),
          const SizedBox(height: 16),
          // Crosshair data panel
          if (_touchedIndex != null && _touchedIndex! < validData.length)
            _buildDataPanel(context, validData[_touchedIndex!]),
          Expanded(
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 20,
                  getDrawingHorizontalLine: (value) {
                    if (value == 70 && _showOverbought) {
                      return FlLine(
                        color: Colors.red.withValues(alpha: 0.5),
                        strokeWidth: 1,
                        dashArray: [5, 5],
                      );
                    }
                    if (value == 30 && _showOversold) {
                      return FlLine(
                        color: Colors.green.withValues(alpha: 0.5),
                        strokeWidth: 1,
                        dashArray: [5, 5],
                      );
                    }
                    return FlLine(
                      color: Theme.of(context).dividerColor.withValues(alpha: 0.3),
                      strokeWidth: 0.5,
                    );
                  },
                ),
                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 40,
                      getTitlesWidget: (value, meta) {
                        if (value == 0 || value == 30 || value == 50 || value == 70 || value == 100) {
                          return Text(
                            value.toInt().toString(),
                            style: TextStyle(
                              fontSize: 10,
                              color: Theme.of(context).textTheme.bodySmall?.color,
                            ),
                          );
                        }
                        return const Text('');
                      },
                    ),
                  ),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 30,
                      interval: (validData.length / 5).ceilToDouble(),
                      getTitlesWidget: (value, meta) {
                        final index = value.toInt();
                        if (index >= 0 && index < validData.length) {
                          final date = validData[index].date;
                          return Padding(
                            padding: const EdgeInsets.only(top: 8.0),
                            child: Text(
                              '${date.month}/${date.day}',
                              style: TextStyle(
                                fontSize: 10,
                                color: Theme.of(context).textTheme.bodySmall?.color,
                              ),
                            ),
                          );
                        }
                        return const Text('');
                      },
                    ),
                  ),
                ),
                borderData: FlBorderData(show: true),
                minY: 0,
                maxY: 100,
                lineTouchData: LineTouchData(
                  touchCallback: (event, response) {
                    if (event is FlTapUpEvent || event is FlLongPressEnd) {
                      setState(() => _touchedIndex = null);
                    } else if (response?.lineBarSpots != null && response!.lineBarSpots!.isNotEmpty) {
                      setState(() => _touchedIndex = response.lineBarSpots!.first.x.toInt());
                    }
                  },
                  touchTooltipData: LineTouchTooltipData(
                    getTooltipItems: (touchedSpots) =>
                        touchedSpots.map((_) => null).toList(),
                  ),
                ),
                lineBarsData: [
                  if (_showRSI)
                    LineChartBarData(
                      spots: validData.asMap().entries.map((e) {
                        return FlSpot(e.key.toDouble(), e.value.value!);
                      }).toList(),
                      isCurved: true,
                      color: Colors.purple,
                      barWidth: 2,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        color: Colors.purple.withValues(alpha: 0.1),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDataPanel(BuildContext context, IndicatorDataPoint data) {
    return Container(
      padding: const EdgeInsets.all(8),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Text(
            '${data.date.year}/${data.date.month}/${data.date.day}',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          ),
          RichText(
            text: TextSpan(
              style: DefaultTextStyle.of(context).style,
              children: [
                const TextSpan(text: 'RSI: ', style: TextStyle(fontSize: 12)),
                TextSpan(
                  text: data.value?.toStringAsFixed(2) ?? '-',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: _getRSIColor(data.value),
                  ),
                ),
              ],
            ),
          ),
          _buildRSISignal(data.value),
        ],
      ),
    );
  }

  Widget _buildRSISignal(double? value) {
    String signal;
    Color color;
    if (value == null) {
      signal = '-';
      color = Colors.grey;
    } else if (value >= 70) {
      signal = '超買';
      color = Colors.red;
    } else if (value <= 30) {
      signal = '超賣';
      color = Colors.green;
    } else {
      signal = '中性';
      color = Colors.purple;
    }
    return Text(
      '訊號: $signal',
      style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.bold),
    );
  }

  Widget _buildLegend(BuildContext context) {
    return Row(
      children: [
        _buildToggleableLegendItem(
          context,
          'RSI',
          Colors.purple,
          _showRSI,
          () => setState(() => _showRSI = !_showRSI),
        ),
        const SizedBox(width: 16),
        _buildToggleableLegendItem(
          context,
          '超買 (>70)',
          Colors.red.withValues(alpha: 0.5),
          _showOverbought,
          () => setState(() => _showOverbought = !_showOverbought),
          isArea: true,
        ),
        const SizedBox(width: 16),
        _buildToggleableLegendItem(
          context,
          '超賣 (<30)',
          Colors.green.withValues(alpha: 0.5),
          _showOversold,
          () => setState(() => _showOversold = !_showOversold),
          isArea: true,
        ),
      ],
    );
  }

  Widget _buildToggleableLegendItem(
    BuildContext context,
    String label,
    Color color,
    bool isVisible,
    VoidCallback onTap, {
    bool isArea = false,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: isVisible ? 1.0 : 0.4,
        child: Row(
          children: [
            Container(
              width: 12,
              height: isArea ? 12 : 3,
              decoration: BoxDecoration(
                color: color,
                borderRadius: isArea ? BorderRadius.circular(2) : null,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                decoration: isVisible ? null : TextDecoration.lineThrough,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getRSIColor(double? value) {
    if (value == null) return Colors.grey;
    if (value >= 70) return Colors.red;
    if (value <= 30) return Colors.green;
    return Colors.purple;
  }
}
