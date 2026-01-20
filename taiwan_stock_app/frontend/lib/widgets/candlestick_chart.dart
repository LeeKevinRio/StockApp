import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/stock_history.dart';

class CandlestickChart extends StatelessWidget {
  final List<StockHistory> data;
  final bool showVolume;

  const CandlestickChart({
    super.key,
    required this.data,
    this.showVolume = true,
  });

  @override
  Widget build(BuildContext context) {
    if (data.isEmpty) {
      return const Center(
        child: Text('無 K 線數據'),
      );
    }

    return Column(
      children: [
        // K線圖
        Expanded(
          flex: 3,
          child: _buildCandlestickChart(context),
        ),
        if (showVolume) ...[
          const SizedBox(height: 8),
          // 成交量圖
          Expanded(
            flex: 1,
            child: _buildVolumeChart(context),
          ),
        ],
      ],
    );
  }

  Widget _buildCandlestickChart(BuildContext context) {
    final minPrice = data
        .map((e) => e.low)
        .reduce((a, b) => a < b ? a : b);
    final maxPrice = data
        .map((e) => e.high)
        .reduce((a, b) => a > b ? a : b);
    final priceRange = maxPrice - minPrice;

    return Padding(
      padding: const EdgeInsets.only(right: 16, left: 8, top: 16, bottom: 8),
      child: LineChart(
        LineChartData(
          minX: 0,
          maxX: data.length.toDouble() - 1,
          minY: minPrice - priceRange * 0.1,
          maxY: maxPrice + priceRange * 0.1,
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: priceRange / 5,
            getDrawingHorizontalLine: (value) {
              return FlLine(
                color: Colors.grey.withOpacity(0.2),
                strokeWidth: 1,
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
                    value.toStringAsFixed(1),
                    style: const TextStyle(fontSize: 10, color: Colors.grey),
                  );
                },
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                interval: (data.length / 5).ceilToDouble(),
                getTitlesWidget: (value, meta) {
                  if (value.toInt() >= data.length || value < 0) {
                    return const SizedBox();
                  }
                  final date = data[value.toInt()].date;
                  return Text(
                    '${date.month}/${date.day}',
                    style: const TextStyle(fontSize: 10, color: Colors.grey),
                  );
                },
              ),
            ),
            rightTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            topTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
          ),
          borderData: FlBorderData(
            show: true,
            border: Border.all(color: Colors.grey.withOpacity(0.2)),
          ),
          lineBarsData: [
            // 繪製蠟燭線
            ..._buildCandlesticks(),
            // MA5
            _buildMovingAverage(5, Colors.blue),
            // MA10
            _buildMovingAverage(10, Colors.orange),
            // MA20
            _buildMovingAverage(20, Colors.purple),
          ],
        ),
      ),
    );
  }

  List<LineChartBarData> _buildCandlesticks() {
    List<LineChartBarData> bars = [];

    for (int i = 0; i < data.length; i++) {
      final candle = data[i];
      final isRising = candle.close >= candle.open;
      final color = isRising ? Colors.red : Colors.green;

      // 上影線
      bars.add(LineChartBarData(
        spots: [
          FlSpot(i.toDouble(), candle.high),
          FlSpot(i.toDouble(), candle.close > candle.open ? candle.close : candle.open),
        ],
        isCurved: false,
        color: color,
        barWidth: 1,
        dotData: const FlDotData(show: false),
      ));

      // 下影線
      bars.add(LineChartBarData(
        spots: [
          FlSpot(i.toDouble(), candle.close < candle.open ? candle.close : candle.open),
          FlSpot(i.toDouble(), candle.low),
        ],
        isCurved: false,
        color: color,
        barWidth: 1,
        dotData: const FlDotData(show: false),
      ));

      // 實體（用粗線模擬）
      bars.add(LineChartBarData(
        spots: [
          FlSpot(i.toDouble(), candle.open),
          FlSpot(i.toDouble(), candle.close),
        ],
        isCurved: false,
        color: color,
        barWidth: 4,
        dotData: const FlDotData(show: false),
      ));
    }

    return bars;
  }

  LineChartBarData _buildMovingAverage(int period, Color color) {
    List<FlSpot> spots = [];

    for (int i = period - 1; i < data.length; i++) {
      double sum = 0;
      for (int j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      double ma = sum / period;
      spots.add(FlSpot(i.toDouble(), ma));
    }

    return LineChartBarData(
      spots: spots,
      isCurved: true,
      color: color,
      barWidth: 1.5,
      dotData: const FlDotData(show: false),
      belowBarData: BarAreaData(show: false),
    );
  }

  Widget _buildVolumeChart(BuildContext context) {
    final maxVolume = data
        .map((e) => e.volume)
        .reduce((a, b) => a > b ? a : b);

    return Padding(
      padding: const EdgeInsets.only(right: 16, left: 8, bottom: 16),
      child: BarChart(
        BarChartData(
          alignment: BarChartAlignment.spaceAround,
          maxY: maxVolume.toDouble() * 1.2,
          barTouchData: BarTouchData(enabled: false),
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: maxVolume / 3,
            getDrawingHorizontalLine: (value) {
              return FlLine(
                color: Colors.grey.withOpacity(0.2),
                strokeWidth: 1,
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
                    _formatVolume(value),
                    style: const TextStyle(fontSize: 10, color: Colors.grey),
                  );
                },
              ),
            ),
            bottomTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            rightTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            topTitles: const AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
          ),
          borderData: FlBorderData(
            show: true,
            border: Border.all(color: Colors.grey.withOpacity(0.2)),
          ),
          barGroups: data.asMap().entries.map((entry) {
            final index = entry.key;
            final candle = entry.value;
            final isRising = candle.close >= candle.open;

            return BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: candle.volume.toDouble(),
                  color: isRising
                      ? Colors.red.withOpacity(0.5)
                      : Colors.green.withOpacity(0.5),
                  width: 4,
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }

  String _formatVolume(double volume) {
    if (volume >= 100000000) {
      return '${(volume / 100000000).toStringAsFixed(0)}億';
    } else if (volume >= 10000) {
      return '${(volume / 10000).toStringAsFixed(0)}萬';
    } else {
      return volume.toStringAsFixed(0);
    }
  }
}
