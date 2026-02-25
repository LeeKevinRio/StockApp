import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;

class AppConfig {
  /// 編譯時指定的 API URL（生產環境用）
  static const String _envApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// 根據平台自動選擇 API base URL
  /// Android 模擬器的 localhost 指向模擬器自己，要用 10.0.2.2 連 host
  static String get apiBaseUrl {
    if (_envApiBaseUrl.isNotEmpty) return _envApiBaseUrl;
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8002';
    }
    return 'http://localhost:8002';
  }

  /// Web 用 Google Client ID（透過 --dart-define=GOOGLE_CLIENT_ID=xxx 傳入）
  static const String _webGoogleClientId = String.fromEnvironment(
    'GOOGLE_CLIENT_ID',
    defaultValue: '506193160322-omn6g1hja95mv192ajdu0ospgndohh6o.apps.googleusercontent.com',
  );

  /// iOS 用 Google Client ID（需在 Google Cloud Console 另建 iOS OAuth 憑證）
  static const String _iosGoogleClientId = String.fromEnvironment(
    'GOOGLE_IOS_CLIENT_ID',
    defaultValue: '',
  );

  /// 根據平台自動選擇正確的 Google Client ID
  static String get googleClientId {
    if (kIsWeb) return _webGoogleClientId;
    if (defaultTargetPlatform == TargetPlatform.iOS) {
      return _iosGoogleClientId.isNotEmpty
          ? _iosGoogleClientId
          : _webGoogleClientId;
    }
    return _webGoogleClientId;
  }

  static const bool isProduction = bool.fromEnvironment('dart.vm.product');
}
