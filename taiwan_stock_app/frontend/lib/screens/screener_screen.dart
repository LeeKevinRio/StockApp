import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/screen_criteria.dart';
import 'stock_detail_screen.dart';

/// 股票篩選器畫面
class ScreenerScreen extends StatefulWidget {
  const ScreenerScreen({super.key});

  @override
  State<ScreenerScreen> createState() => _ScreenerScreenState();
}

class _ScreenerScreenState extends State<ScreenerScreen> {
  final _criteria = ScreenCriteria();
  List<PresetScreen>? _presets;
  ScreenResponse? _results;
  bool _isLoading = false;
  bool _isLoadingPresets = true;
  String? _error;
  String _market = 'TW';
  bool _showFilters = true;

  // Controllers for text fields
  final _peMinController = TextEditingController();
  final _peMaxController = TextEditingController();
  final _pbMinController = TextEditingController();
  final _pbMaxController = TextEditingController();
  final _dividendYieldMinController = TextEditingController();
  final _roeMinController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadPresets();
  }

  @override
  void dispose() {
    _peMinController.dispose();
    _peMaxController.dispose();
    _pbMinController.dispose();
    _pbMaxController.dispose();
    _dividendYieldMinController.dispose();
    _roeMinController.dispose();
    super.dispose();
  }

  Future<void> _loadPresets() async {
    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final presets = await apiService.getPresetScreens();
      setState(() {
        _presets = presets;
        _isLoadingPresets = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingPresets = false;
      });
    }
  }

  Future<void> _search() async {
    // Parse criteria from controllers
    _criteria.peMin = double.tryParse(_peMinController.text);
    _criteria.peMax = double.tryParse(_peMaxController.text);
    _criteria.pbMin = double.tryParse(_pbMinController.text);
    _criteria.pbMax = double.tryParse(_pbMaxController.text);
    _criteria.dividendYieldMin = double.tryParse(_dividendYieldMinController.text);
    _criteria.roeMin = double.tryParse(_roeMinController.text);

    if (_criteria.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請至少輸入一個篩選條件')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
      _showFilters = false;
    });

    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final results = await apiService.screenStocks(_criteria, market: _market);
      setState(() {
        _results = results;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _applyPreset(PresetScreen preset) async {
    setState(() {
      _isLoading = true;
      _error = null;
      _showFilters = false;
    });

    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final results = await apiService.getPresetScreenResults(preset.id, market: _market);
      setState(() {
        _results = results;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _clearFilters() {
    _peMinController.clear();
    _peMaxController.clear();
    _pbMinController.clear();
    _pbMaxController.clear();
    _dividendYieldMinController.clear();
    _roeMinController.clear();
    _criteria.reset();
    setState(() {
      _results = null;
      _showFilters = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('股票篩選器'),
        actions: [
          // Market selector
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'TW', label: Text('台股')),
              ButtonSegment(value: 'US', label: Text('美股')),
            ],
            selected: {_market},
            onSelectionChanged: (value) {
              setState(() {
                _market = value.first;
                _results = null;
              });
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          // Filter panel (collapsible)
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            child: _showFilters ? _buildFilterPanel() : _buildCollapsedFilterBar(),
          ),
          // Results
          Expanded(
            child: _buildResults(),
          ),
        ],
      ),
    );
  }

  Widget _buildCollapsedFilterBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              _results != null ? '找到 ${_results!.total} 檔符合條件' : '',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          TextButton.icon(
            onPressed: () => setState(() => _showFilters = true),
            icon: const Icon(Icons.filter_list, size: 20),
            label: const Text('修改條件'),
          ),
          TextButton.icon(
            onPressed: _clearFilters,
            icon: const Icon(Icons.clear, size: 20),
            label: const Text('清除'),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterPanel() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Preset buttons
          if (_presets != null && _presets!.isNotEmpty) ...[
            const Text('快速篩選', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _presets!.map((preset) {
                return ActionChip(
                  label: Text(preset.name),
                  avatar: const Icon(Icons.flash_on, size: 16),
                  onPressed: () => _applyPreset(preset),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),
          ],
          // Custom filters
          const Text('自訂篩選', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          // P/E ratio
          Row(
            children: [
              Expanded(
                child: _buildFilterField(
                  label: '本益比 (最小)',
                  controller: _peMinController,
                  hint: '例: 5',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildFilterField(
                  label: '本益比 (最大)',
                  controller: _peMaxController,
                  hint: '例: 15',
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // P/B ratio
          Row(
            children: [
              Expanded(
                child: _buildFilterField(
                  label: '股價淨值比 (最小)',
                  controller: _pbMinController,
                  hint: '例: 0.5',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildFilterField(
                  label: '股價淨值比 (最大)',
                  controller: _pbMaxController,
                  hint: '例: 2',
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Dividend yield & ROE
          Row(
            children: [
              Expanded(
                child: _buildFilterField(
                  label: '殖利率 (最低%)',
                  controller: _dividendYieldMinController,
                  hint: '例: 5',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildFilterField(
                  label: 'ROE (最低%)',
                  controller: _roeMinController,
                  hint: '例: 10',
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Search button
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _isLoading ? null : _search,
                  icon: _isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.search),
                  label: Text(_isLoading ? '搜尋中...' : '開始篩選'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              OutlinedButton(
                onPressed: _clearFilters,
                child: const Text('清除'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFilterField({
    required String label,
    required TextEditingController controller,
    String? hint,
  }) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: const OutlineInputBorder(),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        isDense: true,
      ),
    );
  }

  Widget _buildResults() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('正在篩選股票...'),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text('篩選失敗', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.grey)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _search, child: const Text('重試')),
          ],
        ),
      );
    }

    if (_results == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.filter_list, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            const Text('設定篩選條件開始搜尋'),
            const SizedBox(height: 8),
            Text(
              '或選擇快速篩選策略',
              style: TextStyle(color: Theme.of(context).hintColor, fontSize: 14),
            ),
          ],
        ),
      );
    }

    if (_results!.stocks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            const Text('沒有找到符合條件的股票'),
            const SizedBox(height: 8),
            TextButton(
              onPressed: _clearFilters,
              child: const Text('調整篩選條件'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: _results!.stocks.length,
      itemBuilder: (context, index) {
        final stock = _results!.stocks[index];
        return _buildStockCard(stock);
      },
    );
  }

  Widget _buildStockCard(ScreenResultItem stock) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => StockDetailScreen(
                stockId: stock.stockId,
                market: stock.marketRegion,
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Stock name and ID
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          stock.name,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          '${stock.stockId}${stock.industry != null ? ' • ${stock.industry}' : ''}',
                          style: TextStyle(color: Theme.of(context).textTheme.bodySmall?.color, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: Colors.grey),
                ],
              ),
              const SizedBox(height: 12),
              // Metrics
              Row(
                children: [
                  _buildMetricChip('P/E', stock.peRatio?.toStringAsFixed(1) ?? '-'),
                  _buildMetricChip('P/B', stock.pbRatio?.toStringAsFixed(2) ?? '-'),
                  _buildMetricChip('ROE', stock.roe != null ? '${stock.roe!.toStringAsFixed(1)}%' : '-'),
                  _buildMetricChip('殖利率', stock.dividendYield != null ? '${stock.dividendYield!.toStringAsFixed(1)}%' : '-'),
                ],
              ),
              if (stock.marketCap != null) ...[
                const SizedBox(height: 8),
                Text(
                  '市值: ${stock.formattedMarketCap}',
                  style: TextStyle(color: Theme.of(context).textTheme.bodySmall?.color, fontSize: 12),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetricChip(String label, String value) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: Theme.of(context).primaryColor.withAlpha(26),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Column(
          children: [
            Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey)),
            Text(
              value,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Theme.of(context).primaryColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
