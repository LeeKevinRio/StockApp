import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../models/indicator_data.dart';

class BollingerChart extends StatefulWidget {
  final List<BollingerDataPoint> data;

  const BollingerChart({super.key, required this.data});

  @override
  State<BollingerChart> createState() => _BollingerChartState();
}

class _BollingerChartState extends State<BollingerChart> {
  bool _showUpper = true;
  bool _showMiddle = true;
  bool _showLower = true;
  bool _showClose = true;
  int? _touchedIndex;

  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Center(child: Text('無數據'));
    }

    final validData = widget.data.where((d) => d.upper != null && d.middle != null && d.lower != null).toList();
    if (validData.isEmpty) {
      return const Center(child: Text('無有效數據'));
    }

    // 計算Y軸範圍
    double minY = double.infinity;
    double maxY = double.negativeInfinity;
    for (var d in validData) {
      if (d.lower != null) minY = minY < d.lower! ? minY : d.lower!;
      if (d.upper != null) maxY = maxY > d.upper! ? maxY : d.upper!;
      if (d.close != null) {
        minY = minY < d.close! ? minY : d.close!;
        maxY = maxY > d.close! ? maxY : d.close!;
      }
    }
    final range = maxY - minY;
    minY -= range * 0.05;
    maxY += range * 0.05;

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                '布林通道 (20, 2)',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '上軌: ${validData.last.upper?.toStringAsFixed(2) ?? "-"}',
                    style: const TextStyle(fontSize: 11, color: Colors.red),
                  ),
                  Text(
                    '下軌: ${validData.last.lower?.toStringAsFixed(2) ?? "-"}',
                    style: const TextStyle(fontSize: 11, color: Colors.green),
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
                    horizontalInterval: range / 5,
                    getDrawingHorizontalLine: (value) {
                      return FlLine(color: Colors.grey.shade200, strokeWidth: 0.5);
                    },
                  ),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 50,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toStringAsFixed(1),
                            style: const TextStyle(fontSize: 10),
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
                  minY: minY,
                  maxY: maxY,
                  lineBarsData: _buildLineBarsData(validData),
                  betweenBarsData: _showUpper && _showLower
                      ? [
                          BetweenBarsData(
                            fromIndex: 0,
                            toIndex: _showMiddle ? 2 : 1,
                            color: Colors.blue.withAlpha(30),
                          ),
                        ]
                      : [],
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
          _buildBandwidthHint(validData.last),
        ],
      ),
    );
  }

  List<LineChartBarData> _buildLineBarsData(List<BollingerDataPoint> validData) {
    final List<LineChartBarData> bars = [];

    if (_showUpper) {
      bars.add(LineChartBarData(
        spots: validData.asMap().entries.map((e) {
          return FlSpot(e.key.toDouble(), e.value.upper ?? 0);
        }).toList(),
        isCurved: true,
        color: Colors.red.shade300,
        barWidth: 1,
        dotData: const FlDotData(show: false),
      ));
    }

    if (_showMiddle) {
      bars.add(LineChartBarData(
        spots: validData.asMap().entries.map((e) {
          return FlSpot(e.key.toDouble(), e.value.middle ?? 0);
        }).toList(),
        isCurved: true,
        color: Colors.blue,
        barWidth: 1.5,
        dotData: const FlDotData(show: false),
      ));
    }

    if (_showLower) {
      bars.add(LineChartBarData(
        spots: validData.asMap().entries.map((e) {
          return FlSpot(e.key.toDouble(), e.value.lower ?? 0);
        }).toList(),
        isCurved: true,
        color: Colors.green.shade300,
        barWidth: 1,
        dotData: const FlDotData(show: false),
      ));
    }

    if (_showClose) {
      bars.add(LineChartBarData(
        spots: validData.asMap().entries.map((e) {
          return FlSpot(e.key.toDouble(), e.value.close ?? 0);
        }).toList(),
        isCurved: true,
        color: Colors.black,
        barWidth: 2,
        dotData: const FlDotData(show: false),
      ));
    }

    return bars;
  }

  Widget _buildDataPanel(List<BollingerDataPoint> validData) {
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
            '上軌: ${d.upper?.toStringAsFixed(2) ?? "-"}',
            style: TextStyle(fontSize: 11, color: Colors.red.shade300),
          ),
          Text(
            '中軌: ${d.middle?.toStringAsFixed(2) ?? "-"}',
            style: const TextStyle(fontSize: 11, color: Colors.blue),
          ),
          Text(
            '下軌: ${d.lower?.toStringAsFixed(2) ?? "-"}',
            style: TextStyle(fontSize: 11, color: Colors.green.shade300),
          ),
          Text(
            '收盤: ${d.close?.toStringAsFixed(2) ?? "-"}',
            style: const TextStyle(fontSize: 11, color: Colors.black),
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
        _buildLegendItem('上軌', Colors.red.shade300, _showUpper, (v) => setState(() => _showUpper = v)),
        _buildLegendItem('中軌', Colors.blue, _showMiddle, (v) => setState(() => _showMiddle = v)),
        _buildLegendItem('下軌', Colors.green.shade300, _showLower, (v) => setState(() => _showLower = v)),
        _buildLegendItem('收盤', Colors.black, _showClose, (v) => setState(() => _showClose = v)),
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

  Widget _buildBandwidthHint(BollingerDataPoint lastPoint) {
    if (lastPoint.upper == null || lastPoint.lower == null || lastPoint.middle == null) {
      return const SizedBox.shrink();
    }

    final bandwidth = ((lastPoint.upper! - lastPoint.lower!) / lastPoint.middle!) * 100;
    String signal = '';
    Color signalColor = Colors.grey;

    if (bandwidth < 10) {
      signal = '通道收窄，可能即將突破';
      signalColor = Colors.orange;
    } else if (bandwidth > 30) {
      signal = '通道擴張，波動性增加';
      signalColor = Colors.purple;
    } else if (lastPoint.close != null) {
      if (lastPoint.close! >= lastPoint.upper!) {
        signal = '觸及上軌，注意回調風險';
        signalColor = Colors.red;
      } else if (lastPoint.close! <= lastPoint.lower!) {
        signal = '觸及下軌，可能出現反彈';
        signalColor = Colors.green;
      } else {
        signal = '價格在通道內運行';
        signalColor = Colors.blue;
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
          Expanded(
            child: Text(
              '$signal (帶寬: ${bandwidth.toStringAsFixed(1)}%)',
              style: TextStyle(color: signalColor, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
