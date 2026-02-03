/// AI 績效統計數據模型
/// 專業級高風險交易分析平台

/// 類型準確率
class TypeAccuracy {
  final int total;
  final int correct;
  final double accuracy;

  TypeAccuracy({
    required this.total,
    required this.correct,
    required this.accuracy,
  });

  factory TypeAccuracy.fromJson(Map<String, dynamic> json) {
    return TypeAccuracy(
      total: json['total'] ?? 0,
      correct: json['correct'] ?? 0,
      accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0,
    );
  }
}

/// 信心度準確率
class ConfidenceAccuracy {
  final String range;
  final int total;
  final int correct;
  final double accuracy;

  ConfidenceAccuracy({
    required this.range,
    required this.total,
    required this.correct,
    required this.accuracy,
  });

  factory ConfidenceAccuracy.fromJson(Map<String, dynamic> json) {
    return ConfidenceAccuracy(
      range: json['range'] ?? '',
      total: json['total'] ?? 0,
      correct: json['correct'] ?? 0,
      accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0,
    );
  }
}

/// 產業準確率
class IndustryAccuracy {
  final String industry;
  final int total;
  final int correct;
  final double accuracy;

  IndustryAccuracy({
    required this.industry,
    required this.total,
    required this.correct,
    required this.accuracy,
  });

  factory IndustryAccuracy.fromJson(Map<String, dynamic> json) {
    return IndustryAccuracy(
      industry: json['industry'] ?? '',
      total: json['total'] ?? 0,
      correct: json['correct'] ?? 0,
      accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0,
    );
  }
}

/// 準確率趨勢
class AccuracyTrend {
  final String date;
  final double accuracy;
  final int count;

  AccuracyTrend({
    required this.date,
    required this.accuracy,
    required this.count,
  });

  factory AccuracyTrend.fromJson(Map<String, dynamic> json) {
    return AccuracyTrend(
      date: json['date'] ?? '',
      accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0,
      count: json['count'] ?? 0,
    );
  }

  DateTime get dateTime => DateTime.parse(date);
}

/// AI 績效報告
class PerformanceReport {
  final int totalSuggestions;
  final int evaluatedCount;
  final int correctCount;
  final double overallAccuracy;
  final Map<String, TypeAccuracy> byType;
  final List<ConfidenceAccuracy> byConfidence;
  final List<IndustryAccuracy> byIndustry;
  final List<AccuracyTrend> trends;
  final int periodDays;

  PerformanceReport({
    required this.totalSuggestions,
    required this.evaluatedCount,
    required this.correctCount,
    required this.overallAccuracy,
    required this.byType,
    required this.byConfidence,
    required this.byIndustry,
    required this.trends,
    required this.periodDays,
  });

  factory PerformanceReport.fromJson(Map<String, dynamic> json) {
    // 解析 byType
    final byTypeJson = json['by_type'] as Map<String, dynamic>? ?? {};
    final byType = <String, TypeAccuracy>{};
    byTypeJson.forEach((key, value) {
      byType[key] = TypeAccuracy.fromJson(value);
    });

    // 解析 byConfidence
    final byConfidenceJson = json['by_confidence'] as List? ?? [];
    final byConfidence = byConfidenceJson
        .map((e) => ConfidenceAccuracy.fromJson(e))
        .toList();

    // 解析 byIndustry
    final byIndustryJson = json['by_industry'] as List? ?? [];
    final byIndustry = byIndustryJson
        .map((e) => IndustryAccuracy.fromJson(e))
        .toList();

    // 解析 trends
    final trendsJson = json['trends'] as List? ?? [];
    final trends = trendsJson
        .map((e) => AccuracyTrend.fromJson(e))
        .toList();

    return PerformanceReport(
      totalSuggestions: json['total_suggestions'] ?? 0,
      evaluatedCount: json['evaluated_count'] ?? 0,
      correctCount: json['correct_count'] ?? 0,
      overallAccuracy: (json['overall_accuracy'] as num?)?.toDouble() ?? 0,
      byType: byType,
      byConfidence: byConfidence,
      byIndustry: byIndustry,
      trends: trends,
      periodDays: json['period_days'] ?? 30,
    );
  }

  /// BUY 類型準確率
  TypeAccuracy? get buyAccuracy => byType['BUY'];

  /// SELL 類型準確率
  TypeAccuracy? get sellAccuracy => byType['SELL'];

  /// HOLD 類型準確率
  TypeAccuracy? get holdAccuracy => byType['HOLD'];

  /// 評估覆蓋率
  double get evaluationCoverage {
    return totalSuggestions > 0
        ? evaluatedCount / totalSuggestions * 100
        : 0;
  }

  /// 未評估數量
  int get unevaluatedCount => totalSuggestions - evaluatedCount;

  /// 最佳產業
  IndustryAccuracy? get bestIndustry {
    if (byIndustry.isEmpty) return null;
    return byIndustry.reduce((a, b) => a.accuracy > b.accuracy ? a : b);
  }

  /// 最差產業
  IndustryAccuracy? get worstIndustry {
    if (byIndustry.isEmpty) return null;
    return byIndustry.reduce((a, b) => a.accuracy < b.accuracy ? a : b);
  }
}

/// 記錄建議結果請求
class RecordResultRequest {
  final bool isCorrect;
  final double? actualReturn;
  final String? notes;

  RecordResultRequest({
    required this.isCorrect,
    this.actualReturn,
    this.notes,
  });

  Map<String, dynamic> toJson() {
    return {
      'is_correct': isCorrect,
      if (actualReturn != null) 'actual_return': actualReturn,
      if (notes != null) 'notes': notes,
    };
  }
}
