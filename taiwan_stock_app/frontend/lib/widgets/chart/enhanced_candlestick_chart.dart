import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../models/stock_history.dart';
import '../../models/chart_settings.dart';
import '../../models/indicator_data.dart';
import '../../config/app_theme.dart';

/// 副圖類型
enum SubChartType { none, macd, rsi, kd }

/// MACD 計算結果
class _MACDValue {
  final double dif;
  final double dea;
  final double histogram;
  _MACDValue({required this.dif, required this.dea, required this.histogram});
}

/// 增強版 K 線圖表
/// 使用 CustomPainter 繪製 K 線（高效能），副圖仍用 fl_chart
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
  SubChartType _selectedSubChart = SubChartType.none;

  // 指標計算快取
  List<StockHistory>? _cachedData;
  List<_MACDValue>? _cachedMACD;
  List<double>? _cachedRSI;
  List<(double, double)>? _cachedKD;
  // 均線預計算快取
  List<double?>? _cachedMA5;
  List<double?>? _cachedMA10;
  List<double?>? _cachedMA20;
  List<double?>? _cachedMA60;
  // 布林通道預計算快取
  List<(double, double, double)?>? _cachedBollinger; // (upper, middle, lower)

  void _ensureIndicatorCache() {
    if (identical(_cachedData, widget.data)) return;
    _cachedData = widget.data;
    _cachedMACD = _computeMACDValues(widget.data);
    _cachedRSI = _computeRSIValues(widget.data);
    _cachedKD = _computeKDValues(widget.data);
    _cachedMA5 = _precomputeMA(widget.data, 5);
    _cachedMA10 = _precomputeMA(widget.data, 10);
    _cachedMA20 = _precomputeMA(widget.data, 20);
    _cachedMA60 = _precomputeMA(widget.data, 60);
    _cachedBollinger = _precomputeBollinger(widget.data, 20, 2.0);
  }

  List<double?> _precomputeMA(List<StockHistory> data, int period) {
    final result = List<double?>.filled(data.length, null);
    if (data.length < period) return result;
    double sum = 0;
    for (int i = 0; i < period; i++) sum += data[i].close;
    result[period - 1] = sum / period;
    for (int i = period; i < data.length; i++) {
      sum += data[i].close - data[i - period].close;
      result[i] = sum / period;
    }
    return result;
  }

  List<(double, double, double)?> _precomputeBollinger(List<StockHistory> data, int period, double multiplier) {
    final result = List<(double, double, double)?>.filled(data.length, null);
    if (data.length < period) return result;
    for (int i = period - 1; i < data.length; i++) {
      double sum = 0;
      for (int j = 0; j < period; j++) sum += data[i - j].close;
      final ma = sum / period;
      double sumSq = 0;
      for (int j = 0; j < period; j++) {
        final diff = data[i - j].close - ma;
        sumSq += diff * diff;
      }
      final stdDev = sqrt(sumSq / period);
      result[i] = (ma + multiplier * stdDev, ma, ma - multiplier * stdDev);
    }
    return result;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.data.isEmpty) {
      return const Center(child: Text('無 K 線數據'));
    }
    _ensureIndicatorCache();

    final totalPoints = widget.data.length;
    final visiblePoints = (totalPoints * _visibleDataRange).ceil().clamp(10, totalPoints);
    final maxOffset = totalPoints - visiblePoints;
    final startIndex = (_scrollOffset * maxOffset).round().clamp(0, maxOffset);
    final endIndex = (startIndex + visiblePoints).clamp(0, totalPoints);
    final visibleData = widget.data.sublist(startIndex, endIndex);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // 工具欄
        _buildToolbar(context),
        // 指標圖例
        _buildIndicatorLegend(context),
        // K線圖表（使用 CustomPainter）
        Expanded(
          flex: _selectedSubChart != SubChartType.none ? 3 : 1,
          child: MouseRegion(
            // 滑鼠移動時即時顯示十字線
            onHover: widget.settings.enableCrosshair ? (event) => _handleMouseHover(event, visibleData) : null,
            onExit: (_) { if (_touchedIndex != null) setState(() => _touchedIndex = null); },
            child: Listener(
              onPointerSignal: widget.settings.enableZoom ? _handlePointerSignal : null,
              child: GestureDetector(
                onHorizontalDragUpdate: widget.settings.enableZoom ? _handleHorizontalDrag : null,
                onTapUp: _activeDrawingTool != null ? _handleDrawingTap : null,
                behavior: HitTestBehavior.opaque,
                child: RepaintBoundary(
                  child: Stack(
                    children: [
                      // K 線主圖
                      Positioned.fill(
                        child: Padding(
                          padding: const EdgeInsets.only(right: 50, left: 8, top: 16, bottom: 24),
                          child: CustomPaint(
                            painter: _CandlestickChartPainter(
                              data: visibleData,
                              settings: widget.settings,
                              touchedIndex: _touchedIndex,
                              isDark: true,
                              maData: _PrecomputedMA(
                                ma5: _cachedMA5?.sublist(startIndex, endIndex),
                                ma10: _cachedMA10?.sublist(startIndex, endIndex),
                                ma20: _cachedMA20?.sublist(startIndex, endIndex),
                                ma60: _cachedMA60?.sublist(startIndex, endIndex),
                              ),
                              bollingerData: _cachedBollinger?.sublist(startIndex, endIndex),
                            ),
                          ),
                        ),
                      ),
                      // 右側價格軸
                      Positioned(
                        right: 0,
                        top: 16,
                        bottom: 24,
                        width: 50,
                        child: CustomPaint(
                          painter: _PriceAxisPainter(
                            data: visibleData,
                            isDark: true,
                          ),
                        ),
                      ),
                      // 底部日期軸
                      Positioned(
                        left: 8,
                        right: 50,
                        bottom: 0,
                        height: 20,
                        child: CustomPaint(
                          painter: _DateAxisPainter(
                            data: visibleData,
                            isDark: true,
                          ),
                        ),
                      ),
                      // 十字線資訊
                      if (_touchedIndex != null && widget.settings.enableCrosshair)
                        _buildCrosshairOverlay(context, visibleData, startIndex),
                      // 形態標記（用 IgnorePointer 避免攔截滑鼠事件）
                      if (widget.settings.showPatterns && widget.patterns.isNotEmpty)
                        Positioned.fill(
                          child: IgnorePointer(
                            child: Padding(
                              padding: const EdgeInsets.only(right: 50, left: 8, top: 16, bottom: 24),
                              child: _buildPatternMarkers(context, visibleData, startIndex),
                            ),
                          ),
                        ),
                      // 繪圖層
                      if (widget.settings.drawings.isNotEmpty)
                        IgnorePointer(child: _buildDrawingsOverlay(context)),
                      if (_activeDrawingTool != null && _currentDrawingPoints.isNotEmpty)
                        _buildActiveDrawing(context),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
        // 成交量圖表
        if (widget.settings.showVolume) ...[
          const SizedBox(height: 4),
          RepaintBoundary(
            child: SizedBox(
              height: 60,
              child: Padding(
                padding: const EdgeInsets.only(right: 50, left: 8),
                child: CustomPaint(
                  painter: _VolumePainter(data: visibleData),
                ),
              ),
            ),
          ),
        ],
        // 副圖選擇器
        _buildSubChartSelector(context),
        // 副圖指標
        if (_selectedSubChart != SubChartType.none)
          Expanded(
            flex: 1,
            child: RepaintBoundary(
              child: _buildSubChart(context, visibleData, startIndex),
            ),
          ),
        // 縮放控制
        if (widget.settings.enableZoom) _buildZoomControls(context),
      ],
    );
  }

  void _handleMouseHover(PointerHoverEvent event, List<StockHistory> visibleData) {
    final RenderBox? box = context.findRenderObject() as RenderBox?;
    if (box == null) return;
    final chartWidth = box.size.width - 50 - 8; // 減去右側軸和左 padding
    final localX = event.localPosition.dx - 8; // 減去左 padding
    if (localX < 0 || localX > chartWidth || visibleData.isEmpty) {
      if (_touchedIndex != null) setState(() => _touchedIndex = null);
      return;
    }
    final index = (localX / chartWidth * visibleData.length).floor().clamp(0, visibleData.length - 1);
    if (index != _touchedIndex) {
      setState(() => _touchedIndex = index);
    }
  }

  Widget _buildToolbar(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color ?? const Color(0xFF1E272E),
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
        _buildDrawingToolButton(context, DrawingToolType.trendLine, Icons.show_chart, '趨勢線'),
        _buildDrawingToolButton(context, DrawingToolType.horizontalLine, Icons.horizontal_rule, '水平線'),
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

  Widget _buildDrawingToolButton(BuildContext context, DrawingToolType type, IconData icon, String tooltip) {
    final isActive = _activeDrawingTool == type;
    return IconButton(
      icon: Icon(icon, size: 18, color: isActive ? Theme.of(context).primaryColor : null),
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
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      color: Theme.of(context).cardTheme.color ?? const Color(0xFF1E272E),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            ...widget.settings.indicators.entries
                .where((e) => e.key.name.startsWith('ma'))
                .map((e) => _buildLegendItem(
                      e.value.name, e.value.color, e.value.isEnabled, () => _toggleIndicator(e.key),
                    )),
            const SizedBox(width: 8),
            _buildLegendItem('布林', Colors.cyan, widget.settings.isIndicatorEnabled(ChartIndicatorType.bollinger),
                () => _toggleIndicator(ChartIndicatorType.bollinger)),
            const SizedBox(width: 8),
            _buildLegendItem('形態', Colors.amber, widget.settings.showPatterns, () {
              widget.onSettingsChanged?.call(
                widget.settings.copyWith(showPatterns: !widget.settings.showPatterns),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color, bool isVisible, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: isVisible ? 1.0 : 0.4,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          margin: const EdgeInsets.only(right: 4),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: color.withAlpha(128)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(width: 16, height: 2, color: color),
              const SizedBox(width: 4),
              Text(label, style: TextStyle(
                fontSize: 11, color: color, fontWeight: FontWeight.w500,
                decoration: isVisible ? null : TextDecoration.lineThrough,
              )),
            ],
          ),
        ),
      ),
    );
  }

  void _toggleIndicator(ChartIndicatorType type) {
    widget.onSettingsChanged?.call(widget.settings.toggleIndicator(type));
  }

  void _handlePointerSignal(PointerSignalEvent event) {
    if (event is PointerScrollEvent) {
      final scrollDelta = event.scrollDelta.dy;
      final newRange = (_visibleDataRange + scrollDelta * 0.001).clamp(0.1, 1.0);
      if ((newRange - _visibleDataRange).abs() > 0.005) {
        setState(() { _visibleDataRange = newRange; });
      }
    }
  }

  void _handleHorizontalDrag(DragUpdateDetails details) {
    final delta = details.primaryDelta ?? 0;
    final newOffset = (_scrollOffset - delta / 300).clamp(0.0, 1.0);
    if ((newOffset - _scrollOffset).abs() > 0.002) {
      setState(() { _scrollOffset = newOffset; });
    }
  }

  void _handleDrawingTap(TapUpDetails details) {
    setState(() {
      _currentDrawingPoints.add(details.localPosition);
      if (_activeDrawingTool == DrawingToolType.horizontalLine ||
          _activeDrawingTool == DrawingToolType.verticalLine) {
        _completeDrawing();
      } else if (_currentDrawingPoints.length >= 2) {
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
    widget.onSettingsChanged?.call(widget.settings.copyWith(drawings: newDrawings));
    setState(() {
      _activeDrawingTool = null;
      _currentDrawingPoints.clear();
    });
  }

  Widget _buildCrosshairOverlay(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    if (_touchedIndex == null || _touchedIndex! >= visibleData.length) return const SizedBox();

    final candle = visibleData[_touchedIndex!];
    final isRising = candle.close >= candle.open;
    final priceColor = isRising ? AppTheme.stockRise : AppTheme.stockFall;
    final changePercent = candle.open != 0 ? ((candle.close - candle.open) / candle.open * 100) : 0.0;

    return Positioned(
      top: 0, left: 0, right: 0,
      child: IgnorePointer(
        child: Container(
        padding: const EdgeInsets.all(8),
        margin: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor.withAlpha(242),
          borderRadius: BorderRadius.circular(8),
          boxShadow: [BoxShadow(color: Colors.black.withAlpha(25), blurRadius: 4)],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            Text(DateFormat('yyyy/MM/dd').format(candle.date),
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            _buildPriceLabel('開', candle.open, priceColor),
            _buildPriceLabel('高', candle.high, priceColor),
            _buildPriceLabel('低', candle.low, priceColor),
            _buildPriceLabel('收', candle.close, priceColor),
            Text('${changePercent >= 0 ? "+" : ""}${changePercent.toStringAsFixed(2)}%',
                style: TextStyle(fontSize: 11, color: priceColor, fontWeight: FontWeight.w500)),
            Text('量 ${_formatVolume(candle.volume.toDouble())}', style: const TextStyle(fontSize: 11)),
          ],
        ),
        ),
      ),
    );
  }

  Widget _buildPriceLabel(String label, double value, Color color) {
    return RichText(
      text: TextSpan(
        style: DefaultTextStyle.of(context).style.copyWith(fontSize: 11),
        children: [
          TextSpan(text: '$label '),
          TextSpan(text: value.toStringAsFixed(2), style: TextStyle(color: color, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildPatternMarkers(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    return CustomPaint(
      painter: PatternMarkerPainter(
        patterns: widget.patterns, visibleData: visibleData, startIndex: startIndex,
        textStyle: TextStyle(fontSize: 10, color: Theme.of(context).textTheme.bodySmall?.color),
      ),
      size: Size.infinite,
    );
  }

  Widget _buildDrawingsOverlay(BuildContext context) {
    return CustomPaint(painter: DrawingsPainter(drawings: widget.settings.drawings), size: Size.infinite);
  }

  Widget _buildActiveDrawing(BuildContext context) {
    return CustomPaint(
      painter: ActiveDrawingPainter(points: _currentDrawingPoints, toolType: _activeDrawingTool!),
      size: Size.infinite,
    );
  }

  // ==================== 副圖相關 ====================

  Widget _buildSubChartSelector(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color ?? const Color(0xFF1E272E),
        border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: Row(
        children: [
          const Text('副圖', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
          const SizedBox(width: 8),
          ...SubChartType.values.map((type) {
            final isSelected = _selectedSubChart == type;
            return Padding(
              padding: const EdgeInsets.only(right: 4),
              child: ChoiceChip(
                label: Text(_subChartLabel(type), style: const TextStyle(fontSize: 11)),
                selected: isSelected,
                onSelected: (_) => setState(() => _selectedSubChart = type),
                visualDensity: VisualDensity.compact,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            );
          }),
        ],
      ),
    );
  }

  String _subChartLabel(SubChartType type) {
    switch (type) {
      case SubChartType.none: return '無';
      case SubChartType.macd: return 'MACD';
      case SubChartType.rsi: return 'RSI';
      case SubChartType.kd: return 'KD';
    }
  }

  Widget _buildSubChart(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    switch (_selectedSubChart) {
      case SubChartType.macd: return _buildMACDSubChart(context, visibleData, startIndex);
      case SubChartType.rsi: return _buildRSISubChart(context, visibleData, startIndex);
      case SubChartType.kd: return _buildKDSubChart(context, visibleData, startIndex);
      case SubChartType.none: return const SizedBox();
    }
  }

  Widget _buildNoDataHint(String name) {
    return Center(child: Text('$name 數據不足', style: const TextStyle(fontSize: 12, color: Colors.grey)));
  }

  Widget _buildMACDSubChart(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    final macdData = _cachedMACD ?? [];
    if (macdData.isEmpty) return _buildNoDataHint('MACD');

    // 使用 CustomPainter 繪製 MACD（避免 histogram 每根一個 LineChartBarData）
    return Padding(
      padding: const EdgeInsets.only(right: 50, left: 8, top: 4, bottom: 4),
      child: CustomPaint(
        painter: _MACDPainter(
          allMacdData: macdData,
          visibleData: visibleData,
          startIndex: startIndex,
          isDark: true,
        ),
      ),
    );
  }

  Widget _buildRSISubChart(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    final rsiData = _cachedRSI ?? [];
    if (rsiData.isEmpty) return _buildNoDataHint('RSI');

    final List<FlSpot> rsiSpots = [];
    for (int i = 0; i < visibleData.length; i++) {
      final idx = startIndex + i;
      if (idx < rsiData.length) rsiSpots.add(FlSpot(i.toDouble(), rsiData[idx]));
    }
    if (rsiSpots.isEmpty) return _buildNoDataHint('RSI');

    return Padding(
      padding: const EdgeInsets.only(right: 16, left: 8, top: 4, bottom: 4),
      child: LineChart(LineChartData(
        minX: 0, maxX: (visibleData.length - 1).toDouble(), minY: 0, maxY: 100,
        gridData: FlGridData(
          show: true, drawVerticalLine: false, horizontalInterval: 10,
          getDrawingHorizontalLine: (value) {
            if (value == 70) return FlLine(color: Colors.red.withAlpha(128), strokeWidth: 1, dashArray: [4, 4]);
            if (value == 30) return FlLine(color: Colors.green.withAlpha(128), strokeWidth: 1, dashArray: [4, 4]);
            if (value == 50) return FlLine(color: Colors.grey.withAlpha(76), strokeWidth: 0.5, dashArray: [3, 3]);
            return FlLine(color: Theme.of(context).dividerColor.withAlpha(38), strokeWidth: 0.5);
          },
        ),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(sideTitles: SideTitles(
            showTitles: true, reservedSize: 30,
            getTitlesWidget: (v, _) {
              if (v == 0 || v == 30 || v == 50 || v == 70 || v == 100) {
                return Text(v.toInt().toString(),
                    style: TextStyle(fontSize: 9, color: Theme.of(context).textTheme.bodySmall?.color));
              }
              return const SizedBox();
            },
          )),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: true, border: Border.all(color: Theme.of(context).dividerColor.withAlpha(76))),
        lineTouchData: const LineTouchData(enabled: false),
        lineBarsData: [
          LineChartBarData(
            spots: rsiSpots, isCurved: true, color: Colors.purple, barWidth: 1.5,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(show: true, color: Colors.purple.withAlpha(12)),
          ),
        ],
      )),
    );
  }

  Widget _buildKDSubChart(BuildContext context, List<StockHistory> visibleData, int startIndex) {
    final kdData = _cachedKD ?? [];
    if (kdData.isEmpty) return _buildNoDataHint('KD');

    final List<FlSpot> kSpots = [], dSpots = [];
    for (int i = 0; i < visibleData.length; i++) {
      final idx = startIndex + i;
      if (idx < kdData.length) {
        kSpots.add(FlSpot(i.toDouble(), kdData[idx].$1));
        dSpots.add(FlSpot(i.toDouble(), kdData[idx].$2));
      }
    }
    if (kSpots.isEmpty) return _buildNoDataHint('KD');

    return Padding(
      padding: const EdgeInsets.only(right: 16, left: 8, top: 4, bottom: 4),
      child: LineChart(LineChartData(
        minX: 0, maxX: (visibleData.length - 1).toDouble(), minY: 0, maxY: 100,
        gridData: FlGridData(
          show: true, drawVerticalLine: false, horizontalInterval: 20,
          getDrawingHorizontalLine: (value) {
            if (value == 80) return FlLine(color: Colors.red.withAlpha(128), strokeWidth: 1, dashArray: [4, 4]);
            if (value == 20) return FlLine(color: Colors.green.withAlpha(128), strokeWidth: 1, dashArray: [4, 4]);
            if (value == 50) return FlLine(color: Colors.grey.withAlpha(76), strokeWidth: 0.5, dashArray: [3, 3]);
            return FlLine(color: Theme.of(context).dividerColor.withAlpha(38), strokeWidth: 0.5);
          },
        ),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(sideTitles: SideTitles(
            showTitles: true, reservedSize: 30,
            getTitlesWidget: (v, _) {
              if (v == 0 || v == 20 || v == 50 || v == 80 || v == 100) {
                return Text(v.toInt().toString(),
                    style: TextStyle(fontSize: 9, color: Theme.of(context).textTheme.bodySmall?.color));
              }
              return const SizedBox();
            },
          )),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: true, border: Border.all(color: Theme.of(context).dividerColor.withAlpha(76))),
        lineTouchData: const LineTouchData(enabled: false),
        lineBarsData: [
          LineChartBarData(spots: kSpots, isCurved: true, color: Colors.blue.shade700, barWidth: 1.5,
              dotData: const FlDotData(show: false)),
          LineChartBarData(spots: dSpots, isCurved: true, color: Colors.orange.shade700, barWidth: 1.5,
              dotData: const FlDotData(show: false)),
        ],
      )),
    );
  }

  // ==================== 指標計算 ====================

  List<double> _computeEMA(List<double> data, int period) {
    if (data.isEmpty) return [];
    if (data.length < period) {
      List<double> result = [];
      double sum = 0;
      for (int i = 0; i < data.length; i++) { sum += data[i]; result.add(sum / (i + 1)); }
      return result;
    }
    List<double> result = List.filled(data.length, 0);
    double sum = 0;
    for (int i = 0; i < period; i++) { sum += data[i]; result[i] = sum / (i + 1); }
    result[period - 1] = sum / period;
    double k = 2.0 / (period + 1);
    for (int i = period; i < data.length; i++) { result[i] = data[i] * k + result[i - 1] * (1 - k); }
    return result;
  }

  List<_MACDValue> _computeMACDValues(List<StockHistory> data) {
    if (data.length < 2) return [];
    final closes = data.map((d) => d.close).toList();
    final ema12 = _computeEMA(closes, 12);
    final ema26 = _computeEMA(closes, 26);
    List<double> dif = [];
    for (int i = 0; i < closes.length; i++) { dif.add(ema12[i] - ema26[i]); }
    final dea = _computeEMA(dif, 9);
    return List.generate(closes.length, (i) => _MACDValue(dif: dif[i], dea: dea[i], histogram: dif[i] - dea[i]));
  }

  List<double> _computeRSIValues(List<StockHistory> data, {int period = 14}) {
    if (data.length < period + 1) return List.filled(data.length, 50);
    List<double> result = List.filled(data.length, 50);
    List<double> gains = [], losses = [];
    for (int i = 1; i < data.length; i++) {
      double change = data[i].close - data[i - 1].close;
      gains.add(change > 0 ? change : 0);
      losses.add(change < 0 ? -change : 0);
    }
    double avgGain = 0, avgLoss = 0;
    for (int i = 0; i < period; i++) { avgGain += gains[i]; avgLoss += losses[i]; }
    avgGain /= period; avgLoss /= period;
    result[period] = avgLoss == 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    for (int i = period; i < gains.length; i++) {
      avgGain = (avgGain * (period - 1) + gains[i]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
      result[i + 1] = avgLoss == 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    }
    return result;
  }

  List<(double, double)> _computeKDValues(List<StockHistory> data, {int period = 9}) {
    if (data.length < period) return List.filled(data.length, (50.0, 50.0));
    List<(double, double)> result = [];
    double prevK = 50, prevD = 50;
    for (int i = 0; i < data.length; i++) {
      if (i < period - 1) { result.add((50.0, 50.0)); continue; }
      double highestHigh = data[i].high, lowestLow = data[i].low;
      for (int j = 1; j < period; j++) {
        if (data[i - j].high > highestHigh) highestHigh = data[i - j].high;
        if (data[i - j].low < lowestLow) lowestLow = data[i - j].low;
      }
      double rsv = (highestHigh == lowestLow) ? 50 : (data[i].close - lowestLow) / (highestHigh - lowestLow) * 100;
      double k = 2.0 / 3.0 * prevK + 1.0 / 3.0 * rsv;
      double d = 2.0 / 3.0 * prevD + 1.0 / 3.0 * k;
      result.add((k, d));
      prevK = k; prevD = d;
    }
    return result;
  }

  Widget _buildZoomControls(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(icon: const Icon(Icons.zoom_in, size: 20), onPressed: () {
            setState(() { _visibleDataRange = (_visibleDataRange - 0.1).clamp(0.1, 1.0); });
          }, tooltip: '放大'),
          IconButton(icon: const Icon(Icons.zoom_out, size: 20), onPressed: () {
            setState(() { _visibleDataRange = (_visibleDataRange + 0.1).clamp(0.1, 1.0); });
          }, tooltip: '縮小'),
          IconButton(icon: const Icon(Icons.fit_screen, size: 20), onPressed: () {
            setState(() { _visibleDataRange = 1.0; _scrollOffset = 0.0; });
          }, tooltip: '重置'),
          const Spacer(),
          Text('顯示 ${(_visibleDataRange * 100).toStringAsFixed(0)}%',
              style: TextStyle(fontSize: 12, color: Theme.of(context).textTheme.bodySmall?.color)),
        ],
      ),
    );
  }

  void _showSettingsDialog(BuildContext context) {
    showModalBottomSheet(context: context, builder: (context) =>
        _ChartSettingsSheet(settings: widget.settings, onSettingsChanged: widget.onSettingsChanged));
  }

  String _formatVolume(double volume) {
    if (volume >= 100000000) return '${(volume / 100000000).toStringAsFixed(0)}億';
    if (volume >= 10000) return '${(volume / 10000).toStringAsFixed(0)}萬';
    return volume.toStringAsFixed(0);
  }
}

// ==================== CustomPainters ====================

/// 預計算的均線資料
class _PrecomputedMA {
  final List<double?>? ma5;
  final List<double?>? ma10;
  final List<double?>? ma20;
  final List<double?>? ma60;
  const _PrecomputedMA({this.ma5, this.ma10, this.ma20, this.ma60});
}

/// K 線主圖 Painter（高效能：單次 paint 繪製所有 K 棒 + 均線 + 布林）
class _CandlestickChartPainter extends CustomPainter {
  final List<StockHistory> data;
  final ChartSettings settings;
  final int? touchedIndex;
  final bool isDark;
  final _PrecomputedMA? maData;
  final List<(double, double, double)?>? bollingerData;

  _CandlestickChartPainter({
    required this.data,
    required this.settings,
    this.touchedIndex,
    this.isDark = false,
    this.maData,
    this.bollingerData,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;

    final n = data.length;
    final minPrice = data.map((e) => e.low).reduce(min);
    final maxPrice = data.map((e) => e.high).reduce(max);
    final priceRange = maxPrice - minPrice;
    final paddedMin = minPrice - priceRange * 0.1;
    final paddedMax = maxPrice + priceRange * 0.1;
    final paddedRange = paddedMax - paddedMin;
    if (paddedRange == 0) return;

    final candleWidth = (size.width / n).clamp(3.0, 16.0);
    final bodyWidth = candleWidth * 0.7;

    double priceToY(double price) => size.height - ((price - paddedMin) / paddedRange * size.height);

    // 繪製網格線
    final gridPaint = Paint()..color = Colors.grey.shade800.withAlpha(128)..strokeWidth = 0.5;
    for (int i = 1; i < 5; i++) {
      final y = size.height * i / 5;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // 繪製布林通道（使用預計算資料）
    if (settings.isIndicatorEnabled(ChartIndicatorType.bollinger) && bollingerData != null) {
      _drawPrecomputedBollinger(canvas, size, priceToY, n);
    }

    // 繪製均線
    _drawMovingAverages(canvas, size, data, priceToY, n);

    // 繪製 K 棒
    for (int i = 0; i < n; i++) {
      final candle = data[i];
      final isRising = candle.close >= candle.open;
      final color = isRising ? AppTheme.stockRise : AppTheme.stockFall;
      final x = (i + 0.5) * candleWidth;

      // 影線
      final wickPaint = Paint()..color = color..strokeWidth = 1;
      canvas.drawLine(Offset(x, priceToY(candle.high)), Offset(x, priceToY(candle.low)), wickPaint);

      // 實體
      final bodyTop = priceToY(isRising ? candle.close : candle.open);
      final bodyBottom = priceToY(isRising ? candle.open : candle.close);
      final bodyHeight = (bodyBottom - bodyTop).abs().clamp(1.0, size.height);

      final bodyPaint = Paint()
        ..color = color
        ..style = PaintingStyle.fill
        ..strokeWidth = 1;

      canvas.drawRect(
        Rect.fromCenter(center: Offset(x, (bodyTop + bodyBottom) / 2), width: bodyWidth, height: bodyHeight),
        bodyPaint,
      );
    }

    // 繪製十字線
    if (touchedIndex != null && touchedIndex! < n) {
      final x = (touchedIndex! + 0.5) * candleWidth;
      final crossPaint = Paint()..color = Colors.grey..strokeWidth = 0.5..style = PaintingStyle.stroke;
      // 垂直線
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), crossPaint);
      // 水平線（收盤價位置）
      final closeY = priceToY(data[touchedIndex!].close);
      canvas.drawLine(Offset(0, closeY), Offset(size.width, closeY), crossPaint);
    }
  }

  void _drawMovingAverages(Canvas canvas, Size size, List<StockHistory> data, double Function(double) priceToY, int n) {
    final candleWidth = (size.width / n).clamp(3.0, 16.0);

    void drawPrecomputedMA(List<double?>? maValues, Color color, ChartIndicatorType type) {
      if (!settings.isIndicatorEnabled(type) || maValues == null) return;
      final path = Path();
      bool started = false;
      for (int i = 0; i < maValues.length; i++) {
        final v = maValues[i];
        if (v == null) continue;
        final x = (i + 0.5) * candleWidth;
        final y = priceToY(v);
        if (!started) { path.moveTo(x, y); started = true; } else { path.lineTo(x, y); }
      }
      canvas.drawPath(path, Paint()..color = color..strokeWidth = 1.5..style = PaintingStyle.stroke);
    }

    if (maData != null) {
      drawPrecomputedMA(maData!.ma5, Colors.blue, ChartIndicatorType.ma5);
      drawPrecomputedMA(maData!.ma10, Colors.orange, ChartIndicatorType.ma10);
      drawPrecomputedMA(maData!.ma20, Colors.purple, ChartIndicatorType.ma20);
      drawPrecomputedMA(maData!.ma60, Colors.teal, ChartIndicatorType.ma60);
    }
  }

  void _drawPrecomputedBollinger(Canvas canvas, Size size, double Function(double) priceToY, int n) {
    if (bollingerData == null) return;
    final candleWidth = (size.width / n).clamp(3.0, 16.0);
    final upperPath = Path();
    final middlePath = Path();
    final lowerPath = Path();
    bool started = false;

    for (int i = 0; i < bollingerData!.length; i++) {
      final b = bollingerData![i];
      if (b == null) continue;
      final x = (i + 0.5) * candleWidth;
      if (!started) {
        upperPath.moveTo(x, priceToY(b.$1));
        middlePath.moveTo(x, priceToY(b.$2));
        lowerPath.moveTo(x, priceToY(b.$3));
        started = true;
      } else {
        upperPath.lineTo(x, priceToY(b.$1));
        middlePath.lineTo(x, priceToY(b.$2));
        lowerPath.lineTo(x, priceToY(b.$3));
      }
    }

    canvas.drawPath(upperPath, Paint()..color = Colors.cyan.withAlpha(178)..strokeWidth = 1..style = PaintingStyle.stroke);
    canvas.drawPath(middlePath, Paint()..color = Colors.cyan..strokeWidth = 1.5..style = PaintingStyle.stroke);
    canvas.drawPath(lowerPath, Paint()..color = Colors.cyan.withAlpha(178)..strokeWidth = 1..style = PaintingStyle.stroke);
  }

  @override
  bool shouldRepaint(covariant _CandlestickChartPainter oldDelegate) {
    return data != oldDelegate.data || settings != oldDelegate.settings ||
        touchedIndex != oldDelegate.touchedIndex || isDark != oldDelegate.isDark;
  }
}

/// 右側價格軸
class _PriceAxisPainter extends CustomPainter {
  final List<StockHistory> data;
  final bool isDark;

  _PriceAxisPainter({required this.data, this.isDark = false});

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;
    final minPrice = data.map((e) => e.low).reduce(min);
    final maxPrice = data.map((e) => e.high).reduce(max);
    final range = maxPrice - minPrice;
    final paddedMin = minPrice - range * 0.1;
    final paddedMax = maxPrice + range * 0.1;

    final textColor = isDark ? Colors.grey.shade400 : Colors.grey.shade600;

    for (int i = 0; i <= 5; i++) {
      final price = paddedMin + (paddedMax - paddedMin) * (1 - i / 5);
      final y = size.height * i / 5;
      final tp = TextPainter(
        text: TextSpan(text: price.toStringAsFixed(1), style: TextStyle(fontSize: 9, color: textColor)),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(4, y - tp.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant _PriceAxisPainter old) => data != old.data;
}

/// 底部日期軸
class _DateAxisPainter extends CustomPainter {
  final List<StockHistory> data;
  final bool isDark;

  _DateAxisPainter({required this.data, this.isDark = false});

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;
    final n = data.length;
    final step = max(1, n ~/ 5);
    final textColor = isDark ? Colors.grey.shade400 : Colors.grey.shade600;

    for (int i = 0; i < n; i += step) {
      final d = data[i].date;
      final x = (i + 0.5) / n * size.width;
      final tp = TextPainter(
        text: TextSpan(text: '${d.month}/${d.day}', style: TextStyle(fontSize: 9, color: textColor)),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(x - tp.width / 2, 2));
    }
  }

  @override
  bool shouldRepaint(covariant _DateAxisPainter old) => data != old.data;
}

/// 成交量 Painter
class _VolumePainter extends CustomPainter {
  final List<StockHistory> data;

  _VolumePainter({required this.data});

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;
    final n = data.length;
    final maxVol = data.map((e) => e.volume).reduce(max).toDouble();
    if (maxVol == 0) return;

    final barWidth = (size.width / n).clamp(2.0, 14.0) * 0.7;

    for (int i = 0; i < n; i++) {
      final candle = data[i];
      final isRising = candle.close >= candle.open;
      final barHeight = (candle.volume / maxVol) * size.height;
      final x = (i + 0.5) * size.width / n;

      final paint = Paint()..color = (isRising ? AppTheme.stockRise : AppTheme.stockFall).withAlpha(128);
      canvas.drawRect(
        Rect.fromLTWH(x - barWidth / 2, size.height - barHeight, barWidth, barHeight),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _VolumePainter old) => data != old.data;
}

/// MACD 副圖 Painter
class _MACDPainter extends CustomPainter {
  final List<_MACDValue> allMacdData;
  final List<StockHistory> visibleData;
  final int startIndex;
  final bool isDark;

  _MACDPainter({required this.allMacdData, required this.visibleData, required this.startIndex, this.isDark = false});

  @override
  void paint(Canvas canvas, Size size) {
    final n = visibleData.length;
    if (n == 0) return;

    double minY = 0, maxY = 0;
    final List<_MACDValue> visible = [];
    for (int i = 0; i < n; i++) {
      final idx = startIndex + i;
      if (idx >= allMacdData.length) break;
      final m = allMacdData[idx];
      visible.add(m);
      minY = min(minY, min(m.dif, min(m.dea, m.histogram)));
      maxY = max(maxY, max(m.dif, max(m.dea, m.histogram)));
    }
    if (visible.isEmpty) return;

    final range = maxY - minY;
    if (range == 0) return;
    final paddedMin = minY - range * 0.1;
    final paddedMax = maxY + range * 0.1;
    final paddedRange = paddedMax - paddedMin;

    double toY(double v) => size.height - ((v - paddedMin) / paddedRange * size.height);
    final barWidth = (size.width / n).clamp(2.0, 12.0) * 0.6;

    // 零線
    final zeroY = toY(0);
    canvas.drawLine(Offset(0, zeroY), Offset(size.width, zeroY),
        Paint()..color = (isDark ? Colors.grey.shade700 : Colors.grey.shade400)..strokeWidth = 0.5);

    // Histogram
    for (int i = 0; i < visible.length; i++) {
      final x = (i + 0.5) * size.width / n;
      final h = visible[i].histogram;
      final paint = Paint()..color = (h >= 0 ? AppTheme.stockRise : AppTheme.stockFall).withAlpha(128);
      canvas.drawRect(Rect.fromLTWH(x - barWidth / 2, min(zeroY, toY(h)), barWidth, (toY(h) - zeroY).abs()), paint);
    }

    // DIF 線
    final difPath = Path();
    final deaPath = Path();
    for (int i = 0; i < visible.length; i++) {
      final x = (i + 0.5) * size.width / n;
      if (i == 0) {
        difPath.moveTo(x, toY(visible[i].dif));
        deaPath.moveTo(x, toY(visible[i].dea));
      } else {
        difPath.lineTo(x, toY(visible[i].dif));
        deaPath.lineTo(x, toY(visible[i].dea));
      }
    }
    canvas.drawPath(difPath, Paint()..color = Colors.blue..strokeWidth = 1.5..style = PaintingStyle.stroke);
    canvas.drawPath(deaPath, Paint()..color = Colors.orange..strokeWidth = 1.5..style = PaintingStyle.stroke);
  }

  @override
  bool shouldRepaint(covariant _MACDPainter old) =>
      visibleData != old.visibleData || startIndex != old.startIndex;
}

// ==================== 其他 Painters ====================

class PatternMarkerPainter extends CustomPainter {
  final List<PatternMarker> patterns;
  final List<StockHistory> visibleData;
  final int startIndex;
  final TextStyle textStyle;

  PatternMarkerPainter({required this.patterns, required this.visibleData, required this.startIndex, required this.textStyle});

  @override
  void paint(Canvas canvas, Size size) {
    for (final pattern in patterns) {
      final relativeStart = pattern.startIndex - startIndex;
      final relativeEnd = pattern.endIndex - startIndex;
      if (relativeEnd < 0 || relativeStart >= visibleData.length) continue;

      final startX = (relativeStart.clamp(0, visibleData.length - 1)) / visibleData.length * size.width;
      final endX = (relativeEnd.clamp(0, visibleData.length - 1)) / visibleData.length * size.width;

      canvas.drawRect(Rect.fromLTRB(startX, 0, endX, size.height),
          Paint()..color = pattern.markerColor.withAlpha(76)..style = PaintingStyle.fill);

      final tp = TextPainter(
        text: TextSpan(
          text: '${pattern.typeName} ${pattern.confidence.toStringAsFixed(0)}%',
          style: textStyle.copyWith(color: pattern.markerColor, fontWeight: FontWeight.bold),
        ),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(startX + 4, 4));
    }
  }

  @override
  bool shouldRepaint(covariant PatternMarkerPainter old) => patterns != old.patterns || visibleData != old.visibleData;
}

class DrawingsPainter extends CustomPainter {
  final List<DrawingObject> drawings;
  DrawingsPainter({required this.drawings});

  @override
  void paint(Canvas canvas, Size size) {
    for (final drawing in drawings) {
      final paint = Paint()..color = drawing.color..strokeWidth = drawing.strokeWidth..style = PaintingStyle.stroke;
      switch (drawing.type) {
        case DrawingToolType.trendLine:
          if (drawing.points.length >= 2) canvas.drawLine(drawing.points[0], drawing.points[1], paint);
          break;
        case DrawingToolType.horizontalLine:
          if (drawing.points.isNotEmpty) canvas.drawLine(Offset(0, drawing.points[0].dy), Offset(size.width, drawing.points[0].dy), paint);
          break;
        case DrawingToolType.verticalLine:
          if (drawing.points.isNotEmpty) canvas.drawLine(Offset(drawing.points[0].dx, 0), Offset(drawing.points[0].dx, size.height), paint);
          break;
        default: break;
      }
    }
  }

  @override
  bool shouldRepaint(covariant DrawingsPainter old) => drawings != old.drawings;
}

class ActiveDrawingPainter extends CustomPainter {
  final List<Offset> points;
  final DrawingToolType toolType;
  ActiveDrawingPainter({required this.points, required this.toolType});

  @override
  void paint(Canvas canvas, Size size) {
    if (points.isEmpty) return;
    final paint = Paint()..color = Colors.blue.withAlpha(128)..strokeWidth = 2..style = PaintingStyle.stroke;
    for (final point in points) {
      canvas.drawCircle(point, 4, paint..style = PaintingStyle.fill);
    }
    if (toolType == DrawingToolType.horizontalLine && points.isNotEmpty) {
      canvas.drawLine(Offset(0, points[0].dy), Offset(size.width, points[0].dy), paint..style = PaintingStyle.stroke);
    }
  }

  @override
  bool shouldRepaint(covariant ActiveDrawingPainter old) => points != old.points || toolType != old.toolType;
}

class _ChartSettingsSheet extends StatelessWidget {
  final ChartSettings settings;
  final ValueChanged<ChartSettings>? onSettingsChanged;
  const _ChartSettingsSheet({required this.settings, this.onSettingsChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            const Text('圖表設置', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const Spacer(),
            IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
          ]),
          const Divider(),
          const Text('技術指標', style: TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8, runSpacing: 8,
            children: settings.indicators.entries.map((e) {
              return FilterChip(label: Text(e.value.name), selected: e.value.isEnabled,
                  onSelected: (_) { onSettingsChanged?.call(settings.toggleIndicator(e.key)); });
            }).toList(),
          ),
          const SizedBox(height: 16),
          const Text('顯示選項', style: TextStyle(fontWeight: FontWeight.w500)),
          SwitchListTile(title: const Text('顯示成交量'), value: settings.showVolume,
              onChanged: (v) { onSettingsChanged?.call(settings.copyWith(showVolume: v)); }),
          SwitchListTile(title: const Text('顯示形態標記'), value: settings.showPatterns,
              onChanged: (v) { onSettingsChanged?.call(settings.copyWith(showPatterns: v)); }),
          SwitchListTile(title: const Text('啟用十字線'), value: settings.enableCrosshair,
              onChanged: (v) { onSettingsChanged?.call(settings.copyWith(enableCrosshair: v)); }),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
