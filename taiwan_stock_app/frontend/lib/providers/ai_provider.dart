import 'package:flutter/foundation.dart';
import '../models/ai_suggestion.dart';
import '../models/industry_trend.dart';
import '../services/api_service.dart';

class ChatMessage {
  final String id;
  final String role;
  final String content;
  final List<String>? sources;
  final DateTime timestamp;

  ChatMessage({
    String? id,
    required this.role,
    required this.content,
    this.sources,
    DateTime? timestamp,
  })  : id = id ?? DateTime.now().millisecondsSinceEpoch.toString(),
        timestamp = timestamp ?? DateTime.now();

  ChatMessage copyWith({
    String? id,
    String? role,
    String? content,
    List<String>? sources,
    DateTime? timestamp,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      role: role ?? this.role,
      content: content ?? this.content,
      sources: sources ?? this.sources,
      timestamp: timestamp ?? this.timestamp,
    );
  }
}

class AIProvider with ChangeNotifier {
  final ApiService _apiService;
  List<AISuggestion> _suggestions = [];
  List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isLoadingSuggestions = false;
  String? _error;
  String? _suggestionsError;

  IndustryTrendAnalysis? _industryTrends;
  bool _isLoadingTrends = false;
  String? _trendsError;

  IndustryTrendAnalysis? get industryTrends => _industryTrends;
  bool get isLoadingTrends => _isLoadingTrends;
  String? get trendsError => _trendsError;

  AIProvider(this._apiService);

  List<AISuggestion> get suggestions => _suggestions;
  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  bool get isLoadingSuggestions => _isLoadingSuggestions;
  String? get error => _error;
  String? get suggestionsError => _suggestionsError;

  /// 載入已有的 AI 建議（快速）
  Future<void> loadSuggestions() async {
    _isLoadingSuggestions = true;
    _suggestionsError = null;
    notifyListeners();

    try {
      _suggestions = await _apiService.getAISuggestions(generateMissing: false);
      _isLoadingSuggestions = false;
      notifyListeners();
    } catch (e) {
      _suggestionsError = e.toString();
      _isLoadingSuggestions = false;
      notifyListeners();
    }
  }

  /// 刷新並生成缺少的 AI 建議（較慢）
  Future<void> refreshSuggestions() async {
    _isLoadingSuggestions = true;
    _suggestionsError = null;
    notifyListeners();

    try {
      _suggestions = await _apiService.getAISuggestions(generateMissing: true);
      _isLoadingSuggestions = false;
      notifyListeners();
    } catch (e) {
      _suggestionsError = e.toString();
      _isLoadingSuggestions = false;
      notifyListeners();
    }
  }

  Future<void> loadChatHistory({String? stockId}) async {
    try {
      final history = await _apiService.getChatHistory(limit: 50);
      _messages = (history as List).map((msg) => ChatMessage(
        role: msg['role'] ?? 'user',
        content: msg['content'] ?? '',
        timestamp: msg['created_at'] != null
            ? DateTime.tryParse(msg['created_at']) ?? DateTime.now()
            : DateTime.now(),
      )).toList();
    } catch (e) {
      _messages.clear();
    }
    notifyListeners();
  }

  Future<void> sendMessage(String message, {String? stockId}) async {
    // Add user message
    _messages.add(ChatMessage(role: 'user', content: message));
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.chat(message, stockId: stockId);

      // Add assistant message
      _messages.add(ChatMessage(
        role: 'assistant',
        content: response['response'],
        sources: List<String>.from(response['sources'] ?? []),
      ));

      _isLoading = false;
      notifyListeners();
    } catch (e) {
      final errorStr = e.toString();
      _error = errorStr;
      _isLoading = false;

      // Add error message to chat so user can see it
      String errorMessage;
      if (errorStr.contains('429') || errorStr.contains('quota') || errorStr.contains('配額')) {
        errorMessage = 'AI 服務配額已達上限，請稍後再試。';
      } else if (errorStr.contains('Failed to fetch') || errorStr.contains('SocketException')) {
        errorMessage = '無法連接到伺服器，請檢查網路連線。';
      } else {
        errorMessage = 'AI 服務暫時不可用，請稍後再試。';
      }

      _messages.add(ChatMessage(
        role: 'assistant',
        content: errorMessage,
      ));

      notifyListeners();
    }
  }

  Future<void> loadIndustryTrends() async {
    _isLoadingTrends = true;
    _trendsError = null;
    notifyListeners();

    try {
      final data = await _apiService.getIndustryTrends();
      _industryTrends = IndustryTrendAnalysis.fromJson(data);
      _isLoadingTrends = false;
      notifyListeners();
    } catch (e) {
      _trendsError = e.toString();
      _isLoadingTrends = false;
      notifyListeners();
    }
  }

  Future<void> refreshIndustryTrends() async {
    await loadIndustryTrends();
  }
}
