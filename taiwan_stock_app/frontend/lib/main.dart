import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'models/user.dart';
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
import 'providers/portfolio_provider.dart';
import 'providers/connectivity_provider.dart';
import 'providers/broker_provider.dart';
import 'widgets/common/offline_banner.dart';
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
import 'screens/trading_diary_screen.dart';
import 'screens/privacy_policy_screen.dart';
import 'screens/terms_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/about_screen.dart';
import 'screens/broker_screen.dart';
import 'screens/broker_link_screen.dart';
import 'screens/ai_settings_screen.dart';
import 'screens/backtest_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 在 app 啟動前從 storage 完整恢復 auth 狀態（token + user），避免 Web 重整後遺失
  final apiService = ApiService();
  final authService = AuthService(apiService);
  final isLoggedIn = await authService.isLoggedIn();

  // 預載入 user 資料，確保 AuthProvider 一建立就有完整使用者狀態
  User? initialUser;
  if (isLoggedIn) {
    initialUser = await authService.getSavedUser();
  }

  runApp(MyApp(
    apiService: apiService,
    authService: authService,
    initialUser: initialUser,
  ));
}

class MyApp extends StatelessWidget {
  final ApiService apiService;
  final AuthService authService;
  final User? initialUser;

  const MyApp({
    super.key,
    required this.apiService,
    required this.authService,
    this.initialUser,
  });

  @override
  Widget build(BuildContext context) {

    return MultiProvider(
      providers: [
        Provider.value(value: apiService),
        ChangeNotifierProvider(
          create: (_) => AuthProvider(authService, initialUser: initialUser),
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
        ChangeNotifierProvider(
          create: (_) => PortfolioProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => ConnectivityProvider(),
        ),
        ChangeNotifierProvider(
          create: (_) => BrokerProvider(apiService),
        ),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, child) {
          return MaterialApp(
            title: '台股智慧助手',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.defaultTheme,
            themeMode: themeProvider.themeMode,
            debugShowCheckedModeBanner: false,
            initialRoute: '/splash',
            routes: {
              '/splash': (context) => const _SplashScreen(),
              '/login': (context) => const LoginScreen(),
              '/home': (context) => const OfflineBanner(child: HomeScreen()),
              '/search': (context) => const StockSearchScreen(),
              '/alerts': (context) => const AlertsScreen(),
              '/portfolio': (context) => const PortfolioScreen(),
              '/admin': (context) => const AdminScreen(),
              '/notifications': (context) => const NotificationCenterScreen(),
              '/prediction-stats': (context) => const PredictionStatsScreen(),
              '/market-heatmap': (context) => const MarketHeatmapScreen(),
              '/calendar': (context) => const CalendarScreen(),
              '/stock-compare': (context) => const StockCompareScreen(),
              '/trading-diary': (context) => const TradingDiaryScreen(),
              '/backtest': (context) => const BacktestScreen(),
              '/privacy': (context) => const PrivacyPolicyScreen(),
              '/terms': (context) => const TermsScreen(),
              '/settings': (context) => const SettingsScreen(),
              '/onboarding': (context) => const OnboardingScreen(),
              '/about': (context) => const AboutScreen(),
              '/broker': (context) => const BrokerScreen(),
              '/broker-link': (context) => const BrokerLinkScreen(),
              '/ai-settings': (context) => const AISettingsScreen(),
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

/// 啟動畫面：檢查已儲存的登入狀態，自動跳轉
class _SplashScreen extends StatefulWidget {
  const _SplashScreen();

  @override
  State<_SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<_SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkAuth());
  }

  Future<void> _checkAuth() async {
    // 首次啟動導向 Onboarding（含投資免責聲明，金融類 App Store 要求）
    final prefs = await SharedPreferences.getInstance();
    final hasOnboarded = prefs.getBool('onboarding_completed') ?? false;

    if (!mounted) return;

    if (!hasOnboarded) {
      await prefs.setBool('onboarding_completed', true);
      Navigator.of(context).pushReplacementNamed('/onboarding');
      return;
    }

    final authProvider = context.read<AuthProvider>();

    if (authProvider.isAuthenticated) {
      // main() 已預載入 cached user，向伺服器驗證 token 是否仍有效
      final stillValid = await authProvider.refreshUser();
      if (!mounted) return;

      if (stillValid && authProvider.isAuthenticated) {
        Navigator.of(context).pushReplacementNamed('/home');
      } else {
        // Token 已過期，需重新登入
        Navigator.of(context).pushReplacementNamed('/login');
      }
      return;
    }

    // 無 cached user，走完整的 auth check
    final isLoggedIn = await authProvider.checkAuth();

    if (!mounted) return;

    if (isLoggedIn) {
      Navigator.of(context).pushReplacementNamed('/home');
    } else {
      Navigator.of(context).pushReplacementNamed('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Semantics(
              label: '台股智慧助手載入中',
              excludeSemantics: true,
              child: Icon(
                Icons.show_chart,
                size: 64,
                color: Theme.of(context).primaryColor,
              ),
            ),
            const SizedBox(height: 16),
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(
              '台股智慧助手',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ],
        ),
      ),
    );
  }
}
