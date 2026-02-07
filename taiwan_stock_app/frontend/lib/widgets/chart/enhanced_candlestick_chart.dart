import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../models/stock_history.dart';
import '../../models/chart_settings.dart';
import '../../models/indicator_data.dart';

/// 增強版 K 線圖表
/// 支援指標疊加、形態標記、繪圖工具
class EnhancedCandlestickChart extends StatefulWidget {
  final List<StockHistory> data;
  final ChartSettings settings;
  final BollingerDataPoint? bollingerData;
  final List<PatternMarker> patterns;
  final ValueChanged<ChartSettings>? onSettingsChanged;
  final ValueChanged<int>? onCandleTap;

  const EnhancedCandlestickChart({
    super.key,
    required this.data,
    required this.settings,
    this.bollingerData,
    this.patterns = const [],
    this.onSettingsChanged,
    this.onCandleTap,
  });

  @override
  State<EnhancedCandlestickChart> createState() => _EnhancedCandlestickChartState();
}

class _EnhancedCandlestickChartState extends State<EnhancedCandlestickChart> {
  double _visibleDataRange = 1.0;
  double _scrollOffset = 0.0;
  int? _touchedIndex;
  DrawingToolType? _activeDrawingTool;
  List<Offset> _currentDrawingPoints = [];

  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Center(child: Text('無 K 線數據'));
    }

    final totalPoints = widget.data.length;
    final visiblePoints = (totalPoints * _visibleDataRange).ceil().clamp(10, totalPoints);
    final maxOffset = totalPoints - visiblePoints;
    final startIndex = (_scrollOffset * maxOffset).round().clamp(0, maxOffset);
    final endIndex = (startIndex + visiblePoints).clamp(0, totalPoints);
    final visibleData = widget.data.sublist(startIndex, endIndex);

    return Column(
      children: [
        // 工具欄
        _buildToolbar(context),
        // 指標圖例
        _buildIndicatorLegend(context),
        // K線圖表
        Expanded(
          flex: 3,
          child: GestureDetector(
            onScaleUpdate: widget.settings.enableZoom ? _handleScaleUpdate : null,
            onHorizontalDragUpdate: widget.settings.enableZoom ? _handleHorizontalDrag : null,
            onTapUp: _activeDrawingTool != null ? _handleDrawingTap : null,
            child: Stack(
              children: [
                _buildCandlestickChart(context, visibleData, startIndex),
                // 十字線資訊
                if (_touchedIndex != null && widget.settings.enableCrosshair)
                  _buildCrosshairOverlay(context, visibleData, startIndex),
                // 形態標記
                if (widget.settings.showPatterns && widget.patterns.isNotEmpty)
                  _buildPatternMarkers(context, visibleData, startIndex),
                // 繪圖層
                if (widget.settings.drawings.isNotEmpty)
                  _buildDrawingsOverlay(context),
                // 正在繪製的對象
                if (_activeDrawingTool != null && _currentDrawingPoints.isNotEmpty)
                  _buildActiveDrawing(context),
              ],
            ),
          ),
        ),
        // 成交量圖表
        if (widget.settings.showVolume) ...[
          const SizedBox(height: 8),
          Expanded(
            flex: 1,
            child: _buildVolumeChart(context, visibleData),
          ),
        ],
        // 縮放控制
        if (widget.settings.enableZoom) _buildZoomControls(context),
      ],
    );
  }

  Widget _buildToolbar(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isDark ? Colors.grey.shade900 : Colors.grey.shade100,
        border: Border(
          bottom: BorderSide(color: Theme.of(context).dividerColor),
        ),
      ),
      child: Row(
        children: [
          // 時間週期選擇
          _buildPeriodSelector(context),
          const Spacer(),
          // 繪圖工具
          _buildDrawingTools(context),
          const SizedBox(width: 8),
          // 設置按鈕
          IconButton(
            icon: const Icon(Icons.settings, size: 20),
            onPressed: () => _showSettingsDialog(context),
            tooltip: '圖表設置',
          ),
        ],
      ),
    );
  }

  Widget _buildPeriodSelector(BuildContext context) {
    return SegmentedButton<ChartPeriod>(
      segments: ChartPeriod.values.map((p) => ButtonSegment(
        value: p,
        label: Text(p.label, style: const TextStyle(fontSize: 12)),
      )).toList(),
      selected: {widget.settings.period},
      onSelectionChanged: (selected) {
        if (selected.isNotEmpty) {
          widget.onSettingsChanged?.call(
            widget.settings.copyWith(period: selected.first),
          );
        }
      },
      style: ButtonStyle(
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        visualDensity: VisualDensity.compact,
      ),
    );
  }

  Widget _buildDrawingTools(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _buildDrawingToolButton(
          context,
          DrawingToolType.trendLine,
          Icons.show_chart,
          '趨勢線',
        ),
        _buildDrawingToolButton(
          context,
          DrawingToolType.horizontalLine,
          Icons.horizontal_rule,
          '水平線',
        ),
        if (_activeDrawingTool != null)
          IconButton(
            icon: const Icon(Icons.close, size: 18, color: Colors.red),
            onPressed: () {
              setState(() {
                _activeDrawingTool = null;
                _currentDrawingPoints.clear();
              });
            },
            tooltip: '取消繪製',
          ),
      ],
    );
  }

  Widget _buildDrawingToolButton(
    BuildContext context,
    DrawingToolType type,
    IconData icon,
    String tooltip,
  ) {
    final isActive = _activeDrawingTool == type;
    return IconButton(
      icon: Icon(
        icon,
        size: 18,
        color: isActive ? Theme.of(context).primaryColor : null,
      ),
      onPressed: () {
        setState(() {
          _activeDrawingTool = isActive ? null : type;
          _currentDrawingPoints.clear();
        });
      },
      tooltip: tooltip,
    );
  }

  Widget _buildIndicatorLegend(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      color: isDark ? Colors.grey.shade900 : Colors.grey.shade100,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            // MA 均線
            ...widget.settings.indicators.entries
                .where((e) => e.key.name.startsWith('ma'))
                .map((e) => _buildLegendItem(
                      e.value.name,
                      e.value.color,
                      e.value.isEnabled,
                      () => _toggleIndicator(e.key),
                    )),
            const SizedBox(width: 8),
            // 布林通道
            _buildLegendItem(
              '布林',
              Colors.cyan,
              widget.settings.isIndicatorEnabled(ChartIndicatorType.bollinger),
              () => _toggleIndicator(ChartIndicatorType.bollinger),
            ),
            const SizedBox(width: 8),
            // 形態識別
            _buildLegendItem(
              '形態',
              Colors.amber,
              widget.settings.showPatterns,
              () {
                widget.onSettingsChanged?.call(
                  widget.settings.copyWith(showPatterns: !widget.settings.showPatterns),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(
    String label,
    Color color,
    bool isVisible,
    VoidCallback onTap,
  ) {
    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: isVisible ? 1.0 : 0.4,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          margin: const EdgeInsets.only(right: 4),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: color.withOpacity(0.5)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 16,
                height: 2,
                color: color,
              ),
              const SizedBox(width: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                  decoration: isVisible ? null : TextDecoration.lineThrough,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _toggleIndicator(ChartIndicatorType type) {
    widget.onSettingsChanged?.call(widget.settings.toggleIndicator(type));
  }

  void _handleScaleUpdate(ScaleUpdateDetails details) {
    setState(() {
      if (details.scale != 1.0) {
        _visibleDataRange = (_visibleDataRange / details.scale).clamp(0.1, 1.0);
      }
    });
  }

  void _handleHorizontalDrag(DragUpdateDetails details) {
    setState(() {
      final delta = details.primaryDelta ?? 0;
      _scrollOffset = (_scrollOffset - delta / 200).clamp(0.0, 1.0);
    });
  }

  void _handleDrawingTap(TapUpDetails details) {
    setState(() {
      _currentDrawingPoints.add(details.localPosition);

      // 檢查是否完成繪製
      if (_activeDrawingTool == DrawingToolType.horizontalLine ||
          _activeDrawingTool == DrawingToolType.verticalLine) {
        // 單點完成
        _completeDrawing();
      } else if (_currentDrawingPoints.length >= 2) {
        // 兩點完成（趨勢線等）
        _completeDrawing();
      }
    });
  }

  void _completeDrawing() {
    if (_activeDrawingTool == null || _currentDrawingPoints.isEmpty) return;

    final newDrawing = DrawingObject(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: _activeDrawingTool!,
      points: List.from(_currentDrawingPoints),
      color: Colors.blue,
    );

    final newDrawings = [...widget.settings.drawings, newDrawing];
    widget.onSettingsChanged?.call(
      widget.settings.copyWith(drawings: newDrawings),
    );

    setState(() {
      _activeDrawingTool = null;
      _currentDrawingPoints.clear();
    });
  }

  Widget _buildCandlestickChart(
    BuildContext context,
    List<StockHistory> visibleData,
    int startIndex,
  ) {
    final minPrice = visibleData.map((e) => e.low).reduce((a, b) => a < b ? a : b);
    final maxPrice = visibleData.map((e) => e.high).reduce((a, b) => a > b ? a : b);
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
                color: Theme.of(context).dividerColor.withOpacity(0.3),
                strokeWidth: 1,
              );
            },
          ),
          titlesData: _buildTitlesData(context, visibleData),
          borderData: FlBorderData(
            show: true,
            border: Border.all(color: Theme.of(context).dividerColor.withOpacity(0.3)),
          ),
          lineTouchData: LineTouchData(
            enabled: widget.settings.enableCrosshair,
            touchCallback: (event, response) {
              if (event is FlTapUpEvent || event is FlLongPressEnd) {
                setState(() => _touchedIndex = null);
              } else if (response?.lineBarSpots != null &&
                  response!.lineBarSpots!.isNotEmpty) {
                final index = response.lineBarSpots!.first.x.toInt();
                setState(() => _touchedIndex = index);
                widget.onCandleTap?.call(startIndex + index);
              }
            },
            touchTooltipData: LineTouchTooltipData(
              getTooltipItems: (touchedSpots) => touchedSpots.map((_) => null).toList(),
            ),
          ),
          lineBarsData: [
            // K 線
            ..._buildCandlesticks(visibleData),
            // 均線
            if (widget.settings.isIndicatorEnabled(ChartIndicatorType.ma5))
              _buildMovingAverage(visibleData, 5, Colors.blue),
            if (widget.settings.isIndicatorEnabled(ChartIndicatorType.ma10))
              _buildMovingAverage(visibleData, 10, Colors.orange),
            if (widget.settings.isIndicatorEnabled(ChartIndicatorType.ma20))
              _buildMovingAverage(visibleData, 20, Colors.purple),
            if (widget.settings.isIndicatorEnabled(ChartIndicatorType.ma60))
              _buildMovingAverage(visibleData, 60, Colors.teal),
            // 布林通道
            if (widget.settings.isIndicatorEnabled(ChartIndicatorType.bollinger))
              ..._buildBollingerBands(visibleData),
          ],
        ),
      ),
    );
  }

  FlTitlesData _buildTitlesData(BuildContext context, List<StockHistory> visibleData) {
    return FlTitlesData(
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
      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
    );
  }

  List<LineChartBarData> _buildCandlesticks(List<StockHistory> data) {
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

      // 實體
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

  LineChartBarData _buildMovingAverage(
    List<StockHistory> data,
    int period,
    Color color,
  ) {
    List<FlSpot> spots = [];

    for (int i = period - 1; i < data.length; i++) {
      double sum = 0;
      for (int j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      spots.add(FlSpot(i.toDouble(), sum / period));
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

  List<LineChartBarData> _buildBollingerBands(List<StockHistory> data) {
    const period = 20;
    const stdDev = 2.0;

    if (data.length < period) return [];

    List<FlSpot> upperSpots = [];
    List<FlSpot> middleSpots = [];
    List<FlSpot> lowerSpots = [];

    for (int i = period - 1; i < data.length; i++) {
      double sum = 0;
      for (int j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      final ma = sum / period;

      double sumSquares = 0;
      for (int j = 0; j < period; j++) {
        sumSquares += (data[i - j].close - ma) * (data[i - j].close - ma);
      }
      final std = (sumSquares / period).abs();
      final stdDeviation = std > 0 ? std * 0.5 : 0; // sqrt approximation

      upperSpots.add(FlSpot(i.toDouble(), ma + stdDev * stdDeviation));
      middleSpots.add(FlSpot(i.toDouble(), ma));
      lowerSpots.add(FlSpot(i.toDouble(), ma - stdDev * stdDeviation));
    }

    return [
      // 上軌
      LineChartBarData(
        spots: upperSpots,
        isCurved: true,
        color: Colors.cyan.withOpacity(0.7),
        barWidth: 1,
        dotData: const FlDotData(show: false),
      ),
      // 中軌
      LineChartBarData(
        spots: middleSpots,
        isCurved: true,
        color: Colors.cyan,
        barWidth: 1.5,
        dotData: const FlDotData(show: false),
      ),
      // 下軌
      LineChartBarData(
        spots: lowerSpots,
        isCurved: true,
        color: Colors.cyan.withOpacity(0.7),
        barWidth: 1,
        dotData: const FlDotData(show: false),
      ),
    ];
  }

  Widget _buildCrosshairOverlay(
    BuildContext context,
    List<StockHistory> visibleData,
    int startIndex,
  ) {
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
          color: Theme.of(context).cardColor.withOpacity(0.95),
          borderRadius: BorderRadius.circular(8),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
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

  Widget _buildPatternMarkers(
    BuildContext context,
    List<StockHistory> visibleData,
    int startIndex,
  ) {
    return CustomPaint(
      painter: PatternMarkerPainter(
        patterns: widget.patterns,
        visibleData: visibleData,
        startIndex: startIndex,
        textStyle: TextStyle(
          fontSize: 10,
          color: Theme.of(context).textTheme.bodySmall?.color,
        ),
      ),
      size: Size.infinite,
    );
  }

  Widget _buildDrawingsOverlay(BuildContext context) {
    return CustomPaint(
      painter: DrawingsPainter(drawings: widget.settings.drawings),
      size: Size.infinite,
    );
  }

  Widget _buildActiveDrawing(BuildContext context) {
    return CustomPaint(
      painter: ActiveDrawingPainter(
        points: _currentDrawingPoints,
        toolType: _activeDrawingTool!,
      ),
      size: Size.infinite,
    );
  }

  Widget _buildVolumeChart(BuildContext context, List<StockHistory> visibleData) {
    final maxVolume = visibleData.map((e) => e.volume).reduce((a, b) => a > b ? a : b);

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
                color: Theme.of(context).dividerColor.withOpacity(0.3),
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
            bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),
          borderData: FlBorderData(
            show: true,
            border: Border.all(color: Theme.of(context).dividerColor.withOpacity(0.3)),
          ),
          barGroups: visibleData.asMap().entries.map((entry) {
            final candle = entry.value;
            final isRising = candle.close >= candle.open;

            return BarChartGroupData(
              x: entry.key,
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

  void _showSettingsDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => _ChartSettingsSheet(
        settings: widget.settings,
        onSettingsChanged: widget.onSettingsChanged,
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

/// 形態標記繪製器
class PatternMarkerPainter extends CustomPainter {
  final List<PatternMarker> patterns;
  final List<StockHistory> visibleData;
  final int startIndex;
  final TextStyle textStyle;

  PatternMarkerPainter({
    required this.patterns,
    required this.visibleData,
    required this.startIndex,
    required this.textStyle,
  });

  @override
  void paint(Canvas canvas, Size size) {
    for (final pattern in patterns) {
      // 計算可見範圍內的形態
      final relativeStart = pattern.startIndex - startIndex;
      final relativeEnd = pattern.endIndex - startIndex;

      if (relativeEnd < 0 || relativeStart >= visibleData.length) continue;

      final paint = Paint()
        ..color = pattern.markerColor.withOpacity(0.3)
        ..style = PaintingStyle.fill;

      // 繪製形態區域背景
      final startX = (relativeStart.clamp(0, visibleData.length - 1)) / visibleData.length * size.width;
      final endX = (relativeEnd.clamp(0, visibleData.length - 1)) / visibleData.length * size.width;

      canvas.drawRect(
        Rect.fromLTRB(startX, 0, endX, size.height),
        paint,
      );

      // 繪製形態標籤
      final textPainter = TextPainter(
        text: TextSpan(
          text: '${pattern.typeName} ${(pattern.confidence).toStringAsFixed(0)}%',
          style: textStyle.copyWith(
            color: pattern.markerColor,
            fontWeight: FontWeight.bold,
          ),
        ),
        textDirection: ui.TextDirection.ltr,
      )..layout();

      textPainter.paint(canvas, Offset(startX + 4, 4));
    }
  }

  @override
  bool shouldRepaint(covariant PatternMarkerPainter oldDelegate) {
    return patterns != oldDelegate.patterns ||
        visibleData != oldDelegate.visibleData;
  }
}

/// 繪圖對象繪製器
class DrawingsPainter extends CustomPainter {
  final List<DrawingObject> drawings;

  DrawingsPainter({required this.drawings});

  @override
  void paint(Canvas canvas, Size size) {
    for (final drawing in drawings) {
      final paint = Paint()
        ..color = drawing.color
        ..strokeWidth = drawing.strokeWidth
        ..style = PaintingStyle.stroke;

      switch (drawing.type) {
        case DrawingToolType.trendLine:
          if (drawing.points.length >= 2) {
            canvas.drawLine(drawing.points[0], drawing.points[1], paint);
          }
          break;
        case DrawingToolType.horizontalLine:
          if (drawing.points.isNotEmpty) {
            canvas.drawLine(
              Offset(0, drawing.points[0].dy),
              Offset(size.width, drawing.points[0].dy),
              paint,
            );
          }
          break;
        case DrawingToolType.verticalLine:
          if (drawing.points.isNotEmpty) {
            canvas.drawLine(
              Offset(drawing.points[0].dx, 0),
              Offset(drawing.points[0].dx, size.height),
              paint,
            );
          }
          break;
        default:
          break;
      }
    }
  }

  @override
  bool shouldRepaint(covariant DrawingsPainter oldDelegate) {
    return drawings != oldDelegate.drawings;
  }
}

/// 正在繪製的對象繪製器
class ActiveDrawingPainter extends CustomPainter {
  final List<Offset> points;
  final DrawingToolType toolType;

  ActiveDrawingPainter({
    required this.points,
    required this.toolType,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (points.isEmpty) return;

    final paint = Paint()
      ..color = Colors.blue.withOpacity(0.5)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    // 繪製已選擇的點
    for (final point in points) {
      canvas.drawCircle(point, 4, paint..style = PaintingStyle.fill);
    }

    // 繪製預覽線
    if (toolType == DrawingToolType.horizontalLine && points.isNotEmpty) {
      canvas.drawLine(
        Offset(0, points[0].dy),
        Offset(size.width, points[0].dy),
        paint..style = PaintingStyle.stroke,
      );
    }
  }

  @override
  bool shouldRepaint(covariant ActiveDrawingPainter oldDelegate) {
    return points != oldDelegate.points || toolType != oldDelegate.toolType;
  }
}

/// 圖表設置面板
class _ChartSettingsSheet extends StatelessWidget {
  final ChartSettings settings;
  final ValueChanged<ChartSettings>? onSettingsChanged;

  const _ChartSettingsSheet({
    required this.settings,
    this.onSettingsChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                '圖表設置',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const Divider(),
          // 指標開關
          const Text('技術指標', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: settings.indicators.entries.map((e) {
              return FilterChip(
                label: Text(e.value.name),
                selected: e.value.isEnabled,
                onSelected: (_) {
                  onSettingsChanged?.call(settings.toggleIndicator(e.key));
                },
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          // 顯示選項
          const Text('顯示選項', style: TextStyle(fontWeight: FontWeight.w500)),
          SwitchListTile(
            title: const Text('顯示成交量'),
            value: settings.showVolume,
            onChanged: (value) {
              onSettingsChanged?.call(settings.copyWith(showVolume: value));
            },
          ),
          SwitchListTile(
            title: const Text('顯示形態標記'),
            value: settings.showPatterns,
            onChanged: (value) {
              onSettingsChanged?.call(settings.copyWith(showPatterns: value));
            },
          ),
          SwitchListTile(
            title: const Text('啟用十字線'),
            value: settings.enableCrosshair,
            onChanged: (value) {
              onSettingsChanged?.call(settings.copyWith(enableCrosshair: value));
            },
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
