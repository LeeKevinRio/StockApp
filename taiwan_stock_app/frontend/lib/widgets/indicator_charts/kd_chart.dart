import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../models/indicator_data.dart';

class KDChart extends StatefulWidget {
  final List<KDDataPoint> data;

  const KDChart({super.key, required this.data});

  @override
  State<KDChart> createState() => _KDChartState();
}

class _KDChartState extends State<KDChart> {
  bool _showK = true;
  bool _showD = true;
  bool _showOverboughtLine = true;
  bool _showOversoldLine = true;
  int? _touchedIndex;

  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Center(child: Text('無數據'));
    }

    final validData = widget.data.where((d) => d.k != null && d.d != null).toList();
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
                'KD 指標 (9)',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              Row(
                children: [
                  Text(
                    'K: ${validData.last.k?.toStringAsFixed(2) ?? "-"}',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.blue.shade700,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'D: ${validData.last.d?.toStringAsFixed(2) ?? "-"}',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.orange.shade700,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          _buildLegend(),
          const SizedBox(height: 8),
          if (_touchedIndex != null) _buildDataPanel(validData),
          const SizedBox(height: 8),
          Expanded(
            child: GestureDetector(
              onTapUp: (details) {
                setState(() {
                  _touchedIndex = null;
                });
              },
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: 20,
                    getDrawingHorizontalLine: (value) {
                      if (value == 80 && _showOverboughtLine) {
                        return FlLine(
                          color: Colors.red.withAlpha(128),
                          strokeWidth: 1,
                          dashArray: [5, 5],
                        );
                      }
                      if (value == 20 && _showOversoldLine) {
                        return FlLine(
                          color: Colors.green.withAlpha(128),
                          strokeWidth: 1,
                          dashArray: [5, 5],
                        );
                      }
                      if (value == 50) {
                        return FlLine(
                          color: Colors.grey.withAlpha(128),
                          strokeWidth: 1,
                          dashArray: [3, 3],
                        );
                      }
                      return FlLine(color: Colors.grey.shade200, strokeWidth: 0.5);
                    },
                  ),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        getTitlesWidget: (value, meta) {
                          if (value == 0 || value == 20 || value == 50 || value == 80 || value == 100) {
                            return Text(
                              value.toInt().toString(),
                              style: const TextStyle(fontSize: 10),
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
                                style: const TextStyle(fontSize: 10),
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
                  lineBarsData: _buildLineBarsData(validData),
                  lineTouchData: LineTouchData(
                    touchCallback: (event, response) {
                      if (response?.lineBarSpots != null && response!.lineBarSpots!.isNotEmpty) {
                        setState(() {
                          _touchedIndex = response.lineBarSpots!.first.x.toInt();
                        });
                      }
                    },
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipColor: (spot) => Colors.transparent,
                      getTooltipItems: (touchedSpots) =>
                          touchedSpots.map((_) => null).toList(),
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          _buildSignalHint(validData.last),
        ],
      ),
    );
  }

  List<LineChartBarData> _buildLineBarsData(List<KDDataPoint> validData) {
    final List<LineChartBarData> bars = [];

    if (_showK) {
      bars.add(LineChartBarData(
        spots: validData.asMap().entries.map((e) {
          return FlSpot(e.key.toDouble(), e.value.k ?? 0);
        }).toList(),
        isCurved: true,
        color: Colors.blue.shade700,
        barWidth: 2,
        dotData: const FlDotData(show: false),
      ));
    }

    if (_showD) {
      bars.add(LineChartBarData(
        spots: validData.asMap().entries.map((e) {
          return FlSpot(e.key.toDouble(), e.value.d ?? 0);
        }).toList(),
        isCurved: true,
        color: Colors.orange.shade700,
        barWidth: 2,
        dotData: const FlDotData(show: false),
      ));
    }

    return bars;
  }

  Widget _buildDataPanel(List<KDDataPoint> validData) {
    if (_touchedIndex == null || _touchedIndex! < 0 || _touchedIndex! >= validData.length) {
      return const SizedBox.shrink();
    }

    final d = validData[_touchedIndex!];
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          Text(
            '${d.date.month}/${d.date.day}',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          ),
          Text(
            'K: ${d.k?.toStringAsFixed(2) ?? "-"}',
            style: TextStyle(fontSize: 12, color: Colors.blue.shade700),
          ),
          Text(
            'D: ${d.d?.toStringAsFixed(2) ?? "-"}',
            style: TextStyle(fontSize: 12, color: Colors.orange.shade700),
          ),
          if (d.k != null && d.d != null)
            Text(
              d.k! > d.d! ? 'K > D (多)' : 'K < D (空)',
              style: TextStyle(
                fontSize: 12,
                color: d.k! > d.d! ? Colors.green : Colors.red,
                fontWeight: FontWeight.bold,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildLegend() {
    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: [
        _buildLegendItem('K值', Colors.blue.shade700, _showK, (v) => setState(() => _showK = v)),
        _buildLegendItem('D值', Colors.orange.shade700, _showD, (v) => setState(() => _showD = v)),
        _buildZoneLegendItem('超買區(80)', Colors.red, _showOverboughtLine, (v) => setState(() => _showOverboughtLine = v)),
        _buildZoneLegendItem('超賣區(20)', Colors.green, _showOversoldLine, (v) => setState(() => _showOversoldLine = v)),
      ],
    );
  }

  Widget _buildLegendItem(String label, Color color, bool isVisible, Function(bool) onTap) {
    return GestureDetector(
      onTap: () => onTap(!isVisible),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: isVisible ? color.withAlpha(26) : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: isVisible ? color : Colors.grey.shade400),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 3,
              color: isVisible ? color : Colors.grey.shade400,
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: isVisible ? color : Colors.grey.shade600,
                decoration: isVisible ? null : TextDecoration.lineThrough,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildZoneLegendItem(String label, Color color, bool isVisible, Function(bool) onTap) {
    return GestureDetector(
      onTap: () => onTap(!isVisible),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: isVisible ? color.withAlpha(26) : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: isVisible ? color : Colors.grey.shade400),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              color: isVisible ? color.withAlpha(51) : Colors.grey.shade300,
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: isVisible ? color : Colors.grey.shade600,
                decoration: isVisible ? null : TextDecoration.lineThrough,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSignalHint(KDDataPoint lastPoint) {
    String signal = '';
    Color signalColor = Colors.grey;

    if (lastPoint.k != null && lastPoint.d != null) {
      if (lastPoint.k! > 80 && lastPoint.d! > 80) {
        signal = '超買區域，注意回調風險';
        signalColor = Colors.red;
      } else if (lastPoint.k! < 20 && lastPoint.d! < 20) {
        signal = '超賣區域，可能出現反彈';
        signalColor = Colors.green;
      } else if (lastPoint.k! > lastPoint.d!) {
        signal = 'K > D，短期趨勢偏多';
        signalColor = Colors.blue;
      } else {
        signal = 'K < D，短期趨勢偏空';
        signalColor = Colors.orange;
      }
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: signalColor.withAlpha(26),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: signalColor.withAlpha(77)),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline, size: 16, color: signalColor),
          const SizedBox(width: 8),
          Text(
            signal,
            style: TextStyle(color: signalColor, fontSize: 12),
          ),
        ],
      ),
    );
  }
}
