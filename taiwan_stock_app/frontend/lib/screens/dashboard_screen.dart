import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/dashboard_provider.dart';
import '../providers/market_provider.dart';
import '../providers/notification_provider.dart';
import '../widgets/dashboard/market_overview_card.dart';
import '../widgets/dashboard/watchlist_summary_card.dart';
import '../widgets/dashboard/ai_picks_card.dart';
import '../widgets/dashboard/ai_discovery_card.dart';
import '../widgets/dashboard/quick_actions_card.dart';
import '../widgets/common/skeleton_loader.dart';

/// Dashboard 儀表板頁面
class DashboardScreen extends StatefulWidget {
  final void Function(int tabIndex)? onTabChange;

  const DashboardScreen({
    super.key,
    this.onTabChange,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    // 延遲加載以避免在 build 中調用
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadData();
    });
  }

  void _loadData() {
    final dashboardProvider = context.read<DashboardProvider>();
    final marketProvider = context.read<MarketProvider>();

    dashboardProvider.setMarket(marketProvider.marketCode);
    dashboardProvider.loadDashboard();

    // 初始化通知服務
    context.read<NotificationProvider>().initialize();
  }

  Future<void> _refresh() async {
    await context.read<DashboardProvider>().refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer2<DashboardProvider, MarketProvider>(
      builder: (context, dashboardProvider, marketProvider, child) {
        // 市場變更時重新加載
        if (dashboardProvider.currentMarket != marketProvider.marketCode) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            dashboardProvider.setMarket(marketProvider.marketCode);
          });
        }

        return RefreshIndicator(
          onRefresh: _refresh,
          child: dashboardProvider.isLoading && !dashboardProvider.hasData
              ? _buildSkeleton()
              : _buildContent(context, dashboardProvider, marketProvider),
        );
      },
    );
  }

  Widget _buildSkeleton() {
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // 市場概況骨架
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SkeletonLoader(width: 100, height: 16),
                  const SizedBox(height: 16),
                  SkeletonLoader(width: 180, height: 32),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: List.generate(4, (_) =>
                      SkeletonLoader(width: 60, height: 40),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          // 快捷操作骨架
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: List.generate(4, (_) =>
                  Column(
                    children: [
                      SkeletonLoader(width: 48, height: 48, borderRadius: 12),
                      const SizedBox(height: 8),
                      SkeletonLoader(width: 48, height: 12),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          // 自選股摘要骨架
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SkeletonLoader(width: 100, height: 16),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      SkeletonLoader(width: 80, height: 80, borderRadius: 40),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          children: List.generate(3, (_) =>
                            Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: SkeletonLoader(height: 20),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          // AI 精選骨架
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SkeletonLoader(width: 100, height: 16),
                  const SizedBox(height: 12),
                  ...List.generate(3, (_) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: SkeletonLoader(height: 50),
                  )),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    DashboardProvider dashboardProvider,
    MarketProvider marketProvider,
  ) {
    final data = dashboardProvider.dashboardData;
    final isUS = marketProvider.isUSMarket;

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 市場概況卡片
          if (data?.marketOverview != null)
            MarketOverviewCard(
              data: data!.marketOverview,
            ),

          const SizedBox(height: 12),

          // 快捷操作
          QuickActionsCard(
            actions: QuickActionsCard.defaultActions,
            onActionTap: (action) => _handleQuickAction(context, action),
          ),

          const SizedBox(height: 12),

          // 警報狀態
          if (data?.alertSummary != null)
            AlertStatusWidget(
              activeCount: data!.alertSummary.activeCount,
              triggeredToday: data.alertSummary.triggeredToday,
              onTap: () => _navigateToAlerts(context),
            ),

          const SizedBox(height: 12),

          // 自選股摘要卡片
          if (data?.watchlistSummary != null)
            WatchlistSummaryCard(
              data: data!.watchlistSummary,
              onTap: () => _navigateToWatchlist(context),
            ),

          const SizedBox(height: 12),

          // AI 精選推薦卡片（自選股分析）
          AIPicksCard(
            picks: dashboardProvider.aiPicks,
            isLoading: dashboardProvider.isLoadingAI,
            onViewAll: () => _navigateToAISuggestions(context),
            onPickTap: (pick) => _navigateToStock(context, pick.stockId, pick.market),
          ),

          const SizedBox(height: 12),

          // AI 潛力股掃描卡片（全市場掃描）
          AIDiscoveryCard(
            picks: dashboardProvider.discoveryPicks,
            marketSummary: dashboardProvider.discoveryMarketSummary,
            isLoading: dashboardProvider.isLoadingDiscovery,
            hasScanned: dashboardProvider.hasScannedDiscovery,
            onScan: () => dashboardProvider.scanDiscovery(),
            onRefresh: () => dashboardProvider.scanDiscovery(refresh: true),
            onPickTap: (pick) => _navigateToStock(context, pick.stockId, pick.market),
          ),

          const SizedBox(height: 24),

          // 底部提示
          Center(
            child: Text(
              isUS ? 'US Market Data' : '台股市場數據',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  void _handleQuickAction(BuildContext context, QuickActionItem action) {
    if (action.route == '/home' && action.arguments?['tab'] != null) {
      widget.onTabChange?.call(action.arguments!['tab'] as int);
    } else {
      Navigator.pushNamed(context, action.route, arguments: action.arguments);
    }
  }

  void _navigateToWatchlist(BuildContext context) {
    widget.onTabChange?.call(1); // Tab 1: 自選股
  }

  void _navigateToAISuggestions(BuildContext context) {
    widget.onTabChange?.call(2); // Tab 2: AI 建議
  }

  void _navigateToAlerts(BuildContext context) {
    Navigator.pushNamed(context, '/alerts');
  }

  void _navigateToStock(BuildContext context, String stockId, String market) {
    Navigator.pushNamed(
      context,
      '/stock-detail',
      arguments: {'stockId': stockId, 'market': market},
    );
  }
}
