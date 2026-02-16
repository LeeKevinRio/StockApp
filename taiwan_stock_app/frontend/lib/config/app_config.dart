class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  static const String googleClientId = String.fromEnvironment(
    'GOOGLE_CLIENT_ID',
    defaultValue: '506193160322-omn6g1hja95mv192ajdu0ospgndohh6o.apps.googleusercontent.com',
  );

  static const bool isProduction = bool.fromEnvironment('dart.vm.product');
}
