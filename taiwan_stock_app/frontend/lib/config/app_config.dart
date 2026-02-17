import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;

class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// Web 用 Google Client ID
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
