import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/stock.dart';
import '../models/watchlist_item.dart';
import '../models/ai_suggestion.dart';
import '../models/stock_history.dart';
import '../models/indicator_data.dart';
import '../models/portfolio.dart'
    show Portfolio, Position, Transaction, PortfolioSummary, PositionAllocation,
         CreatePortfolioRequest, CreateTransactionRequest;
import '../models/alert.dart' show PriceAlert, CreateAlertRequest;
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

  Future<Map<String, dynamic>> googleAuth(String idToken) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/google'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'id_token': idToken}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> googleAuthWithAccessToken({
    required String accessToken,
    required String email,
    String? displayName,
    String? photoUrl,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/google-access-token'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'access_token': accessToken,
        'email': email,
        'display_name': displayName,
        'photo_url': photoUrl,
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/auth/me'),
      headers: _headers,
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

  Future<List<WatchlistItem>> getWatchlist({String? market, bool forceRefresh = false}) async {
    final params = <String>[];
    if (market != null) params.add('market=$market');
    if (forceRefresh) params.add('force_refresh=true');
    final query = params.isNotEmpty ? '?${params.join('&')}' : '';
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

  // ==================== 自選股分組相關 ====================

  Future<List<Map<String, dynamic>>> getWatchlistGroups() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/watchlist/groups'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> createWatchlistGroup(String name, {String color = '#2196F3'}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/watchlist/groups'),
      headers: _headers,
      body: jsonEncode({'name': name, 'color': color}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<void> updateWatchlistGroup(int groupId, {String? name, String? color}) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/watchlist/groups/$groupId'),
      headers: _headers,
      body: jsonEncode({
        if (name != null) 'name': name,
        if (color != null) 'color': color,
      }),
    );
    _checkResponse(response);
  }

  Future<void> deleteWatchlistGroup(int groupId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/watchlist/groups/$groupId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  Future<void> assignStockToGroup(String stockId, int? groupId) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/watchlist/$stockId/group'),
      headers: _headers,
      body: jsonEncode({'group_id': groupId}),
    );
    _checkResponse(response);
  }

  // ==================== 交易日記相關 ====================

  Future<Map<String, dynamic>> getDiaryEntries({
    int limit = 50,
    int offset = 0,
    String? stockId,
    String? tradeType,
    String? emotion,
  }) async {
    final params = <String>['limit=$limit', 'offset=$offset'];
    if (stockId != null) params.add('stock_id=$stockId');
    if (tradeType != null) params.add('trade_type=$tradeType');
    if (emotion != null) params.add('emotion=$emotion');
    final response = await http.get(
      Uri.parse('$baseUrl/api/diary?${params.join("&")}'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> createDiaryEntry(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/diary'),
      headers: _headers,
      body: jsonEncode(data),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updateDiaryEntry(int entryId, Map<String, dynamic> data) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/diary/$entryId'),
      headers: _headers,
      body: jsonEncode(data),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<void> deleteDiaryEntry(int entryId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/diary/$entryId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  Future<Map<String, dynamic>> getDiaryStats({int days = 30}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/diary/stats?days=$days'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== AI 相關 ====================

  /// 獲取 AI 建議
  /// [generateMissing] 為 true 時會為沒有建議的股票生成新建議（較慢）
  Future<List<AISuggestion>> getAISuggestions({bool generateMissing = false}) async {
    final uri = Uri.parse('$baseUrl/api/ai/suggestions').replace(
      queryParameters: {'generate_missing': generateMissing.toString()},
    );
    final response = await http.get(uri, headers: _headers);
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => AISuggestion.fromJson(e)).toList();
  }

  Future<AISuggestion> getStockSuggestion(String stockId, {String market = 'TW', bool refresh = false}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/suggestions/$stockId?market=$market&refresh=$refresh'),
      headers: _headers,
    );
    _checkResponse(response);
    return AISuggestion.fromJson(jsonDecode(response.body));
  }

  /// 綜合 AI 分析（6維度雷達圖 + 健康等級）
  Future<Map<String, dynamic>> getComprehensiveAnalysis(String stockId, {String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/comprehensive-analysis/$stockId?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
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

  // ==================== 預測準確度追蹤 ====================

  Future<Map<String, dynamic>> getPredictionStatistics({int days = 30, String? market, String? stockId}) async {
    final params = <String, String>{'days': days.toString()};
    if (market != null) params['market'] = market;
    if (stockId != null) params['stock_id'] = stockId;

    final uri = Uri.parse('$baseUrl/api/predictions/statistics').replace(queryParameters: params);
    final response = await http.get(uri, headers: _headers);
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getYesterdayPredictions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/predictions/yesterday'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getDailyPredictions(String date) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/predictions/daily/$date'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updatePredictionResults({String? market}) async {
    final uri = market != null
        ? Uri.parse('$baseUrl/api/predictions/update-results?market=$market')
        : Uri.parse('$baseUrl/api/predictions/update-results');
    final response = await http.post(uri, headers: _headers);
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getTodayPredictions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/predictions/today'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getAllStocksPredictionStats({int days = 30}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/predictions/all-stocks?days=$days'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 價格警示相關 ====================

  Future<List<PriceAlert>> getAlerts({bool? activeOnly}) async {
    String url = '$baseUrl/api/alerts';
    if (activeOnly != null) {
      url += '?active_only=$activeOnly';
    }
    final response = await http.get(
      Uri.parse(url),
      headers: _headers,
    );
    _checkResponse(response);
    final Map<String, dynamic> responseData = jsonDecode(response.body);
    final List<dynamic> data = responseData['alerts'] ?? [];
    return data.map((e) => PriceAlert.fromJson(e)).toList();
  }

  Future<PriceAlert> createAlert(CreateAlertRequest request) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/alerts'),
      headers: _headers,
      body: jsonEncode(request.toJson()),
    );
    _checkResponse(response);
    return PriceAlert.fromJson(jsonDecode(response.body));
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

  Future<PriceAlert> toggleAlert(int alertId, bool isActive) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/alerts/$alertId/toggle'),
      headers: _headers,
      body: jsonEncode({'is_active': isActive}),
    );
    _checkResponse(response);
    return PriceAlert.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> resetAlert(int alertId) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/alerts/$alertId/reset'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<List<PriceAlert>> checkAlerts() async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/alerts/check'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => PriceAlert.fromJson(e)).toList();
  }

  Future<List<PriceAlert>> getTriggeredAlerts() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/alerts/triggered/list'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => PriceAlert.fromJson(e)).toList();
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

  // ==================== 形態識別相關 ====================

  /// 取得股票形態識別結果
  Future<Map<String, dynamic>> getStockPatterns(
    String stockId, {
    int lookback = 60,
    String market = 'TW',
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/patterns?lookback=$lookback&market=$market'),
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

  Future<List<Portfolio>> getPortfolios() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolios'),
      headers: _headers,
    );
    _checkResponse(response);
    final Map<String, dynamic> body = jsonDecode(response.body);
    final List<dynamic> data = body['portfolios'] ?? [];
    return data.map((e) => Portfolio.fromJson(e)).toList();
  }

  Future<Portfolio> createPortfolio(CreatePortfolioRequest request) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/portfolios'),
      headers: _headers,
      body: jsonEncode(request.toJson()),
    );
    _checkResponse(response);
    return Portfolio.fromJson(jsonDecode(response.body));
  }

  Future<Portfolio> getPortfolio(int portfolioId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId'),
      headers: _headers,
    );
    _checkResponse(response);
    return Portfolio.fromJson(jsonDecode(response.body));
  }

  Future<Portfolio> updatePortfolio(int portfolioId, {String? name, String? description}) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId'),
      headers: _headers,
      body: jsonEncode({
        if (name != null) 'name': name,
        if (description != null) 'description': description,
      }),
    );
    _checkResponse(response);
    return Portfolio.fromJson(jsonDecode(response.body));
  }

  Future<void> deletePortfolio(int portfolioId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  Future<List<Position>> getPositions(int portfolioId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId/positions'),
      headers: _headers,
    );
    _checkResponse(response);
    final Map<String, dynamic> body = jsonDecode(response.body);
    final List<dynamic> data = body['positions'] ?? [];
    return data.map((e) => Position.fromJson(e)).toList();
  }

  Future<PortfolioSummary> getPortfolioSummary(int portfolioId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId/summary'),
      headers: _headers,
    );
    _checkResponse(response);
    return PortfolioSummary.fromJson(jsonDecode(response.body));
  }

  Future<List<PositionAllocation>> getPositionAllocation(int portfolioId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId/allocation'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => PositionAllocation.fromJson(e)).toList();
  }

  Future<List<Transaction>> getTransactions(int portfolioId, {int limit = 50}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId/transactions?limit=$limit'),
      headers: _headers,
    );
    _checkResponse(response);
    final Map<String, dynamic> body = jsonDecode(response.body);
    final List<dynamic> data = body['transactions'] ?? [];
    return data.map((e) => Transaction.fromJson(e)).toList();
  }

  Future<Transaction> addTransaction(int portfolioId, CreateTransactionRequest request) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId/transactions'),
      headers: _headers,
      body: jsonEncode(request.toJson()),
    );
    _checkResponse(response);
    return Transaction.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> getPortfolioPerformance(int portfolioId, {int days = 30}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/portfolios/$portfolioId/performance?days=$days'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
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

  // ==================== 日曆相關 ====================

  Future<Map<String, dynamic>> getEarningsCalendar({
    String market = 'TW',
    int? month,
    int? year,
  }) async {
    final params = <String>['market=$market'];
    if (month != null) params.add('month=$month');
    if (year != null) params.add('year=$year');
    final response = await http.get(
      Uri.parse('$baseUrl/api/calendar/earnings?${params.join("&")}'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getDividendCalendar({
    String market = 'TW',
    int? month,
    int? year,
  }) async {
    final params = <String>['market=$market'];
    if (month != null) params.add('month=$month');
    if (year != null) params.add('year=$year');
    final response = await http.get(
      Uri.parse('$baseUrl/api/calendar/dividends?${params.join("&")}'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getEconomicCalendar({
    String market = 'TW',
    int? month,
    int? year,
  }) async {
    final params = <String>['market=$market'];
    if (month != null) params.add('month=$month');
    if (year != null) params.add('year=$year');
    final response = await http.get(
      Uri.parse('$baseUrl/api/calendar/economic?${params.join("&")}'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 風險指標相關 ====================

  Future<Map<String, dynamic>> getStockRisk(String stockId, {int days = 252, String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/risk?days=$days&market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 市場概覽相關 ====================

  Future<Map<String, dynamic>> getMarketHeatmap({String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/market/heatmap?market=$market'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> getMarketRankings({
    String market = 'TW',
    String category = 'gainers',
    int limit = 20,
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/market/rankings?market=$market&category=$category&limit=$limit'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 管理員相關 ====================

  Future<List<Map<String, dynamic>>> getAdminUsers({int skip = 0, int limit = 50}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/admin/users?skip=$skip&limit=$limit'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getAdminStats() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/admin/stats'),
      headers: _headers,
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updateUserSubscription(int userId, String tier) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/api/admin/users/$userId/subscription'),
      headers: _headers,
      body: jsonEncode({'subscription_tier': tier}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> updateUserAdmin(int userId, bool isAdmin) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/api/admin/users/$userId/admin'),
      headers: _headers,
      body: jsonEncode({'is_admin': isAdmin}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 聊天歷史相關 ====================

  Future<List<dynamic>> getChatHistory({int limit = 50}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/chat/history?limit=$limit'),
      headers: _headers,
    );
    _checkResponse(response);
    final data = jsonDecode(response.body);
    return data['messages'] ?? [];
  }

  // ==================== 產業趨勢相關 ====================

  Future<Map<String, dynamic>> getIndustryTrends({String market = 'TW'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/industry-trends?market=$market'),
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
