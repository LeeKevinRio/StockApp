import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../models/stock_history.dart';

class CandlestickChart extends StatefulWidget {
  final List<StockHistory> data;
  final bool showVolume;
  final bool enableZoom;
  final bool enableCrosshair;

  const CandlestickChart({
    super.key,
    required this.data,
    this.showVolume = true,
    this.enableZoom = true,
    this.enableCrosshair = true,
  });

  @override
  State<CandlestickChart> createState() => _CandlestickChartState();
}

class _CandlestickChartState extends State<CandlestickChart> {
  // Zoom and pan state
  double _visibleDataRange = 1.0; // 1.0 = show all data
  double _scrollOffset = 0.0;
  int? _touchedIndex;

  // MA visibility
  bool _showMA5 = true;
  bool _showMA10 = true;
  bool _showMA20 = true;

  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Center(
        child: Text('無 K 線數據'),
      );
    }

    // Calculate visible range
    final totalPoints = widget.data.length;
    final visiblePoints = (totalPoints * _visibleDataRange).ceil().clamp(10, totalPoints);
    final maxOffset = totalPoints - visiblePoints;
    final startIndex = (_scrollOffset * maxOffset).round().clamp(0, maxOffset);
    final endIndex = (startIndex + visiblePoints).clamp(0, totalPoints);

    final visibleData = widget.data.sublist(startIndex, endIndex);

    return Column(
      children: [
        // MA Legend (toggleable)
        _buildLegend(context),
        // K-line chart
        Expanded(
          flex: 3,
          child: GestureDetector(
            onScaleUpdate: widget.enableZoom ? _handleScaleUpdate : null,
            onHorizontalDragUpdate: widget.enableZoom ? _handleHorizontalDrag : null,
            child: Stack(
              children: [
                _buildCandlestickChart(context, visibleData, startIndex),
                if (_touchedIndex != null && widget.enableCrosshair)
                  _buildCrosshairOverlay(context, visibleData, startIndex),
              ],
            ),
          ),
        ),
        if (widget.showVolume) ...[
          const SizedBox(height: 8),
          // Volume chart
          Expanded(
            flex: 1,
            child: _buildVolumeChart(context, visibleData),
          ),
        ],
        // Zoom controls
        if (widget.enableZoom) _buildZoomControls(context),
      ],
    );
  }

  Widget _buildLegend(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: Theme.of(context).brightness == Brightness.dark
          ? Colors.grey.shade900
          : Colors.grey.shade100,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildLegendItem('MA5', Colors.blue, _showMA5, () {
            setState(() => _showMA5 = !_showMA5);
          }),
          const SizedBox(width: 16),
          _buildLegendItem('MA10', Colors.orange, _showMA10, () {
            setState(() => _showMA10 = !_showMA10);
          }),
          const SizedBox(width: 16),
          _buildLegendItem('MA20', Colors.purple, _showMA20, () {
            setState(() => _showMA20 = !_showMA20);
          }),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color, bool isVisible, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: isVisible ? 1.0 : 0.4,
        child: Row(
          children: [
            Container(
              width: 24,
              height: 2,
              color: color,
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                decoration: isVisible ? null : TextDecoration.lineThrough,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handleScaleUpdate(ScaleUpdateDetails details) {
    setState(() {
      // Pinch to zoom
      if (details.scale != 1.0) {
        _visibleDataRange = (_visibleDataRange / details.scale).clamp(0.1, 1.0);
      }
    });
  }

  void _handleHorizontalDrag(DragUpdateDetails details) {
    setState(() {
      // Drag to scroll
      final delta = details.primaryDelta ?? 0;
      _scrollOffset = (_scrollOffset - delta / 200).clamp(0.0, 1.0);
    });
  }

  Widget _buildZoomControls(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: const Icon(Icons.zoom_in, size: 20),
            onPressed: () {
              setState(() {
                _visibleDataRange = (_visibleDataRange - 0.1).clamp(0.1, 1.0);
              });
            },
            tooltip: '放大',
          ),
          IconButton(
            icon: const Icon(Icons.zoom_out, size: 20),
            onPressed: () {
              setState(() {
                _visibleDataRange = (_visibleDataRange + 0.1).clamp(0.1, 1.0);
              });
            },
            tooltip: '縮小',
          ),
          IconButton(
            icon: const Icon(Icons.fit_screen, size: 20),
            onPressed: () {
              setState(() {
                _visibleDataRange = 1.0;
                _scrollOffset = 0.0;
              });
            },
            tooltip: '重置',
          ),
          const Spacer(),
          Text(
            '顯示 ${(_visibleDataRange * 100).toStringAsFixed(0)}%',
            style: TextStyle(
              fontSize: 12,
              color: Theme.of(context).textTheme.bodySmall?.color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCandlestickChart(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    final minPrice = visibleData
        .map((e) => e.low)
        .reduce((a, b) => a < b ? a : b);
    final maxPrice = visibleData
        .map((e) => e.high)
        .reduce((a, b) => a > b ? a : b);
    final priceRange = maxPrice - minPrice;

    return Padding(
      padding: const EdgeInsets.only(right: 16, left: 8, top: 16, bottom: 8),
      child: LineChart(
        LineChartData(
          minX: 0,
          maxX: visibleData.length.toDouble() - 1,
          minY: minPrice - priceRange * 0.1,
          maxY: maxPrice + priceRange * 0.1,
          gridData: FlGridData(
            show: true,
            drawVerticalLine: false,
            horizontalInterval: priceRange / 5,
            getDrawingHorizontalLine: (value) {
              return FlLine(
                color: Theme.of(context).dividerColor.withValues(alpha: 0.3),
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
                    style: TextStyle(
                      fontSize: 10,
                      color: Theme.of(context).textTheme.bodySmall?.color,
                    ),
                  );
                },
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                interval: (visibleData.length / 5).ceilToDouble(),
                getTitlesWidget: (value, meta) {
                  if (value.toInt() >= visibleData.length || value < 0) {
                    return const SizedBox();
                  }
                  final date = visibleData[value.toInt()].date;
                  return Text(
                    '${date.month}/${date.day}',
                    style: TextStyle(
                      fontSize: 10,
                      color: Theme.of(context).textTheme.bodySmall?.color,
                    ),
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
            border: Border.all(color: Theme.of(context).dividerColor.withValues(alpha: 0.3)),
          ),
          lineTouchData: LineTouchData(
            enabled: widget.enableCrosshair,
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
            // Candlesticks
            ..._buildCandlesticks(visibleData),
            // Moving averages
            if (_showMA5)
              _buildMovingAverage(visibleData, 5, Colors.blue),
            if (_showMA10)
              _buildMovingAverage(visibleData, 10, Colors.orange),
            if (_showMA20)
              _buildMovingAverage(visibleData, 20, Colors.purple),
          ],
        ),
      ),
    );
  }

  Widget _buildCrosshairOverlay(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    if (_touchedIndex == null || _touchedIndex! >= visibleData.length) {
      return const SizedBox();
    }

    final candle = visibleData[_touchedIndex!];
    final isRising = candle.close >= candle.open;
    final priceColor = isRising ? Colors.red : Colors.green;

    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: Container(
        padding: const EdgeInsets.all(8),
        margin: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor.withValues(alpha: 0.95),
          borderRadius: BorderRadius.circular(8),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 4,
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            Text(
              DateFormat('yyyy/MM/dd').format(candle.date),
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
            ),
            _buildPriceInfo('開', candle.open, priceColor),
            _buildPriceInfo('高', candle.high, priceColor),
            _buildPriceInfo('低', candle.low, priceColor),
            _buildPriceInfo('收', candle.close, priceColor),
            Text(
              '量 ${_formatVolume(candle.volume.toDouble())}',
              style: const TextStyle(fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPriceInfo(String label, double value, Color color) {
    return RichText(
      text: TextSpan(
        style: DefaultTextStyle.of(context).style.copyWith(fontSize: 11),
        children: [
          TextSpan(text: '$label '),
          TextSpan(
            text: value.toStringAsFixed(2),
            style: TextStyle(color: color, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  List<LineChartBarData> _buildCandlesticks(List<StockHistory> data) {
    List<LineChartBarData> bars = [];

    // 根據數據量動態調整 K 線寬度
    // 數據越少，K 線越粗
    final double bodyWidth = data.length <= 20 ? 12 : (data.length <= 40 ? 8 : 6);
    final double wickWidth = data.length <= 20 ? 3 : 2;

    for (int i = 0; i < data.length; i++) {
      final candle = data[i];
      final isRising = candle.close >= candle.open;
      final color = isRising ? Colors.red : Colors.green;

      // Upper shadow (影線上半部)
      bars.add(LineChartBarData(
        spots: [
          FlSpot(i.toDouble(), candle.high),
          FlSpot(i.toDouble(), candle.close > candle.open ? candle.close : candle.open),
        ],
        isCurved: false,
        color: color,
        barWidth: wickWidth,
        dotData: const FlDotData(show: false),
      ));

      // Lower shadow (影線下半部)
      bars.add(LineChartBarData(
        spots: [
          FlSpot(i.toDouble(), candle.close < candle.open ? candle.close : candle.open),
          FlSpot(i.toDouble(), candle.low),
        ],
        isCurved: false,
        color: color,
        barWidth: wickWidth,
        dotData: const FlDotData(show: false),
      ));

      // Body (實體部分)
      bars.add(LineChartBarData(
        spots: [
          FlSpot(i.toDouble(), candle.open),
          FlSpot(i.toDouble(), candle.close),
        ],
        isCurved: false,
        color: color,
        barWidth: bodyWidth,
        dotData: const FlDotData(show: false),
      ));
    }

    return bars;
  }

  LineChartBarData _buildMovingAverage(List<StockHistory> data, int period, Color color) {
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

  Widget _buildVolumeChart(BuildContext context, List<StockHistory> visibleData) {
    final maxVolume = visibleData
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
                color: Theme.of(context).dividerColor.withValues(alpha: 0.3),
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
                    style: TextStyle(
                      fontSize: 10,
                      color: Theme.of(context).textTheme.bodySmall?.color,
                    ),
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
            border: Border.all(color: Theme.of(context).dividerColor.withValues(alpha: 0.3)),
          ),
          barGroups: visibleData.asMap().entries.map((entry) {
            final index = entry.key;
            final candle = entry.value;
            final isRising = candle.close >= candle.open;
            // 根據數據量動態調整成交量柱寬度
            final double volumeBarWidth = visibleData.length <= 20 ? 10 : (visibleData.length <= 40 ? 6 : 4);

            return BarChartGroupData(
              x: index,
              barRods: [
                BarChartRodData(
                  toY: candle.volume.toDouble(),
                  color: isRising
                      ? Colors.red.withValues(alpha: 0.7)
                      : Colors.green.withValues(alpha: 0.7),
                  width: volumeBarWidth,
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
