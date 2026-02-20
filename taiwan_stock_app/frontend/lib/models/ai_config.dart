/// AI Config Models — BYOK 設定

class AIModelInfo {
  final String id;
  final String label;

  AIModelInfo({required this.id, required this.label});

  factory AIModelInfo.fromJson(Map<String, dynamic> json) {
    return AIModelInfo(
      id: json['id'] as String,
      label: json['label'] as String,
    );
  }
}

class AIProviderInfo {
  final String id;
  final String label;
  final List<AIModelInfo> models;

  AIProviderInfo({required this.id, required this.label, required this.models});

  factory AIProviderInfo.fromJson(Map<String, dynamic> json) {
    return AIProviderInfo(
      id: json['id'] as String,
      label: json['label'] as String,
      models: (json['models'] as List)
          .map((m) => AIModelInfo.fromJson(m as Map<String, dynamic>))
          .toList(),
    );
  }
}

class AIConfig {
  final String? provider;
  final String? model;
  final bool hasApiKey;
  final String? providerLabel;

  AIConfig({
    this.provider,
    this.model,
    this.hasApiKey = false,
    this.providerLabel,
  });

  factory AIConfig.fromJson(Map<String, dynamic> json) {
    return AIConfig(
      provider: json['provider'] as String?,
      model: json['model'] as String?,
      hasApiKey: json['has_api_key'] as bool? ?? false,
      providerLabel: json['provider_label'] as String?,
    );
  }
}
