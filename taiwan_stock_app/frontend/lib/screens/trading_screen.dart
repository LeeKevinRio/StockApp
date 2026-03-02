import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/trading.dart';
import '../services/api_service.dart';

class TradingScreen extends StatefulWidget {
  const TradingScreen({super.key});

  @override
  State<TradingScreen> createState() => _TradingScreenState();
}

class _TradingScreenState extends State<TradingScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  AccountSummary? _accountSummary;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final accountSummary = await apiService.getTradingAccount();

      setState(() {
        _accountSummary = accountSummary;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('模擬交易'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '帳戶'),
            Tab(text: '持倉'),
            Tab(text: '訂單'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'reset') {
                _showResetConfirmDialog();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'reset',
                child: Text('重置帳戶'),
              ),
            ],
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.grey),
                      const SizedBox(height: 12),
                      Text('載入失敗', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 4),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 32),
                        child: Text(
                          _error!,
                          style: Theme.of(context).textTheme.bodySmall,
                          textAlign: TextAlign.center,
                        ),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: _loadData,
                        icon: const Icon(Icons.refresh),
                        label: const Text('重試'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildAccountTab(),
                      _buildPositionsTab(),
                      _buildOrdersTab(),
                    ],
                  ),
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showOrderDialog(context),
        icon: const Icon(Icons.add),
        label: const Text('下單'),
      ),
    );
  }

  Widget _buildAccountTab() {
    if (_accountSummary == null) return const SizedBox.shrink();

    final account = _accountSummary!.account;
    final isProfit = account.totalProfitLoss > 0;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // 總資產卡片
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Text('總資產', style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 8),
                  Text(
                    '\$${_formatNumber(account.totalValue)}',
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        isProfit ? Icons.arrow_upward : Icons.arrow_downward,
                        color: isProfit ? Colors.green : Colors.red,
                        size: 20,
                      ),
                      Text(
                        '${isProfit ? "+" : ""}\$${_formatNumber(account.totalProfitLoss)} '
                        '(${account.totalProfitLossPercent.toStringAsFixed(2)}%)',
                        style: TextStyle(
                          fontSize: 16,
                          color: isProfit ? Colors.green : Colors.red,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // 資金明細
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '資金明細',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const Divider(),
                  _buildDetailRow('初始資金', '\$${_formatNumber(account.initialBalance)}'),
                  _buildDetailRow('現金餘額', '\$${_formatNumber(account.cashBalance)}'),
                  _buildDetailRow('持倉市值', '\$${_formatNumber(account.totalValue - account.cashBalance)}'),
                  _buildDetailRow(
                    '總損益',
                    '${isProfit ? "+" : ""}\$${_formatNumber(account.totalProfitLoss)}',
                    valueColor: isProfit ? Colors.green : Colors.red,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // 快速操作
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '快速操作',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _showOrderDialog(context, orderType: 'BUY'),
                          icon: const Icon(Icons.add_shopping_cart),
                          label: const Text('買入'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _showOrderDialog(context, orderType: 'SELL'),
                          icon: const Icon(Icons.remove_shopping_cart),
                          label: const Text('賣出'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPositionsTab() {
    if (_accountSummary == null) return const SizedBox.shrink();

    final positions = _accountSummary!.positions;

    if (positions.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inventory_2_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('尚無持倉', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: positions.length,
      itemBuilder: (context, index) {
        return _buildPositionCard(positions[index]);
      },
    );
  }

  Widget _buildPositionCard(VirtualPosition position) {
    final isProfit = position.isProfit;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: isProfit ? Colors.green.withAlpha(51) : Colors.red.withAlpha(51),
          child: Icon(
            isProfit ? Icons.trending_up : Icons.trending_down,
            color: isProfit ? Colors.green : Colors.red,
          ),
        ),
        title: Text(
          '${position.stockId} ${position.stockName ?? ""}',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('持有 ${position.quantity} 股 @ \$${position.avgCost.toStringAsFixed(2)}'),
            Text(
              '市值 \$${_formatNumber(position.marketValue ?? 0)}',
              style: const TextStyle(fontSize: 12),
            ),
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '\$${position.currentPrice?.toStringAsFixed(2) ?? "-"}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              '${isProfit ? "+" : ""}\$${position.unrealizedPnl.toStringAsFixed(0)}',
              style: TextStyle(
                color: isProfit ? Colors.green : (position.isLoss ? Colors.red : Colors.grey),
                fontSize: 12,
              ),
            ),
            Text(
              '${isProfit ? "+" : ""}${position.unrealizedPnlPercent.toStringAsFixed(2)}%',
              style: TextStyle(
                color: isProfit ? Colors.green : (position.isLoss ? Colors.red : Colors.grey),
                fontSize: 12,
              ),
            ),
          ],
        ),
        isThreeLine: true,
      ),
    );
  }

  Widget _buildOrdersTab() {
    if (_accountSummary == null) return const SizedBox.shrink();

    final orders = _accountSummary!.recentOrders;

    if (orders.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.receipt_long_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('尚無訂單記錄', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: orders.length,
      itemBuilder: (context, index) {
        return _buildOrderCard(orders[index]);
      },
    );
  }

  Widget _buildOrderCard(VirtualOrder order) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: order.isBuy ? Colors.green.withAlpha(51) : Colors.red.withAlpha(51),
          child: Icon(
            order.isBuy ? Icons.add : Icons.remove,
            color: order.isBuy ? Colors.green : Colors.red,
          ),
        ),
        title: Text(
          '${order.stockId} ${order.stockName ?? ""}',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(
          '${order.isBuy ? "買入" : "賣出"} ${order.quantity} 股 @ \$${order.price.toStringAsFixed(2)}',
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: order.isFilled ? Colors.green.withAlpha(26) : Colors.orange.withAlpha(26),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                order.isFilled ? '已成交' : '待處理',
                style: TextStyle(
                  fontSize: 12,
                  color: order.isFilled ? Colors.green : Colors.orange,
                ),
              ),
            ),
            if (order.createdAt != null)
              Text(
                '${order.createdAt!.month}/${order.createdAt!.day}',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w500,
              color: valueColor,
            ),
          ),
        ],
      ),
    );
  }

  void _showOrderDialog(BuildContext context, {String? orderType}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (dialogContext) => OrderDialog(
        initialOrderType: orderType,
        onSubmit: (stockId, type, quantity, price) async {
          Navigator.pop(dialogContext);
          try {
            final apiService = context.read<ApiService>();
            await apiService.placeOrder(
              stockId: stockId,
              orderType: type,
              quantity: quantity,
              price: price,
            );
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('${type == "BUY" ? "買入" : "賣出"}訂單已提交: $stockId $quantity 股 @ \$$price')),
              );
              await _loadData();
            }
          } catch (e) {
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('下單失敗: $e'), backgroundColor: Colors.red),
              );
            }
          }
        },
      ),
    );
  }

  void _showResetConfirmDialog() {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('重置帳戶'),
        content: const Text('確定要重置帳戶嗎？這將清除所有持倉和訂單，並將資金恢復到初始狀態。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(dialogContext);
              try {
                final apiService = context.read<ApiService>();
                await apiService.resetTradingAccount();
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('帳戶已重置')),
                  );
                  await _loadData();
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('重置失敗: $e'), backgroundColor: Colors.red),
                  );
                }
              }
            },
            child: const Text('確定', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  String _formatNumber(double value) {
    if (value >= 1000000) {
      return '${(value / 1000000).toStringAsFixed(2)}M';
    } else if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}K';
    }
    return value.toStringAsFixed(0);
  }
}

class OrderDialog extends StatefulWidget {
  final String? initialOrderType;
  final Function(String stockId, String orderType, int quantity, double price) onSubmit;

  const OrderDialog({
    super.key,
    this.initialOrderType,
    required this.onSubmit,
  });

  @override
  State<OrderDialog> createState() => _OrderDialogState();
}

class _OrderDialogState extends State<OrderDialog> {
  final _stockIdController = TextEditingController();
  final _quantityController = TextEditingController();
  final _priceController = TextEditingController();
  String _orderType = 'BUY';

  @override
  void initState() {
    super.initState();
    if (widget.initialOrderType != null) {
      _orderType = widget.initialOrderType!;
    }
  }

  @override
  void dispose() {
    _stockIdController.dispose();
    _quantityController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16,
        right: 16,
        top: 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                '下單',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // 買賣選擇
          Row(
            children: [
              Expanded(
                child: ChoiceChip(
                  label: const Text('買入'),
                  selected: _orderType == 'BUY',
                  selectedColor: Colors.green.withAlpha(51),
                  onSelected: (selected) {
                    if (selected) setState(() => _orderType = 'BUY');
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ChoiceChip(
                  label: const Text('賣出'),
                  selected: _orderType == 'SELL',
                  selectedColor: Colors.red.withAlpha(51),
                  onSelected: (selected) {
                    if (selected) setState(() => _orderType = 'SELL');
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _stockIdController,
            decoration: const InputDecoration(
              labelText: '股票代碼',
              border: OutlineInputBorder(),
              hintText: '例如: 2330',
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _quantityController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: '數量',
                    border: OutlineInputBorder(),
                    suffixText: '股',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _priceController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: '價格',
                    border: OutlineInputBorder(),
                    prefixText: '\$ ',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _submitOrder,
              style: ElevatedButton.styleFrom(
                backgroundColor: _orderType == 'BUY' ? Colors.green : Colors.red,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: Text(
                _orderType == 'BUY' ? '確認買入' : '確認賣出',
                style: const TextStyle(fontSize: 16),
              ),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  void _submitOrder() {
    final stockId = _stockIdController.text.trim();
    final quantity = int.tryParse(_quantityController.text) ?? 0;
    final price = double.tryParse(_priceController.text) ?? 0;

    if (stockId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請輸入股票代碼')),
      );
      return;
    }

    if (quantity <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請輸入有效數量')),
      );
      return;
    }

    if (price <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('請輸入有效價格')),
      );
      return;
    }

    widget.onSubmit(stockId, _orderType, quantity, price);
  }
}
