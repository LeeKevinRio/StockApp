import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/market_provider.dart';
import '../providers/locale_provider.dart';
import '../providers/watchlist_provider.dart';
import '../providers/dashboard_provider.dart';
import '../providers/notification_provider.dart';
import '../providers/theme_provider.dart';
import '../widgets/market_switcher.dart';
import '../widgets/notification/notification_badge.dart';
import 'dashboard_screen.dart';
import 'watchlist_screen.dart';
import 'ai_chat_screen.dart';
import 'ai_suggestions_screen.dart';
import 'alerts_screen.dart';
import 'trading_screen.dart';
import 'news_screen.dart';
import 'social_screen.dart';
import 'screener_screen.dart';
import 'industry_trends_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  late final List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    _screens = [
      DashboardScreen(onTabChange: (index) => _switchToTab(index)),
      const WatchlistScreen(),
      const AISuggestionsScreen(),
      // AIChatScreen 功能保留，暫時從底部導航隱藏
      const AlertsScreen(),
    ];

    // Auth 安全守衛：若使用者狀態遺失（不正常情況），嘗試恢復或導回登入頁
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _ensureAuth();
    });
  }

  Future<void> _ensureAuth() async {
    final authProvider = context.read<AuthProvider>();
    if (!authProvider.isAuthenticated) {
      // 嘗試從 storage 恢復
      final restored = await authProvider.checkAuth();
      if (!restored && mounted) {
        Navigator.of(context).pushReplacementNamed('/login');
      }
    }
  }

  void _switchToTab(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  void _onMarketChanged() {
    final marketProvider = context.read<MarketProvider>();
    final marketCode = marketProvider.marketCode;
    // 切換市場時同步更新所有相關 Provider
    context.read<WatchlistProvider>().setMarketFilter(marketCode);
    context.read<DashboardProvider>().setMarket(marketCode);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Consumer2<MarketProvider, LocaleProvider>(
          builder: (context, marketProvider, locale, child) {
            final marketLabel = marketProvider.isUSMarket
                ? locale.tr('美股', 'US')
                : locale.tr('台股', 'TW');
            return Text(locale.tr(
              '$marketLabel AI 投資建議',
              '$marketLabel AI Insights',
            ));
          },
        ),
        actions: [
          NotificationIconButton(
            onPressed: () {
              Navigator.pushNamed(context, '/notifications');
            },
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: CompactMarketSwitcher(
              onMarketChanged: _onMarketChanged,
            ),
          ),
        ],
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: Consumer<LocaleProvider>(
        builder: (context, locale, child) {
          return BottomNavigationBar(
            type: BottomNavigationBarType.fixed,
            currentIndex: _selectedIndex,
            selectedItemColor: Theme.of(context).colorScheme.primary,
            unselectedItemColor: Theme.of(context).textTheme.bodySmall?.color,
            onTap: (index) {
              setState(() {
                _selectedIndex = index;
              });
            },
            items: [
              BottomNavigationBarItem(
                icon: const Icon(Icons.dashboard),
                label: locale.tr('首頁', 'Home'),
              ),
              BottomNavigationBarItem(
                icon: const Icon(Icons.star),
                label: locale.tr('自選股', 'Watchlist'),
              ),
              BottomNavigationBarItem(
                icon: const Icon(Icons.lightbulb),
                label: locale.tr('AI 建議', 'AI Tips'),
              ),
              BottomNavigationBarItem(
                icon: const Icon(Icons.notifications),
                label: locale.tr('警示', 'Alerts'),
              ),
            ],
          );
        },
      ),
      drawer: Drawer(
        child: ListView(
          children: [
            Consumer2<MarketProvider, AuthProvider>(
              builder: (context, marketProvider, authProvider, child) {
                final user = authProvider.user;
                return DrawerHeader(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFF1B5E20), Color(0xFF2E7D32)],
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 24,
                            backgroundColor: Colors.white24,
                            child: user?.avatarUrl != null && user!.avatarUrl!.isNotEmpty
                                ? ClipOval(
                                    child: Image.network(
                                      user.avatarUrl!,
                                      width: 48,
                                      height: 48,
                                      fit: BoxFit.cover,
                                      errorBuilder: (context, error, stackTrace) {
                                        return const Icon(Icons.person, color: Colors.white);
                                      },
                                    ),
                                  )
                                : const Icon(Icons.person, color: Colors.white),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  user?.displayName ?? user?.email ?? '',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 2,
                                      ),
                                      decoration: BoxDecoration(
                                        color: user?.isPro == true
                                            ? Colors.amber
                                            : Colors.white24,
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Text(
                                        user?.isPro == true ? 'PRO' : 'FREE',
                                        style: TextStyle(
                                          color: user?.isPro == true
                                              ? Colors.black
                                              : Colors.white,
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    if (user?.isAdmin == true) ...[
                                      const SizedBox(width: 4),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 2,
                                        ),
                                        decoration: BoxDecoration(
                                          color: Colors.red,
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: const Text(
                                          'ADMIN',
                                          style: TextStyle(
                                            color: Colors.white,
                                            fontSize: 10,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      MarketSwitcher(
                        onMarketChanged: _onMarketChanged,
                      ),
                    ],
                  ),
                );
              },
            ),
            Consumer<LocaleProvider>(
              builder: (context, locale, child) {
                return Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.swap_horiz),
                      title: Text(locale.tr('模擬交易', 'Paper Trading')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const TradingScreen(),
                          ),
                        );
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.pie_chart),
                      title: Text(locale.tr('投資組合', 'Portfolio')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/portfolio');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.grid_view),
                      title: Text(locale.tr('市場熱力圖', 'Market Heatmap')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/market-heatmap');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.filter_list),
                      title: Text(locale.tr('股票篩選', 'Stock Screener')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ScreenerScreen(),
                          ),
                        );
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.compare_arrows),
                      title: Text(locale.tr('個股比較', 'Stock Compare')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/stock-compare');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.calendar_month),
                      title: Text(locale.tr('財報/除息日曆', 'Calendar')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/calendar');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.analytics),
                      title: Text(locale.tr('AI 預測準確度', 'AI Prediction Stats')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/prediction-stats');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.book),
                      title: Text(locale.tr('交易日記', 'Trading Diary')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/trading-diary');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.speed),
                      title: Text(locale.tr('策略回測', 'Strategy Backtest')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/backtest');
                      },
                    ),
                    const Divider(),
                    ListTile(
                      leading: const Icon(Icons.newspaper),
                      title: Text(locale.tr('財經新聞', 'Financial News')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const NewsScreen(),
                          ),
                        );
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.forum),
                      title: Text(locale.tr('社群情緒', 'Social Sentiment')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const SocialScreen(),
                          ),
                        );
                      },
                    ),
                    const Divider(),
                    Consumer<AuthProvider>(
                      builder: (context, authProvider, child) {
                        if (authProvider.isAdmin) {
                          return ListTile(
                            leading: const Icon(Icons.admin_panel_settings),
                            title: Text(locale.tr('管理後台', 'Admin Panel')),
                            onTap: () {
                              Navigator.pop(context);
                              Navigator.pushNamed(context, '/admin');
                            },
                          );
                        }
                        return const SizedBox.shrink();
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.trending_up),
                      title: Text(locale.tr('產業趨勢', 'Industry Trends')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const IndustryTrendsScreen(),
                          ),
                        );
                      },
                    ),
                    Consumer<ThemeProvider>(
                      builder: (context, themeProvider, child) {
                        return ListTile(
                          leading: Icon(themeProvider.themeModeIcon),
                          title: Text(themeProvider.themeModeLabel),
                          subtitle: Text(locale.tr('點擊切換主題', 'Tap to toggle theme')),
                          onTap: () {
                            themeProvider.toggleTheme();
                          },
                        );
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.settings),
                      title: Text(locale.tr('設定', 'Settings')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/settings');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.privacy_tip),
                      title: Text(locale.tr('隱私權政策', 'Privacy Policy')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/privacy');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.description),
                      title: Text(locale.tr('使用條款', 'Terms of Service')),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/terms');
                      },
                    ),
                    const Divider(),
                    ListTile(
                      leading: const Icon(Icons.logout),
                      title: Text(locale.tr('登出', 'Logout')),
                      onTap: () async {
                        await context.read<AuthProvider>().logout();
                        if (context.mounted) {
                          Navigator.of(context).pushReplacementNamed('/login');
                        }
                      },
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
