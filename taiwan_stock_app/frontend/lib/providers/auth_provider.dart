import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/auth_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService;
  User? _user;
  bool _isLoading = false;
  String? _error;

  AuthProvider(this._authService);

  User? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _user != null;
  bool get isPro => _user?.isPro ?? false;
  bool get isAdmin => _user?.isAdmin ?? false;

  Future<bool> checkAuth() async {
    _isLoading = true;
    notifyListeners();

    try {
      final isLoggedIn = await _authService.isLoggedIn();
      if (isLoggedIn) {
        // Try to get saved user data
        _user = await _authService.getSavedUser();
        // Refresh user data from server
        final refreshedUser = await _authService.refreshUser();
        if (refreshedUser != null) {
          _user = refreshedUser;
        }
      }
      _isLoading = false;
      notifyListeners();
      return isLoggedIn;
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _user = await _authService.login(email, password);
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> register(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _user = await _authService.register(email, password);
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> googleLogin(String idToken) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _user = await _authService.googleLogin(idToken);
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> refreshUser() async {
    final refreshedUser = await _authService.refreshUser();
    if (refreshedUser != null) {
      _user = refreshedUser;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    notifyListeners();
  }
}
