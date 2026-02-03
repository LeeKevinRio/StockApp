class BullishIndustry {
  final String industry;
  final double probability;
  final String reasoning;
  final List<String> keyFactors;
  final List<String> representativeStocks;
  final List<String> riskFactors;

  BullishIndustry({
    required this.industry,
    required this.probability,
    required this.reasoning,
    required this.keyFactors,
    required this.representativeStocks,
    required this.riskFactors,
  });

  factory BullishIndustry.fromJson(Map<String, dynamic> json) {
    return BullishIndustry(
      industry: json['industry'] ?? '',
      probability: (json['probability'] as num?)?.toDouble() ?? 0.0,
      reasoning: json['reasoning'] ?? '',
      keyFactors: List<String>.from(json['key_factors'] ?? []),
      representativeStocks: List<String>.from(json['representative_stocks'] ?? []),
      riskFactors: List<String>.from(json['risk_factors'] ?? []),
    );
  }
}

class BearishIndustry {
  final String industry;
  final double probability;
  final String reasoning;
  final List<String> keyFactors;
  final List<String> representativeStocks;
  final List<String> avoidReasons;

  BearishIndustry({
    required this.industry,
    required this.probability,
    required this.reasoning,
    required this.keyFactors,
    required this.representativeStocks,
    required this.avoidReasons,
  });

  factory BearishIndustry.fromJson(Map<String, dynamic> json) {
    return BearishIndustry(
      industry: json['industry'] ?? '',
      probability: (json['probability'] as num?)?.toDouble() ?? 0.0,
      reasoning: json['reasoning'] ?? '',
      keyFactors: List<String>.from(json['key_factors'] ?? []),
      representativeStocks: List<String>.from(json['representative_stocks'] ?? []),
      avoidReasons: List<String>.from(json['avoid_reasons'] ?? []),
    );
  }
}

class NeutralIndustry {
  final String industry;
  final String reasoning;

  NeutralIndustry({
    required this.industry,
    required this.reasoning,
  });

  factory NeutralIndustry.fromJson(Map<String, dynamic> json) {
    return NeutralIndustry(
      industry: json['industry'] ?? '',
      reasoning: json['reasoning'] ?? '',
    );
  }
}

class IndustryTrendAnalysis {
  final String analysisDate;
  final String marketOverview;
  final List<BullishIndustry> bullishIndustries;
  final List<BearishIndustry> bearishIndustries;
  final List<NeutralIndustry> neutralIndustries;
  final String investmentSuggestions;
  final String disclaimer;

  IndustryTrendAnalysis({
    required this.analysisDate,
    required this.marketOverview,
    required this.bullishIndustries,
    required this.bearishIndustries,
    required this.neutralIndustries,
    required this.investmentSuggestions,
    required this.disclaimer,
  });

  factory IndustryTrendAnalysis.fromJson(Map<String, dynamic> json) {
    return IndustryTrendAnalysis(
      analysisDate: json['analysis_date'] ?? '',
      marketOverview: json['market_overview'] ?? '',
      bullishIndustries: (json['bullish_industries'] as List?)
              ?.map((e) => BullishIndustry.fromJson(e))
              .toList() ??
          [],
      bearishIndustries: (json['bearish_industries'] as List?)
              ?.map((e) => BearishIndustry.fromJson(e))
              .toList() ??
          [],
      neutralIndustries: (json['neutral_industries'] as List?)
              ?.map((e) => NeutralIndustry.fromJson(e))
              .toList() ??
          [],
      investmentSuggestions: json['investment_suggestions'] ?? '',
      disclaimer: json['disclaimer'] ?? '',
    );
  }
}
