import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../models/indicator_data.dart';

class MACDChart extends StatefulWidget {
  final List<MACDDataPoint> data;

  const MACDChart({super.key, required this.data});

  @override
  State<MACDChart> createState() => _MACDChartState();
}

class _MACDChartState extends State<MACDChart> {
  bool _showDIF = true;
  bool _showDEA = true;
  bool _showHistogram = true;
  int? _touchedIndex;

  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Center(child: Text('無數據'));
    }

    final validData = widget.data.where((d) => d.macd != null && d.signal != null).toList();
    if (validData.isEmpty) {
      return const Center(child: Text('無有效數據'));
    }

    // Calculate Y-axis range
    double minY = double.infinity;
    double maxY = double.negativeInfinity;
    for (var d in validData) {
      if (d.macd != null) {
        minY = minY < d.macd! ? minY : d.macd!;
        maxY = maxY > d.macd! ? maxY : d.macd!;
      }
      if (d.signal != null) {
        minY = minY < d.signal! ? minY : d.signal!;
        maxY = maxY > d.signal! ? maxY : d.signal!;
      }
      if (d.histogram != null) {
        minY = minY < d.histogram! ? minY : d.histogram!;
        maxY = maxY > d.histogram! ? maxY : d.histogram!;
      }
    }
    final range = maxY - minY;
    minY -= range * 0.1;
    maxY += range * 0.1;

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'MACD (12, 26, 9)',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              Text(
                'DIF: ${validData.last.macd?.toStringAsFixed(2) ?? "-"}',
                style: TextStyle(
                  fontSize: 12,
                  color: (validData.last.macd ?? 0) >= 0 ? Colors.red : Colors.green,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          _buildLegend(context),
          const SizedBox(height: 8),
          // Data panel
          if (_touchedIndex != null && _touchedIndex! < validData.length)
            _buildDataPanel(context, validData[_touchedIndex!]),
          // Histogram chart
          if (_showHistogram)
            Expanded(
              flex: 2,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: maxY,
                  minY: minY,
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: (maxY - minY) / 5,
                    getDrawingHorizontalLine: (value) {
                      if (value.abs() < 0.001) {
                        return FlLine(
                          color: Theme.of(context).dividerColor,
                          strokeWidth: 1,
                        );
                      }
                      return FlLine(
                        color: Theme.of(context).dividerColor.withOpacity(0.3),
                        strokeWidth: 0.5,
                      );
                    },
                  ),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 50,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toStringAsFixed(2),
                            style: TextStyle(
                              fontSize: 10,
                              color: Theme.of(context).textTheme.bodySmall?.color,
                            ),
                          );
                        },
                      ),
                    ),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        getTitlesWidget: (value, meta) {
                          final index = value.toInt();
                          if (index >= 0 && index < validData.length && index % (validData.length ~/ 5 + 1) == 0) {
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
                  barGroups: validData.asMap().entries.map((e) {
                    final histogram = e.value.histogram ?? 0;
                    return BarChartGroupData(
                      x: e.key,
                      barRods: [
                        BarChartRodData(
                          toY: histogram,
                          fromY: 0,
                          color: histogram >= 0 ? Colors.red : Colors.green,
                          width: 2,
                        ),
                      ],
                    );
                  }).toList(),
                  barTouchData: BarTouchData(
                    touchCallback: (event, response) {
                      if (event is FlTapUpEvent || event is FlLongPressEnd) {
                        setState(() => _touchedIndex = null);
                      } else if (response?.spot != null) {
                        setState(() => _touchedIndex = response!.spot!.touchedBarGroupIndex);
                      }
                    },
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipItem: (group, groupIndex, rod, rodIndex) => null,
                    ),
                  ),
                ),
              ),
            ),
          // DIF and DEA lines
          Expanded(
            flex: _showHistogram ? 1 : 2,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: !_showHistogram,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (value) {
                    if (value.abs() < 0.001) {
                      return FlLine(
                        color: Theme.of(context).dividerColor,
                        strokeWidth: 1,
                      );
                    }
                    return FlLine(
                      color: Theme.of(context).dividerColor.withOpacity(0.3),
                      strokeWidth: 0.5,
                    );
                  },
                ),
                titlesData: FlTitlesData(
                  show: !_showHistogram,
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: !_showHistogram,
                      reservedSize: 50,
                    ),
                  ),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: !_showHistogram),
                minY: minY,
                maxY: maxY,
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
                  if (_showDIF)
                    LineChartBarData(
                      spots: validData.asMap().entries.map((e) {
                        return FlSpot(e.key.toDouble(), e.value.macd ?? 0);
                      }).toList(),
                      isCurved: true,
                      color: Colors.blue,
                      barWidth: 1.5,
                      dotData: const FlDotData(show: false),
                    ),
                  if (_showDEA)
                    LineChartBarData(
                      spots: validData.asMap().entries.map((e) {
                        return FlSpot(e.key.toDouble(), e.value.signal ?? 0);
                      }).toList(),
                      isCurved: true,
                      color: Colors.orange,
                      barWidth: 1.5,
                      dotData: const FlDotData(show: false),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDataPanel(BuildContext context, MACDDataPoint data) {
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
            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
          ),
          _buildValueText('DIF', data.macd, Colors.blue),
          _buildValueText('DEA', data.signal, Colors.orange),
          _buildValueText(
            'MACD',
            data.histogram,
            (data.histogram ?? 0) >= 0 ? Colors.red : Colors.green,
          ),
        ],
      ),
    );
  }

  Widget _buildValueText(String label, double? value, Color color) {
    return RichText(
      text: TextSpan(
        style: DefaultTextStyle.of(context).style,
        children: [
          TextSpan(text: '$label: ', style: const TextStyle(fontSize: 11)),
          TextSpan(
            text: value?.toStringAsFixed(2) ?? '-',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegend(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 8,
      children: [
        _buildToggleableLegendItem(
          context,
          'DIF',
          Colors.blue,
          _showDIF,
          () => setState(() => _showDIF = !_showDIF),
        ),
        _buildToggleableLegendItem(
          context,
          'DEA',
          Colors.orange,
          _showDEA,
          () => setState(() => _showDEA = !_showDEA),
        ),
        _buildToggleableLegendItem(
          context,
          '柱 +',
          Colors.red,
          _showHistogram,
          () => setState(() => _showHistogram = !_showHistogram),
          isArea: true,
        ),
        _buildToggleableLegendItem(
          context,
          '柱 -',
          Colors.green,
          _showHistogram,
          () => setState(() => _showHistogram = !_showHistogram),
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
          mainAxisSize: MainAxisSize.min,
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
}
