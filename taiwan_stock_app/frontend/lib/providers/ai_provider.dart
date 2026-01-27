import 'package:flutter/foundation.dart';
import '../models/ai_suggestion.dart';
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

  AIProvider(this._apiService);

  List<AISuggestion> get suggestions => _suggestions;
  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  bool get isLoadingSuggestions => _isLoadingSuggestions;
  String? get error => _error;
  String? get suggestionsError => _suggestionsError;

  Future<void> loadSuggestions() async {
    _isLoadingSuggestions = true;
    _suggestionsError = null;
    notifyListeners();

    try {
      _suggestions = await _apiService.getAISuggestions();
      _isLoadingSuggestions = false;
      notifyListeners();
    } catch (e) {
      _suggestionsError = e.toString();
      _isLoadingSuggestions = false;
      notifyListeners();
    }
  }

  Future<void> refreshSuggestions() async {
    await loadSuggestions();
  }

  Future<void> loadChatHistory({String? stockId}) async {
    // For now, just clear messages
    // In a real app, you would fetch history from API
    _messages.clear();
    notifyListeners();
  }

  Future<void> sendMessage(String message, {String? stockId}) async {
    // Add user message
    _messages.add(ChatMessage(role: 'user', content: message));
    _isLoading = true;
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
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }
}
