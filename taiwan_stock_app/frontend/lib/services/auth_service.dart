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
    await _storage.write(key: _userKey, value: user.toJson().toString());

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
    await _storage.write(key: _userKey, value: user.toJson().toString());

    // Set token in API service
    _apiService.setAuthToken(token);

    return user;
  }

  Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }

  Future<void> logout() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _userKey);
  }

  Future<bool> isLoggedIn() async {
    final token = await getToken();
    if (token != null) {
      _apiService.setAuthToken(token);
      return true;
    }
    return false;
  }
}
