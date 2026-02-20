import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/broker_provider.dart';
import '../models/broker.dart';

class BrokerScreen extends StatefulWidget {
  const BrokerScreen({super.key});

  @override
  State<BrokerScreen> createState() => _BrokerScreenState();
}

class _BrokerScreenState extends State<BrokerScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<BrokerProvider>().loadStatus();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('券商持倉'),
        actions: [
          Consumer<BrokerProvider>(
            builder: (context, provider, _) {
              if (!provider.isLinked) return const SizedBox.shrink();
              return IconButton(
                icon: const Icon(Icons.link_off),
                tooltip: '解除連結',
                onPressed: () => _confirmUnlink(context, provider),
              );
            },
          ),
        ],
      ),
      body: Consumer<BrokerProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (!provider.isLinked) {
            return _buildUnlinkedView(context);
          }

          return _buildPositionsView(context, provider);
        },
      ),
    );
  }

  Widget _buildUnlinkedView(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.account_balance, size: 80, color: Colors.grey.shade400),
            const SizedBox(height: 16),
            Text('尚未連結券商帳戶', style: theme.textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(
              '連結 Firstrade 帳戶，自動同步美股持倉。',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey),
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              icon: const Icon(Icons.link),
              label: const Text('連結 Firstrade'),
              onPressed: () => Navigator.pushNamed(context, '/broker-link'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPositionsView(BuildContext context, BrokerProvider provider) {
    final theme = Theme.of(context);
    final positions = provider.positions;

    return RefreshIndicator(
      onRefresh: provider.syncPositions,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 帳戶摘要
          _buildSummaryCard(theme, provider),
          const SizedBox(height: 16),

          // 同步狀態
          if (provider.isSyncing)
            const Padding(
              padding: EdgeInsets.only(bottom: 8),
              child: LinearProgressIndicator(),
            ),

          // 持倉列表
          if (positions.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 32),
              child: Center(
                child: Text('無持倉資料，下拉刷新同步', style: theme.textTheme.bodyMedium),
              ),
            )
          else
            ...positions.map((p) => _buildPositionCard(theme, p)),

          // 同步按鈕
          const SizedBox(height: 16),
          OutlinedButton.icon(
            icon: const Icon(Icons.sync),
            label: const Text('手動同步'),
            onPressed: provider.isSyncing ? null : () => provider.syncPositions(),
          ),

          if (provider.error != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                provider.error!,
                style: const TextStyle(color: Colors.red, fontSize: 12),
                textAlign: TextAlign.center,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(ThemeData theme, BrokerProvider provider) {
    final pnl = provider.totalUnrealizedPnl;
    final pnlColor = pnl >= 0 ? Colors.green : Colors.red;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Firstrade', style: theme.textTheme.titleMedium),
                if (provider.account.accountNumber != null)
                  Text(
                    '帳號: ${provider.account.accountNumber}',
                    style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
              ],
            ),
            const Divider(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('總市值', style: theme.textTheme.bodySmall),
                    Text(
                      '\$${provider.totalMarketValue.toStringAsFixed(2)}',
                      style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('未實現損益', style: theme.textTheme.bodySmall),
                    Text(
                      '${pnl >= 0 ? '+' : ''}\$${pnl.toStringAsFixed(2)}',
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: pnlColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            if (provider.account.lastSynced != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  '最後同步：${_formatTime(provider.account.lastSynced!)}',
                  style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPositionCard(ThemeData theme, BrokerPosition pos) {
    final pnlColor = pos.isProfit
        ? Colors.green
        : pos.isLoss
            ? Colors.red
            : Colors.grey;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(pos.symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text('${pos.quantity.toStringAsFixed(2)} 股 · 成本 \$${pos.avgCost.toStringAsFixed(2)}'),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '\$${pos.marketValue.toStringAsFixed(2)}',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              '${pos.unrealizedPnl >= 0 ? '+' : ''}\$${pos.unrealizedPnl.toStringAsFixed(2)}',
              style: TextStyle(color: pnlColor, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmUnlink(BuildContext context, BrokerProvider provider) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('解除連結'),
        content: const Text('確定要解除 Firstrade 帳戶連結嗎？\n\n所有已同步的持倉資料將被清除。'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await provider.unlinkAccount();
            },
            child: const Text('確認解除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime dt) {
    return '${dt.year}/${dt.month.toString().padLeft(2, '0')}/${dt.day.toString().padLeft(2, '0')} '
        '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}
