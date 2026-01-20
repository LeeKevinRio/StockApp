import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'providers/auth_provider.dart';
import 'providers/watchlist_provider.dart';
import 'providers/ai_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/stock_search_screen.dart';
import 'screens/stock_detail_screen.dart';

void main() {
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
          create: (_) => WatchlistProvider(apiService),
        ),
        ChangeNotifierProvider(
          create: (_) => AIProvider(apiService),
        ),
      ],
      child: MaterialApp(
        title: '台股 AI 投資建議',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          useMaterial3: true,
        ),
        initialRoute: '/login',
        routes: {
          '/login': (context) => const LoginScreen(),
          '/home': (context) => const HomeScreen(),
          '/search': (context) => const StockSearchScreen(),
        },
        onGenerateRoute: (settings) {
          if (settings.name == '/stock-detail') {
            final stockId = settings.arguments as String;
            return MaterialPageRoute(
              builder: (context) => StockDetailScreen(stockId: stockId),
            );
          }
          return null;
        },
      ),
    );
  }
}
