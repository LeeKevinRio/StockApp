import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/market_provider.dart';
import '../providers/watchlist_provider.dart';
import '../providers/notification_provider.dart';
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
      DashboardScreen(onTabChange: () => _switchToTab(1)),
      const WatchlistScreen(),
      const AISuggestionsScreen(),
      const AIChatScreen(),
      const AlertsScreen(),
    ];
  }

  void _switchToTab(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  void _onMarketChanged() {
    // Refresh watchlist when market changes
    final marketProvider = context.read<MarketProvider>();
    context.read<WatchlistProvider>().setMarketFilter(marketProvider.marketCode);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Consumer<MarketProvider>(
          builder: (context, marketProvider, child) {
            return Text('${marketProvider.marketDisplayName} AI 投資建議');
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
      bottomNavigationBar: Consumer<MarketProvider>(
        builder: (context, marketProvider, child) {
          final isUS = marketProvider.isUSMarket;
          return BottomNavigationBar(
            type: BottomNavigationBarType.fixed,
            currentIndex: _selectedIndex,
            selectedItemColor: isUS ? Colors.indigo : Colors.blue,
            unselectedItemColor: Colors.grey,
            onTap: (index) {
              setState(() {
                _selectedIndex = index;
              });
            },
            items: [
              BottomNavigationBarItem(
                icon: const Icon(Icons.dashboard),
                label: isUS ? 'Home' : '首頁',
              ),
              BottomNavigationBarItem(
                icon: const Icon(Icons.star),
                label: isUS ? 'Watchlist' : '自選股',
              ),
              BottomNavigationBarItem(
                icon: const Icon(Icons.lightbulb),
                label: isUS ? 'AI Tips' : 'AI 建議',
              ),
              BottomNavigationBarItem(
                icon: const Icon(Icons.chat),
                label: isUS ? 'AI Chat' : 'AI 問答',
              ),
              BottomNavigationBarItem(
                icon: const Icon(Icons.notifications),
                label: isUS ? 'Alerts' : '警示',
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
                  decoration: BoxDecoration(
                    color: marketProvider.isUSMarket ? Colors.indigo : Colors.blue,
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
            Consumer<MarketProvider>(
              builder: (context, marketProvider, child) {
                final isUS = marketProvider.isUSMarket;
                return Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.swap_horiz),
                      title: Text(isUS ? 'Paper Trading' : '模擬交易'),
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
                      title: Text(isUS ? 'Portfolio' : '投資組合'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/portfolio');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.grid_view),
                      title: Text(isUS ? 'Market Heatmap' : '市場熱力圖'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/market-heatmap');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.filter_list),
                      title: Text(isUS ? 'Stock Screener' : '股票篩選'),
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
                      title: Text(isUS ? 'Stock Compare' : '個股比較'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/stock-compare');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.calendar_month),
                      title: Text(isUS ? 'Calendar' : '財報/除息日曆'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/calendar');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.analytics),
                      title: Text(isUS ? 'AI Prediction Stats' : 'AI 預測準確度'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/prediction-stats');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.book),
                      title: Text(isUS ? 'Trading Diary' : '交易日記'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/trading-diary');
                      },
                    ),
                    const Divider(),
                    ListTile(
                      leading: const Icon(Icons.newspaper),
                      title: Text(isUS ? 'Financial News' : '財經新聞'),
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
                      title: Text(isUS ? 'Social Sentiment' : '社群情緒'),
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
                            title: Text(isUS ? 'Admin Panel' : '管理後台'),
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
                      leading: const Icon(Icons.privacy_tip),
                      title: Text(isUS ? 'Privacy Policy' : '隱私權政策'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/privacy');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.description),
                      title: Text(isUS ? 'Terms of Service' : '使用條款'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/terms');
                      },
                    ),
                    const Divider(),
                    ListTile(
                      leading: const Icon(Icons.logout),
                      title: Text(isUS ? 'Logout' : '登出'),
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
