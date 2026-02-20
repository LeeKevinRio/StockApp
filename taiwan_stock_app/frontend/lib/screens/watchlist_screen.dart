import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/watchlist_provider.dart';
import '../providers/market_provider.dart';
import '../services/api_service.dart';
import '../widgets/stock_card.dart';
import '../widgets/common/sort_filter_bar.dart';
import '../widgets/common/skeleton_loader.dart';
import '../widgets/common/error_view.dart';
import '../widgets/market_switcher.dart';

class WatchlistScreen extends StatefulWidget {
  const WatchlistScreen({super.key});

  @override
  State<WatchlistScreen> createState() => _WatchlistScreenState();
}

class _WatchlistScreenState extends State<WatchlistScreen> {
  String? _lastMarket;
  List<Map<String, dynamic>> _groups = [];
  int? _selectedGroupId; // null = 全部

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final marketProvider = context.read<MarketProvider>();
      _lastMarket = marketProvider.marketCode;
      context.read<WatchlistProvider>().setMarketFilter(marketProvider.marketCode);
      _loadGroups();
    });
  }

  Future<void> _loadGroups() async {
    try {
      final groups = await context.read<ApiService>().getWatchlistGroups();
      if (mounted) setState(() => _groups = groups);
    } catch (e) {
      debugPrint('Failed to load watchlist groups: $e');
    }
  }

  void _onMarketChanged() {
    final marketProvider = context.read<MarketProvider>();
    final newMarket = marketProvider.marketCode;

    // 只有市場真的改變時才重新載入
    if (_lastMarket != newMarket) {
      _lastMarket = newMarket;
      // 強制重新載入，清除舊資料
      context.read<WatchlistProvider>().setMarketFilter(newMarket);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<MarketProvider>(
      builder: (context, marketProvider, child) {
        return Scaffold(
      appBar: AppBar(
        title: Text(marketProvider.isUSMarket ? 'Watchlist' : '自選股'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: CompactMarketSwitcher(onMarketChanged: _onMarketChanged),
          ),
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => Navigator.pushNamed(context, '/search'),
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddStockDialog(context),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<WatchlistProvider>().refresh(),
          ),
        ],
      ),
      body: Consumer<WatchlistProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const StockListSkeleton(itemCount: 6);
          }

          if (provider.error != null) {
            return ErrorView(
              message: '載入自選股失敗',
              details: provider.error,
              onRetry: () => provider.loadWatchlist(),
            );
          }

          if (provider.allItems.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.star_border, size: 64, color: Theme.of(context).disabledColor),
                  const SizedBox(height: 16),
                  Text(marketProvider.isUSMarket ? 'No stocks in watchlist' : '尚無自選股'),
                  Text(
                    marketProvider.isUSMarket ? 'Tap + to add stocks' : '點擊右上角 + 新增股票',
                    style: TextStyle(color: Theme.of(context).textTheme.bodySmall?.color),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.pushNamed(context, '/search'),
                    icon: const Icon(Icons.search),
                    label: Text(marketProvider.isUSMarket ? 'Search Stocks' : '搜尋股票'),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              // 分組 tab
              if (_groups.isNotEmpty)
                Container(
                  height: 44,
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(right: 6, top: 6, bottom: 6),
                        child: ChoiceChip(
                          label: Text(marketProvider.isUSMarket ? 'All' : '全部'),
                          selected: _selectedGroupId == null,
                          onSelected: (_) => setState(() => _selectedGroupId = null),
                          visualDensity: VisualDensity.compact,
                        ),
                      ),
                      ..._groups.map((g) => Padding(
                        padding: const EdgeInsets.only(right: 6, top: 6, bottom: 6),
                        child: ChoiceChip(
                          label: Text(g['name'] ?? ''),
                          selected: _selectedGroupId == g['id'],
                          onSelected: (_) => setState(() => _selectedGroupId = g['id'] as int?),
                          visualDensity: VisualDensity.compact,
                        ),
                      )),
                      Padding(
                        padding: const EdgeInsets.only(top: 6, bottom: 6),
                        child: ActionChip(
                          label: const Icon(Icons.add, size: 16),
                          onPressed: _showCreateGroupDialog,
                          visualDensity: VisualDensity.compact,
                        ),
                      ),
                    ],
                  ),
                ),
              // Sort and filter bar
              SortFilterBar(
                currentSort: provider.currentSort,
                onSortChanged: provider.setSortOption,
                showFilterButton: provider.availableIndustries.isNotEmpty,
                filterCount: provider.industryFilter.length,
                onFilterPressed: () => _showFilterBottomSheet(context, provider),
              ),
              // Stock count
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                alignment: Alignment.centerLeft,
                child: Text(
                  marketProvider.isUSMarket
                      ? '${provider.items.length} stocks'
                      : '共 ${provider.items.length} 檔股票',
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).textTheme.bodySmall?.color,
                  ),
                ),
              ),
              // Stock list
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () => provider.refresh(),
                  child: ListView.builder(
                    padding: const EdgeInsets.only(bottom: 8),
                    itemCount: provider.items.length,
                    itemBuilder: (context, index) {
                      final stock = provider.items[index];
                      return Dismissible(
                        key: Key(stock.stockId),
                        direction: DismissDirection.endToStart,
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          margin: const EdgeInsets.symmetric(vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.red,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(Icons.delete, color: Colors.white),
                        ),
                        confirmDismiss: (direction) async {
                          return await showDialog<bool>(
                            context: context,
                            builder: (context) => AlertDialog(
                              title: Text(marketProvider.isUSMarket ? 'Confirm Delete' : '確認刪除'),
                              content: Text(
                                marketProvider.isUSMarket
                                    ? 'Remove ${stock.stockId} from watchlist?'
                                    : '確定要從自選股移除 ${stock.name} (${stock.stockId}) 嗎？',
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(context, false),
                                  child: Text(marketProvider.isUSMarket ? 'Cancel' : '取消'),
                                ),
                                TextButton(
                                  onPressed: () => Navigator.pop(context, true),
                                  child: Text(
                                    marketProvider.isUSMarket ? 'Delete' : '刪除',
                                    style: const TextStyle(color: Colors.red),
                                  ),
                                ),
                              ],
                            ),
                          ) ?? false;
                        },
                        onDismissed: (direction) {
                          provider.removeStock(stock.stockId);
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                marketProvider.isUSMarket
                                    ? '${stock.stockId} removed'
                                    : '${stock.name} 已移除',
                              ),
                              action: SnackBarAction(
                                label: marketProvider.isUSMarket ? 'Undo' : '復原',
                                onPressed: () {
                                  provider.addStock(
                                    stock.stockId,
                                    market: stock.marketRegion ?? 'TW',
                                  );
                                },
                              ),
                            ),
                          );
                        },
                        child: StockCard(
                          stock: stock,
                          onTap: () {
                            Navigator.pushNamed(
                              context,
                              '/stock-detail',
                              arguments: {
                                'stockId': stock.stockId,
                                'market': stock.marketRegion,
                              },
                            );
                          },
                          onDelete: () => _confirmDelete(context, stock.stockId, marketProvider.isUSMarket),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
      },
    );
  }

  void _showCreateGroupDialog() {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('建立分組'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: '分組名稱',
            hintText: '例如: 半導體、金融股',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () async {
              final name = controller.text.trim();
              if (name.isNotEmpty) {
                try {
                  await context.read<ApiService>().createWatchlistGroup(name);
                  if (context.mounted) Navigator.pop(context);
                  _loadGroups();
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('建立失敗: $e')),
                    );
                  }
                }
              }
            },
            child: const Text('建立'),
          ),
        ],
      ),
    );
  }

  void _showFilterBottomSheet(BuildContext context, WatchlistProvider provider) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => _FilterBottomSheet(provider: provider),
    );
  }

  void _showAddStockDialog(BuildContext context) {
    final controller = TextEditingController();
    final marketProvider = context.read<MarketProvider>();
    final isUS = marketProvider.isUSMarket;
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isUS ? 'Add to Watchlist' : '新增自選股'),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(
            labelText: isUS ? 'Stock Symbol' : '股票代碼',
            hintText: isUS ? 'e.g., AAPL' : '例如: 2330',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(isUS ? 'Cancel' : '取消'),
          ),
          TextButton(
            onPressed: () async {
              final stockId = controller.text.trim();
              if (stockId.isNotEmpty) {
                try {
                  await context.read<WatchlistProvider>().addStock(
                    stockId,
                    market: marketProvider.marketCode,
                  );
                  if (context.mounted) {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(isUS ? 'Added to watchlist' : '已新增至自選股')),
                    );
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(isUS ? 'Error: $e' : '錯誤: $e')),
                    );
                  }
                }
              }
            },
            child: Text(isUS ? 'Add' : '新增'),
          ),
        ],
      ),
    );
  }

  void _confirmDelete(BuildContext context, String stockId, bool isUS) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isUS ? 'Confirm Delete' : '確認刪除'),
        content: Text(isUS ? 'Remove from watchlist?' : '確定要從自選股移除嗎？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(isUS ? 'Cancel' : '取消'),
          ),
          TextButton(
            onPressed: () {
              context.read<WatchlistProvider>().removeStock(stockId);
              Navigator.pop(context);
            },
            child: Text(isUS ? 'Delete' : '刪除', style: const TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}

class _FilterBottomSheet extends StatelessWidget {
  final WatchlistProvider provider;

  const _FilterBottomSheet({required this.provider});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '篩選產業',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Row(
                  children: [
                    if (provider.industryFilter.isNotEmpty)
                      TextButton(
                        onPressed: () {
                          provider.clearFilters();
                          Navigator.pop(context);
                        },
                        child: const Text('清除'),
                      ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: provider.availableIndustries.map((industry) {
                  final isSelected = provider.industryFilter.contains(industry);
                  return FilterChip(
                    label: Text(industry),
                    selected: isSelected,
                    onSelected: (_) {
                      provider.toggleIndustryFilter(industry);
                    },
                    selectedColor: Theme.of(context).primaryColor.withValues(alpha: 0.2),
                    checkmarkColor: Theme.of(context).primaryColor,
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}
