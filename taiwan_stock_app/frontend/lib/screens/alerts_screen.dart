import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/alert_provider.dart';
import '../providers/watchlist_provider.dart';
import '../models/price_alert.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AlertProvider>().refresh();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('價格警示'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '進行中'),
            Tab(text: '已觸發'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<AlertProvider>().refresh(),
          ),
        ],
      ),
      body: Consumer<AlertProvider>(
        builder: (context, alertProvider, child) {
          if (alertProvider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (alertProvider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '載入失敗: ${alertProvider.error}',
                    style: const TextStyle(color: Colors.red),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => alertProvider.refresh(),
                    child: const Text('重試'),
                  ),
                ],
              ),
            );
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildActiveAlerts(alertProvider),
              _buildTriggeredAlerts(alertProvider),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateAlertDialog(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildActiveAlerts(AlertProvider provider) {
    final activeAlerts = provider.activeAlerts;

    if (activeAlerts.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.notifications_off, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('尚無進行中的警示', style: TextStyle(color: Colors.grey)),
            SizedBox(height: 8),
            Text('點擊右下角按鈕新增警示', style: TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.refresh(),
      child: ListView.builder(
        itemCount: activeAlerts.length,
        itemBuilder: (context, index) {
          return _buildAlertCard(activeAlerts[index]);
        },
      ),
    );
  }

  Widget _buildTriggeredAlerts(AlertProvider provider) {
    final triggeredAlerts =
        provider.alerts.where((a) => a.isTriggered).toList();

    if (triggeredAlerts.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle_outline, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('尚無已觸發的警示', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.refresh(),
      child: ListView.builder(
        itemCount: triggeredAlerts.length,
        itemBuilder: (context, index) {
          return _buildAlertCard(triggeredAlerts[index], isTriggered: true);
        },
      ),
    );
  }

  Widget _buildAlertCard(PriceAlert alert, {bool isTriggered = false}) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: isTriggered
              ? Colors.orange
              : (alert.isActive ? Colors.green : Colors.grey),
          child: Icon(
            isTriggered
                ? Icons.notifications_active
                : (alert.isActive ? Icons.notifications : Icons.notifications_off),
            color: Colors.white,
          ),
        ),
        title: Text(
          '${alert.stockId} ${alert.stockName ?? ""}',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(alert.displayText),
            if (isTriggered && alert.triggeredAt != null)
              Text(
                '觸發時間: ${_formatDateTime(alert.triggeredAt!)}',
                style: const TextStyle(fontSize: 12, color: Colors.orange),
              ),
            if (isTriggered && alert.triggeredPrice != null)
              Text(
                '觸發價格: \$${alert.triggeredPrice!.toStringAsFixed(2)}',
                style: const TextStyle(fontSize: 12, color: Colors.orange),
              ),
            if (alert.notes != null && alert.notes!.isNotEmpty)
              Text(
                '備註: ${alert.notes}',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) => _handleAlertAction(value, alert),
          itemBuilder: (context) => [
            if (!isTriggered)
              PopupMenuItem(
                value: 'toggle',
                child: Text(alert.isActive ? '暫停' : '啟用'),
              ),
            if (isTriggered)
              const PopupMenuItem(
                value: 'reset',
                child: Text('重設'),
              ),
            const PopupMenuItem(
              value: 'delete',
              child: Text('刪除', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
        isThreeLine: true,
      ),
    );
  }

  void _handleAlertAction(String action, PriceAlert alert) async {
    final provider = context.read<AlertProvider>();

    try {
      switch (action) {
        case 'toggle':
          await provider.toggleAlert(alert.id);
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(alert.isActive ? '警示已暫停' : '警示已啟用')),
            );
          }
          break;
        case 'reset':
          await provider.resetAlert(alert.id);
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('警示已重設')),
            );
          }
          break;
        case 'delete':
          final confirm = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text('確認刪除'),
              content: const Text('確定要刪除此警示嗎？'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('取消'),
                ),
                TextButton(
                  onPressed: () => Navigator.pop(context, true),
                  child: const Text('刪除', style: TextStyle(color: Colors.red)),
                ),
              ],
            ),
          );
          if (confirm == true) {
            await provider.deleteAlert(alert.id);
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('警示已刪除')),
              );
            }
          }
          break;
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('操作失敗: $e')),
        );
      }
    }
  }

  void _showCreateAlertDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => const CreateAlertDialog(),
    );
  }

  String _formatDateTime(DateTime dt) {
    return '${dt.year}/${dt.month.toString().padLeft(2, '0')}/${dt.day.toString().padLeft(2, '0')} '
        '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}

class CreateAlertDialog extends StatefulWidget {
  const CreateAlertDialog({super.key});

  @override
  State<CreateAlertDialog> createState() => _CreateAlertDialogState();
}

class _CreateAlertDialogState extends State<CreateAlertDialog> {
  final _formKey = GlobalKey<FormState>();
  String? _selectedStockId;
  String _alertType = 'ABOVE';
  final _priceController = TextEditingController();
  final _percentController = TextEditingController();
  final _notesController = TextEditingController();
  bool _notifyPush = true;
  bool _notifyEmail = false;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _priceController.dispose();
    _percentController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  bool get _isPriceType => _alertType == 'ABOVE' || _alertType == 'BELOW';

  @override
  Widget build(BuildContext context) {
    final watchlistProvider = context.watch<WatchlistProvider>();

    return AlertDialog(
      title: const Text('新增價格警示'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(
                  labelText: '選擇股票',
                  border: OutlineInputBorder(),
                ),
                items: watchlistProvider.items.map((item) {
                  return DropdownMenuItem(
                    value: item.stockId,
                    child: Text('${item.stockId} ${item.name}'),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _selectedStockId = value;
                  });
                },
                validator: (value) {
                  if (value == null) return '請選擇股票';
                  return null;
                },
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _alertType,
                decoration: const InputDecoration(
                  labelText: '警示類型',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'ABOVE', child: Text('價格高於')),
                  DropdownMenuItem(value: 'BELOW', child: Text('價格低於')),
                  DropdownMenuItem(value: 'PERCENT_UP', child: Text('漲幅達到')),
                  DropdownMenuItem(value: 'PERCENT_DOWN', child: Text('跌幅達到')),
                ],
                onChanged: (value) {
                  setState(() {
                    _alertType = value!;
                  });
                },
              ),
              const SizedBox(height: 16),
              if (_isPriceType)
                TextFormField(
                  controller: _priceController,
                  decoration: const InputDecoration(
                    labelText: '目標價格',
                    border: OutlineInputBorder(),
                    prefixText: '\$ ',
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (_isPriceType && (value == null || value.isEmpty)) {
                      return '請輸入目標價格';
                    }
                    if (value != null &&
                        value.isNotEmpty &&
                        double.tryParse(value) == null) {
                      return '請輸入有效數字';
                    }
                    return null;
                  },
                )
              else
                TextFormField(
                  controller: _percentController,
                  decoration: const InputDecoration(
                    labelText: '百分比閾值',
                    border: OutlineInputBorder(),
                    suffixText: '%',
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (!_isPriceType && (value == null || value.isEmpty)) {
                      return '請輸入百分比';
                    }
                    if (value != null &&
                        value.isNotEmpty &&
                        double.tryParse(value) == null) {
                      return '請輸入有效數字';
                    }
                    return null;
                  },
                ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _notesController,
                decoration: const InputDecoration(
                  labelText: '備註（選填）',
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              const Text('通知方式:', style: TextStyle(fontWeight: FontWeight.bold)),
              CheckboxListTile(
                title: const Text('推送通知'),
                value: _notifyPush,
                onChanged: (value) {
                  setState(() {
                    _notifyPush = value ?? true;
                  });
                },
                contentPadding: EdgeInsets.zero,
              ),
              CheckboxListTile(
                title: const Text('Email 通知'),
                value: _notifyEmail,
                onChanged: (value) {
                  setState(() {
                    _notifyEmail = value ?? false;
                  });
                },
                contentPadding: EdgeInsets.zero,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isSubmitting ? null : () => Navigator.pop(context),
          child: const Text('取消'),
        ),
        ElevatedButton(
          onPressed: _isSubmitting ? null : _submitAlert,
          child: _isSubmitting
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('建立'),
        ),
      ],
    );
  }

  void _submitAlert() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSubmitting = true;
    });

    try {
      await context.read<AlertProvider>().createAlert(
            stockId: _selectedStockId!,
            alertType: _alertType,
            targetPrice:
                _isPriceType ? double.tryParse(_priceController.text) : null,
            percentThreshold:
                !_isPriceType ? double.tryParse(_percentController.text) : null,
            notifyPush: _notifyPush,
            notifyEmail: _notifyEmail,
            notes: _notesController.text.isNotEmpty
                ? _notesController.text
                : null,
          );

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('警示已建立')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('建立失敗: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }
}
