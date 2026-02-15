/// 綜合 AI 分析數據模型

class ComprehensiveAnalysis {
  final String stockId;
  final String stockName;
  final String market;
  final double totalScore;
  final String healthGrade;
  final Map<String, DimensionScore> dimensions;
  final RadarData radar;
  final String aiSummary;
  final double latestPrice;
  final double priceChange5d;
  final double priceChange20d;

  ComprehensiveAnalysis({
    required this.stockId,
    required this.stockName,
    required this.market,
    required this.totalScore,
    required this.healthGrade,
    required this.dimensions,
    required this.radar,
    required this.aiSummary,
    required this.latestPrice,
    required this.priceChange5d,
    required this.priceChange20d,
  });

  factory ComprehensiveAnalysis.fromJson(Map<String, dynamic> json) {
    final dimMap = <String, DimensionScore>{};
    final dims = json['dimensions'] as Map<String, dynamic>? ?? {};
    dims.forEach((key, value) {
      dimMap[key] = DimensionScore.fromJson(value as Map<String, dynamic>);
    });

    return ComprehensiveAnalysis(
      stockId: json['stock_id'] ?? '',
      stockName: json['stock_name'] ?? '',
      market: json['market'] ?? 'TW',
      totalScore: (json['total_score'] ?? 0).toDouble(),
      healthGrade: json['health_grade'] ?? 'C',
      dimensions: dimMap,
      radar: RadarData.fromJson(json['radar'] ?? {}),
      aiSummary: json['ai_summary'] ?? '',
      latestPrice: (json['latest_price'] ?? 0).toDouble(),
      priceChange5d: (json['price_change_5d'] ?? 0).toDouble(),
      priceChange20d: (json['price_change_20d'] ?? 0).toDouble(),
    );
  }
}

class DimensionScore {
  final double? score;
  final int? normalized;
  final String signal;
  final double weight;
  final String label;
  final Map<String, dynamic> details;

  DimensionScore({
    this.score,
    this.normalized,
    required this.signal,
    required this.weight,
    required this.label,
    required this.details,
  });

  factory DimensionScore.fromJson(Map<String, dynamic> json) {
    return DimensionScore(
      score: json['score']?.toDouble(),
      normalized: json['normalized']?.toInt(),
      signal: json['signal'] ?? 'N/A',
      weight: (json['weight'] ?? 0).toDouble(),
      label: json['label'] ?? '',
      details: Map<String, dynamic>.from(json['details'] ?? {}),
    );
  }
}

class RadarData {
  final List<String> labels;
  final List<int> values;

  RadarData({required this.labels, required this.values});

  factory RadarData.fromJson(Map<String, dynamic> json) {
    return RadarData(
      labels: List<String>.from(json['labels'] ?? []),
      values: (json['values'] as List? ?? []).map((v) => (v as num).toInt()).toList(),
    );
  }
}
