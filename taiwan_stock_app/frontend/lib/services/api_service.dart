import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/stock.dart';
import '../models/watchlist_item.dart';
import '../models/ai_suggestion.dart';
import '../models/stock_history.dart';
import '../models/indicator_data.dart';
import '../models/portfolio.dart';
import '../models/trading.dart';
import '../models/social_sentiment.dart';
import '../models/fundamental.dart';
import '../models/screen_criteria.dart';

class ApiService {
  final String baseUrl;
  String? _authToken;

  ApiService({String? baseUrl}) : baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  void setAuthToken(String token) {
    _authToken = token;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  // ==================== 認證相關 ====================

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> register(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 股票相關 ====================

  Future<List<Stock>> searchStocks(String query, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/search?q=$query&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => Stock.fromJson(e)).toList();
  }

  Future<StockPrice> getStockPrice(String stockId, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/price?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return StockPrice.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> getStockDetail(String stockId, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<List<StockHistory>> getStockHistory(
    String stockId, {
    int days = 60,
    String period = 'day',
    String market = 'TW',
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/history?days=$days&period=$period&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => StockHistory.fromJson(e)).toList();
  }

  Future<List<Map<String, dynamic>>> getUSStockNews(String stockId, {int limit = 10}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/news?market=US&limit=$limit'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.cast<Map<String, dynamic>>();
  }

  // ==================== 自選股相關 ====================

  Future<List<WatchlistItem>> getWatchlist({String? market}) async {
    final query = market != null ? '?market=$market' : '';
    final response = await http.get(
      Uri.parse('$baseUrl/api/watchlist$query'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => WatchlistItem.fromJson(e)).toList();
  }

  Future<void> addToWatchlist(String stockId, {String? notes, String market = 'TW'}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/watchlist'),
      headers: _headers,
      body: jsonEncode({
        'stock_id': stockId,
        'notes': notes,
        'market': market,
      }),
    );
    _checkResponse(response);
  }

  Future<void> removeFromWatchlist(String stockId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/watchlist/$stockId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  // ==================== AI 相關 ====================

  Future<List<AISuggestion>> getAISuggestions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/suggestions'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => AISuggestion.fromJson(e)).toList();
  }

  Future<AISuggestion> getStockSuggestion(String stockId, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/suggestions/$stockId?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return AISuggestion.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> chat(String message, {String? stockId}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/ai/chat'),
      headers: _headers,
      body: jsonEncode({
        'message': message,
        if (stockId != null) 'stock_id': stockId,
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 價格警示相關 ====================

  Future<List<Map<String, dynamic>>> getAlerts() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/alerts'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> createAlert({
    required String stockId,
    required String alertType,
    double? targetPrice,
    double? percentThreshold,
    bool notifyPush = true,
    bool notifyEmail = false,
    String? notes,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/alerts'),
      headers: _headers,
      body: jsonEncode({
        'stock_id': stockId,
        'alert_type': alertType,
        if (targetPrice != null) 'target_price': targetPrice,
        if (percentThreshold != null) 'percent_threshold': percentThreshold,
        'notify_push': notifyPush,
        'notify_email': notifyEmail,
        if (notes != null) 'notes': notes,
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updateAlert(
    int alertId, {
    String? alertType,
    double? targetPrice,
    double? percentThreshold,
    bool? notifyPush,
    bool? notifyEmail,
    String? notes,
  }) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/alerts/$alertId'),
      headers: _headers,
      body: jsonEncode({
        if (alertType != null) 'alert_type': alertType,
        if (targetPrice != null) 'target_price': targetPrice,
        if (percentThreshold != null) 'percent_threshold': percentThreshold,
        if (notifyPush != null) 'notify_push': notifyPush,
        if (notifyEmail != null) 'notify_email': notifyEmail,
        if (notes != null) 'notes': notes,
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<void> deleteAlert(int alertId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/alerts/$alertId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  Future<Map<String, dynamic>> toggleAlert(int alertId) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/alerts/$alertId/toggle'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> resetAlert(int alertId) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/alerts/$alertId/reset'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<List<Map<String, dynamic>>> getTriggeredAlerts() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/alerts/triggered/list'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.cast<Map<String, dynamic>>();
  }

  // ==================== 技術指標相關 ====================

  Future<AllIndicatorsData> getAllIndicators(String stockId, {int days = 60, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/indicators/all?days=$days&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return AllIndicatorsData.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> getRSI(String stockId, {int period = 14, int days = 60, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/indicators/rsi?period=$period&days=$days&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getMACD(String stockId, {int days = 60, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/indicators/macd?days=$days&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getBollinger(String stockId, {int days = 60, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/indicators/bollinger?days=$days&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getKD(String stockId, {int days = 60, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/indicators/kd?days=$days&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 新聞相關 ====================

  Future<Map<String, dynamic>> getStockNews(String stockId, {int limit = 10, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/news/stock/$stockId?limit=$limit&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getMarketNews({int limit = 20, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/news/market?limit=$limit&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 投資組合相關 ====================

  Future<List<PortfolioSummary>> getPortfolios() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolio'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => PortfolioSummary.fromJson(e)).toList();
  }

  Future<Map<String, dynamic>> createPortfolio(String name, String? description) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/portfolio'),
      headers: _headers,
      body: jsonEncode({
        'name': name,
        if (description != null) 'description': description,
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<PortfolioDetail> getPortfolioDetail(int portfolioId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolio/$portfolioId'),
      headers: _headers,
    );
    _checkResponse(response);
    return PortfolioDetail.fromJson(jsonDecode(response.body));
  }

  Future<void> deletePortfolio(int portfolioId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/portfolio/$portfolioId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  Future<Map<String, dynamic>> addPortfolioHolding(
    int portfolioId,
    String stockId,
    int quantity,
    double avgCost,
    DateTime buyDate,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/portfolio/$portfolioId/holdings'),
      headers: _headers,
      body: jsonEncode({
        'stock_id': stockId,
        'quantity': quantity,
        'avg_cost': avgCost,
        'buy_date': buyDate.toIso8601String().split('T')[0],
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<void> deletePortfolioHolding(int holdingId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/portfolio/holdings/$holdingId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  Future<PortfolioPerformance> getPortfolioPerformance(int portfolioId, {int days = 30}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolio/$portfolioId/performance?days=$days'),
      headers: _headers,
    );
    _checkResponse(response);
    return PortfolioPerformance.fromJson(jsonDecode(response.body));
  }

  // ==================== 虛擬交易相關 ====================

  Future<AccountSummary> getTradingAccount() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/trading/account'),
      headers: _headers,
    );
    _checkResponse(response);
    return AccountSummary.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> placeOrder({
    required String stockId,
    required String orderType,
    required int quantity,
    required double price,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/trading/order'),
      headers: _headers,
      body: jsonEncode({
        'stock_id': stockId,
        'order_type': orderType,
        'quantity': quantity,
        'price': price,
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> cancelOrder(int orderId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/trading/order/$orderId'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> resetTradingAccount() async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/trading/reset'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<List<VirtualPosition>> getTradingPositions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/trading/positions'),
      headers: _headers,
    );
    _checkResponse(response);
    final data = jsonDecode(response.body);
    final List<dynamic> positions = data['positions'] ?? [];
    return positions.map((e) => VirtualPosition.fromJson(e)).toList();
  }

  Future<List<VirtualOrder>> getTradingOrders() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/trading/orders'),
      headers: _headers,
    );
    _checkResponse(response);
    final data = jsonDecode(response.body);
    final List<dynamic> orders = data['orders'] ?? [];
    return orders.map((e) => VirtualOrder.fromJson(e)).toList();
  }

  // ==================== 社群情緒相關 ====================

  Future<Map<String, dynamic>> getHotStocks({int limit = 10, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/social/hot-stocks?limit=$limit&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<StockSentimentResponse> getStockSentiment(String stockId, {int days = 7, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/social/stock/$stockId/sentiment?days=$days&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return StockSentimentResponse.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> getMarketSentiment({String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/social/market?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 基本面數據相關 ====================

  /// 取得股票基本面數據
  Future<FundamentalData> getFundamental(String stockId, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/fundamental?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return FundamentalData.fromJson(jsonDecode(response.body));
  }

  /// 取得財務報表
  Future<FinancialStatements> getFinancialStatements(String stockId, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/financial-statements?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return FinancialStatements.fromJson(jsonDecode(response.body));
  }

  /// 取得股息歷史
  Future<List<DividendData>> getDividends(String stockId, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/dividends?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => DividendData.fromJson(e)).toList();
  }

  /// 取得法人買賣超 (僅限台股)
  Future<List<InstitutionalData>> getInstitutional(String stockId, {int days = 30}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/institutional?days=$days'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => InstitutionalData.fromJson(e)).toList();
  }

  /// 取得融資融券 (僅限台股)
  Future<List<MarginData>> getMarginTrading(String stockId, {int days = 30}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/margin?days=$days'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => MarginData.fromJson(e)).toList();
  }

  // ==================== 股票篩選器相關 ====================

  /// 依條件篩選股票
  Future<ScreenResponse> screenStocks(ScreenCriteria criteria, {String market = 'TW', int limit = 50}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/screener/search?market=$market&limit=$limit'),
      headers: _headers,
      body: jsonEncode(criteria.toJson()),
    );
    _checkResponse(response);
    return ScreenResponse.fromJson(jsonDecode(response.body));
  }

  /// 取得預設篩選條件列表
  Future<List<PresetScreen>> getPresetScreens() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/screener/presets'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => PresetScreen.fromJson(e)).toList();
  }

  /// 執行預設篩選
  Future<ScreenResponse> getPresetScreenResults(String presetId, {String market = 'TW', int limit = 50}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/screener/presets/$presetId?market=$market&limit=$limit'),
      headers: _headers,
    );
    _checkResponse(response);
    return ScreenResponse.fromJson(jsonDecode(response.body));
  }

  /// 取得產業列表
  Future<List<String>> getIndustries({String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/screener/industries?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    final data = jsonDecode(response.body);
    final List<dynamic> industries = data['industries'] ?? [];
    return industries.cast<String>();
  }

  /// 依指標排名取得股票
  Future<Map<String, dynamic>> getTopByMetric(
    String metric, {
    String market = 'TW',
    bool ascending = false,
    int limit = 20,
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/screener/top/$metric?market=$market&ascending=$ascending&limit=$limit'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 錯誤處理 ====================

  void _checkResponse(http.Response response) {
    if (response.statusCode >= 400) {
      final body = jsonDecode(response.body);
      throw ApiException(
        statusCode: response.statusCode,
        message: body['detail'] ?? 'Unknown error',
      );
    }
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException: $statusCode - $message';
}
