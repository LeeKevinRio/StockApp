import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user.dart';
import 'api_service.dart';

class AuthService {
  final ApiService _apiService;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static const String _tokenKey = 'auth_token';
  static const String _userKey = 'user_data';

  AuthService(this._apiService);

  Future<User> login(String email, String password) async {
    final response = await _apiService.login(email, password);
    final token = response['access_token'];
    final user = User.fromJson(response['user']);

    // Save token and user data
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _userKey, value: jsonEncode(user.toJson()));

    // Set token in API service
    _apiService.setAuthToken(token);

    return user;
  }

  Future<User> register(String email, String password) async {
    final response = await _apiService.register(email, password);
    final token = response['access_token'];
    final user = User.fromJson(response['user']);

    // Save token and user data
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _userKey, value: jsonEncode(user.toJson()));

    // Set token in API service
    _apiService.setAuthToken(token);

    return user;
  }

  Future<User> googleLogin(String idToken) async {
    final response = await _apiService.googleAuth(idToken);
    final token = response['access_token'];
    final user = User.fromJson(response['user']);

    // Save token and user data
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _userKey, value: jsonEncode(user.toJson()));

    // Set token in API service
    _apiService.setAuthToken(token);

    return user;
  }

  Future<User> googleLoginWithAccessToken({
    required String accessToken,
    required String email,
    String? displayName,
    String? photoUrl,
  }) async {
    final response = await _apiService.googleAuthWithAccessToken(
      accessToken: accessToken,
      email: email,
      displayName: displayName,
      photoUrl: photoUrl,
    );
    final token = response['access_token'];
    final user = User.fromJson(response['user']);

    // Save token and user data
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _userKey, value: jsonEncode(user.toJson()));

    // Set token in API service
    _apiService.setAuthToken(token);

    return user;
  }

  Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }

  Future<User?> getSavedUser() async {
    final userJson = await _storage.read(key: _userKey);
    if (userJson != null) {
      try {
        return User.fromJson(jsonDecode(userJson));
      } catch (e) {
        return null;
      }
    }
    return null;
  }

  Future<User?> refreshUser() async {
    try {
      final userData = await _apiService.getCurrentUser();
      final user = User.fromJson(userData);
      await _storage.write(key: _userKey, value: jsonEncode(user.toJson()));
      return user;
    } catch (e) {
      return null;
    }
  }

  Future<void> deleteAccount() async {
    await _apiService.deleteAccount();
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _userKey);
    _apiService.setAuthToken('');
  }

  Future<void> logout() async {
    // 讀取目前 token，若有效才嘗試呼叫後端登出 API
    final token = await _storage.read(key: _tokenKey);
    if (token != null && token.isNotEmpty) {
      try {
        // 嘗試呼叫後端登出（若後端有提供），失敗不影響本地登出
        // await _apiService.logoutRemote();
      } catch (_) {
        // 忽略遠端登出失敗，確保本地狀態仍能清除
      }
    }

    // 無論遠端登出是否成功，都清除本地狀態
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _userKey);
    _apiService.setAuthToken('');
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    if (token != null && token.isNotEmpty) {
      _apiService.setAuthToken(token);
      return true;
    }
    return false;
  }
}
