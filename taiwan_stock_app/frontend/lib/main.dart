import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'providers/auth_provider.dart';
import 'providers/watchlist_provider.dart';
import 'providers/ai_provider.dart';
import 'providers/alert_provider.dart';
import 'providers/app_state_provider.dart';
import 'providers/theme_provider.dart';
import 'providers/market_provider.dart';
import 'providers/notification_provider.dart';
import 'providers/dashboard_provider.dart';
import 'screens/notification_center_screen.dart';
import 'config/app_theme.dart';
import 'utils/page_transitions.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/stock_search_screen.dart';
import 'screens/stock_detail_screen.dart';
import 'screens/alerts_screen.dart';
import 'screens/portfolio_screen.dart';
import 'screens/admin_screen.dart';
import 'screens/prediction_stats_screen.dart';
import 'screens/market_heatmap_screen.dart';
import 'screens/calendar_screen.dart';
import 'screens/stock_compare_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final apiService = ApiService();
    final authService = AuthService(apiService);

    return MultiProvider(
      providers: [
        Provider.value(value: apiService),
        ChangeNotifierProvider(
          create: (_) => AuthProvider(authService),
        ),
        ChangeNotifierProvider(
          create: (_) => MarketProvider(),
        ),
        ChangeNotifierProvider(
          create: (_) => WatchlistProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => AIProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => AlertProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => AppStateProvider(),
        ),
        ChangeNotifierProvider(
          create: (_) => ThemeProvider(),
        ),
        ChangeNotifierProvider(
          create: (_) => NotificationProvider(),
        ),
        ChangeNotifierProvider(
          create: (_) => DashboardProvider(apiService),
        ),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, child) {
          return MaterialApp(
            title: 'AI 投資建議',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: themeProvider.themeMode,
            debugShowCheckedModeBanner: false,
            initialRoute: '/login',
            routes: {
              '/login': (context) => const LoginScreen(),
              '/home': (context) => const HomeScreen(),
              '/search': (context) => const StockSearchScreen(),
              '/alerts': (context) => const AlertsScreen(),
              '/portfolio': (context) => const PortfolioScreen(),
              '/admin': (context) => const AdminScreen(),
              '/notifications': (context) => const NotificationCenterScreen(),
              '/prediction-stats': (context) => const PredictionStatsScreen(),
              '/market-heatmap': (context) => const MarketHeatmapScreen(),
              '/calendar': (context) => const CalendarScreen(),
              '/stock-compare': (context) => const StockCompareScreen(),
            },
            onGenerateRoute: (settings) {
              if (settings.name == '/stock-detail') {
                final args = settings.arguments;
                String stockId;
                String market = 'TW';

                if (args is Map<String, dynamic>) {
                  stockId = args['stockId'] as String;
                  market = args['market'] as String? ?? 'TW';
                } else {
                  stockId = args as String;
                }

                return AppPageRoute.slide(
                  StockDetailScreen(stockId: stockId, market: market),
                  settings: settings,
                );
              }
              return null;
            },
          );
        },
      ),
    );
  }
}
