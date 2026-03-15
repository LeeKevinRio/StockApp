import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService;
  User? _user;
  bool _isLoading = false;
  String? _error;

  AuthProvider(this._authService, {User? initialUser}) : _user = initialUser;

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
        // 先從本地 cache 恢復 user
        _user = await _authService.getSavedUser();
        // 向伺服器驗證 token 並刷新 user 資料
        // refreshUser() 會在 401 時 rethrow ApiException
        final refreshedUser = await _authService.refreshUser();
        if (refreshedUser != null) {
          _user = refreshedUser;
        }
      }
      _isLoading = false;
      notifyListeners();
      return isLoggedIn;
    } on ApiException catch (e) {
      // Token 過期 (401)，清除登入狀態
      if (e.isUnauthorized) {
        _user = null;
      }
      _isLoading = false;
      notifyListeners();
      return false;
    } catch (e) {
      // 網路錯誤等：如果有 cached user 就保持登入
      _isLoading = false;
      notifyListeners();
      return _user != null;
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

  Future<void> googleLoginWithAccessToken({
    required String accessToken,
    required String email,
    String? displayName,
    String? photoUrl,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _user = await _authService.googleLoginWithAccessToken(
        accessToken: accessToken,
        email: email,
        displayName: displayName,
        photoUrl: photoUrl,
      );
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  /// 刷新使用者資料，若 token 已過期則清除登入狀態
  /// 回傳 true 表示使用者仍有效，false 表示已被登出
  Future<bool> refreshUser() async {
    try {
      final refreshedUser = await _authService.refreshUser();
      if (refreshedUser != null) {
        _user = refreshedUser;
        notifyListeners();
      }
      return true;
    } on ApiException catch (e) {
      if (e.isUnauthorized) {
        // Token 過期，清除登入狀態
        _user = null;
        notifyListeners();
        return false;
      }
      return true; // 其他 API 錯誤，保留 cached user
    } catch (e) {
      return true; // 網路錯誤等，保留 cached user
    }
  }

  Future<void> deleteAccount() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _authService.deleteAccount();
      _user = null;
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    notifyListeners();
  }
}
