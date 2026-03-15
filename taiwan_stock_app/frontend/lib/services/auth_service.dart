import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import 'api_service.dart';

/// 跨平台 Token 持久化存儲
/// - Web: 使用 SharedPreferences (localStorage)，避免 FlutterSecureStorage 加密 key 遺失
/// - Mobile: 使用 FlutterSecureStorage (Keychain/Keystore)
class _TokenStorage {
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();

  Future<void> write(String key, String value) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, value);
    } else {
      await _secureStorage.write(key: key, value: value);
    }
  }

  Future<String?> read(String key) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(key);
    } else {
      return await _secureStorage.read(key: key);
    }
  }

  Future<void> delete(String key) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(key);
    } else {
      await _secureStorage.delete(key: key);
    }
  }
}

class AuthService {
  final ApiService _apiService;
  final _TokenStorage _storage = _TokenStorage();

  static const String _tokenKey = 'auth_token';
  static const String _userKey = 'user_data';

  AuthService(this._apiService);

  Future<User> login(String email, String password) async {
    final response = await _apiService.login(email, password);
    final token = response['access_token'];
    final user = User.fromJson(response['user']);

    await _storage.write(_tokenKey, token);
    await _storage.write(_userKey, jsonEncode(user.toJson()));
    _apiService.setAuthToken(token);

    return user;
  }

  Future<User> register(String email, String password) async {
    final response = await _apiService.register(email, password);
    final token = response['access_token'];
    final user = User.fromJson(response['user']);

    await _storage.write(_tokenKey, token);
    await _storage.write(_userKey, jsonEncode(user.toJson()));
    _apiService.setAuthToken(token);

    return user;
  }

  Future<User> googleLogin(String idToken) async {
    final response = await _apiService.googleAuth(idToken);
    final token = response['access_token'];
    final user = User.fromJson(response['user']);

    await _storage.write(_tokenKey, token);
    await _storage.write(_userKey, jsonEncode(user.toJson()));
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

    await _storage.write(_tokenKey, token);
    await _storage.write(_userKey, jsonEncode(user.toJson()));
    _apiService.setAuthToken(token);

    return user;
  }

  Future<String?> getToken() async {
    return await _storage.read(_tokenKey);
  }

  Future<User?> getSavedUser() async {
    final userJson = await _storage.read(_userKey);
    if (userJson != null) {
      try {
        return User.fromJson(jsonDecode(userJson));
      } catch (e) {
        return null;
      }
    }
    return null;
  }

  /// 從伺服器刷新使用者資料
  /// - 成功：回傳更新後的 User
  /// - 401（token 過期）：清除本地 auth 資料並 rethrow，讓呼叫端處理登出
  /// - 其他錯誤（網路/伺服器）：回傳 null，保留 cached user
  Future<User?> refreshUser() async {
    try {
      final userData = await _apiService.getCurrentUser();
      final user = User.fromJson(userData);
      await _storage.write(_userKey, jsonEncode(user.toJson()));
      return user;
    } on ApiException catch (e) {
      if (e.isUnauthorized) {
        // Token 已過期或無效，清除本地 auth 資料
        await logout();
        rethrow;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<void> deleteAccount() async {
    await _apiService.deleteAccount();
    await _storage.delete(_tokenKey);
    await _storage.delete(_userKey);
    _apiService.setAuthToken('');
  }

  Future<void> logout() async {
    await _storage.delete(_tokenKey);
    await _storage.delete(_userKey);
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
