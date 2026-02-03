class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8002',
  );

  static const bool isProduction = bool.fromEnvironment('dart.vm.product');
}
