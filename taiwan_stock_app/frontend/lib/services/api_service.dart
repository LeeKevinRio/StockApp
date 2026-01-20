import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/stock.dart';
import '../models/watchlist_item.dart';
import '../models/ai_suggestion.dart';
import '../models/stock_history.dart';

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

  Future<List<Stock>> searchStocks(String query) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/search?q=$query'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => Stock.fromJson(e)).toList();
  }

  Future<StockPrice> getStockPrice(String stockId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/price'),
      headers: _headers,
    );
    _checkResponse(response);
    return StockPrice.fromJson(jsonDecode(response.body));
  }

  Future<List<StockHistory>> getStockHistory(String stockId, {int days = 60}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/history?days=$days'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => StockHistory.fromJson(e)).toList();
  }

  // ==================== 自選股相關 ====================

  Future<List<WatchlistItem>> getWatchlist() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/watchlist'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => WatchlistItem.fromJson(e)).toList();
  }

  Future<void> addToWatchlist(String stockId, {String? notes}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/watchlist'),
      headers: _headers,
      body: jsonEncode({'stock_id': stockId, 'notes': notes}),
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

  Future<AISuggestion> getStockSuggestion(String stockId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/suggestions/$stockId'),
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
