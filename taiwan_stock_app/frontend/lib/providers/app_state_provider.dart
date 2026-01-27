import 'package:flutter/foundation.dart';

/// Global app state provider for managing loading states and errors
class AppStateProvider with ChangeNotifier {
  bool _isGlobalLoading = false;
  String? _globalError;
  final Map<String, bool> _loadingStates = {};
  final Map<String, String?> _errors = {};

  // Global loading state
  bool get isGlobalLoading => _isGlobalLoading;
  String? get globalError => _globalError;

  void setGlobalLoading(bool loading) {
    _isGlobalLoading = loading;
    notifyListeners();
  }

  void setGlobalError(String? error) {
    _globalError = error;
    notifyListeners();
  }

  void clearGlobalError() {
    _globalError = null;
    notifyListeners();
  }

  // Scoped loading states (e.g., 'stocks', 'watchlist', etc.)
  bool isLoading(String key) => _loadingStates[key] ?? false;

  void setLoading(String key, bool loading) {
    _loadingStates[key] = loading;
    notifyListeners();
  }

  // Scoped error states
  String? getError(String key) => _errors[key];

  void setError(String key, String? error) {
    _errors[key] = error;
    notifyListeners();
  }

  void clearError(String key) {
    _errors[key] = null;
    notifyListeners();
  }

  void clearAllErrors() {
    _errors.clear();
    _globalError = null;
    notifyListeners();
  }

  // Check if any loading is active
  bool get hasActiveLoading =>
      _isGlobalLoading || _loadingStates.values.any((v) => v);

  // Check if any error exists
  bool get hasAnyError =>
      _globalError != null || _errors.values.any((v) => v != null);
}
