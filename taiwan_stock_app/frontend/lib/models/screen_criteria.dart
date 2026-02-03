/// Stock screener models - 股票篩選器相關模型

/// 篩選條件
class ScreenCriteria {
  double? peMin;
  double? peMax;
  double? pbMin;
  double? pbMax;
  double? dividendYieldMin;
  double? roeMin;
  double? roaMin;
  double? grossMarginMin;
  double? revenueGrowthMin;
  double? marketCapMin;
  double? marketCapMax;
  String? industry;

  ScreenCriteria({
    this.peMin,
    this.peMax,
    this.pbMin,
    this.pbMax,
    this.dividendYieldMin,
    this.roeMin,
    this.roaMin,
    this.grossMarginMin,
    this.revenueGrowthMin,
    this.marketCapMin,
    this.marketCapMax,
    this.industry,
  });

  /// Convert to JSON for API request
  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    if (peMin != null) map['pe_min'] = peMin;
    if (peMax != null) map['pe_max'] = peMax;
    if (pbMin != null) map['pb_min'] = pbMin;
    if (pbMax != null) map['pb_max'] = pbMax;
    if (dividendYieldMin != null) map['dividend_yield_min'] = dividendYieldMin;
    if (roeMin != null) map['roe_min'] = roeMin;
    if (roaMin != null) map['roa_min'] = roaMin;
    if (grossMarginMin != null) map['gross_margin_min'] = grossMarginMin;
    if (revenueGrowthMin != null) map['revenue_growth_min'] = revenueGrowthMin;
    if (marketCapMin != null) map['market_cap_min'] = marketCapMin;
    if (marketCapMax != null) map['market_cap_max'] = marketCapMax;
    if (industry != null && industry!.isNotEmpty) map['industry'] = industry;
    return map;
  }

  factory ScreenCriteria.fromJson(Map<String, dynamic> json) {
    return ScreenCriteria(
      peMin: (json['pe_min'] as num?)?.toDouble(),
      peMax: (json['pe_max'] as num?)?.toDouble(),
      pbMin: (json['pb_min'] as num?)?.toDouble(),
      pbMax: (json['pb_max'] as num?)?.toDouble(),
      dividendYieldMin: (json['dividend_yield_min'] as num?)?.toDouble(),
      roeMin: (json['roe_min'] as num?)?.toDouble(),
      roaMin: (json['roa_min'] as num?)?.toDouble(),
      grossMarginMin: (json['gross_margin_min'] as num?)?.toDouble(),
      revenueGrowthMin: (json['revenue_growth_min'] as num?)?.toDouble(),
      marketCapMin: (json['market_cap_min'] as num?)?.toDouble(),
      marketCapMax: (json['market_cap_max'] as num?)?.toDouble(),
      industry: json['industry'],
    );
  }

  /// Check if any criteria is set
  bool get isEmpty =>
      peMin == null &&
      peMax == null &&
      pbMin == null &&
      pbMax == null &&
      dividendYieldMin == null &&
      roeMin == null &&
      roaMin == null &&
      grossMarginMin == null &&
      revenueGrowthMin == null &&
      marketCapMin == null &&
      marketCapMax == null &&
      (industry == null || industry!.isEmpty);

  /// Create a copy with updated values
  ScreenCriteria copyWith({
    double? peMin,
    double? peMax,
    double? pbMin,
    double? pbMax,
    double? dividendYieldMin,
    double? roeMin,
    double? roaMin,
    double? grossMarginMin,
    double? revenueGrowthMin,
    double? marketCapMin,
    double? marketCapMax,
    String? industry,
  }) {
    return ScreenCriteria(
      peMin: peMin ?? this.peMin,
      peMax: peMax ?? this.peMax,
      pbMin: pbMin ?? this.pbMin,
      pbMax: pbMax ?? this.pbMax,
      dividendYieldMin: dividendYieldMin ?? this.dividendYieldMin,
      roeMin: roeMin ?? this.roeMin,
      roaMin: roaMin ?? this.roaMin,
      grossMarginMin: grossMarginMin ?? this.grossMarginMin,
      revenueGrowthMin: revenueGrowthMin ?? this.revenueGrowthMin,
      marketCapMin: marketCapMin ?? this.marketCapMin,
      marketCapMax: marketCapMax ?? this.marketCapMax,
      industry: industry ?? this.industry,
    );
  }

  /// Reset all criteria
  void reset() {
    peMin = null;
    peMax = null;
    pbMin = null;
    pbMax = null;
    dividendYieldMin = null;
    roeMin = null;
    roaMin = null;
    grossMarginMin = null;
    revenueGrowthMin = null;
    marketCapMin = null;
    marketCapMax = null;
    industry = null;
  }
}

/// 預設篩選條件
class PresetScreen {
  final String id;
  final String name;
  final String nameEn;
  final String description;
  final ScreenCriteria criteria;

  PresetScreen({
    required this.id,
    required this.name,
    required this.nameEn,
    required this.description,
    required this.criteria,
  });

  factory PresetScreen.fromJson(Map<String, dynamic> json) {
    return PresetScreen(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      nameEn: json['name_en'] ?? '',
      description: json['description'] ?? '',
      criteria: ScreenCriteria.fromJson(json['criteria'] ?? {}),
    );
  }
}

/// 篩選結果項目
class ScreenResultItem {
  final String stockId;
  final String name;
  final String? industry;
  final String? market;
  final String marketRegion;
  final double? peRatio;
  final double? pbRatio;
  final double? eps;
  final double? roe;
  final double? roa;
  final double? grossMargin;
  final double? marketCap;
  final double? dividendYield;
  final double? totalDividend;
  final String? reportDate;

  ScreenResultItem({
    required this.stockId,
    required this.name,
    this.industry,
    this.market,
    this.marketRegion = 'TW',
    this.peRatio,
    this.pbRatio,
    this.eps,
    this.roe,
    this.roa,
    this.grossMargin,
    this.marketCap,
    this.dividendYield,
    this.totalDividend,
    this.reportDate,
  });

  factory ScreenResultItem.fromJson(Map<String, dynamic> json) {
    return ScreenResultItem(
      stockId: json['stock_id'] ?? '',
      name: json['name'] ?? '',
      industry: json['industry'],
      market: json['market'],
      marketRegion: json['market_region'] ?? 'TW',
      peRatio: (json['pe_ratio'] as num?)?.toDouble(),
      pbRatio: (json['pb_ratio'] as num?)?.toDouble(),
      eps: (json['eps'] as num?)?.toDouble(),
      roe: (json['roe'] as num?)?.toDouble(),
      roa: (json['roa'] as num?)?.toDouble(),
      grossMargin: (json['gross_margin'] as num?)?.toDouble(),
      marketCap: (json['market_cap'] as num?)?.toDouble(),
      dividendYield: (json['dividend_yield'] as num?)?.toDouble(),
      totalDividend: (json['total_dividend'] as num?)?.toDouble(),
      reportDate: json['report_date'],
    );
  }

  /// Format market cap for display
  String get formattedMarketCap {
    if (marketCap == null) return '-';
    if (marketCap! >= 1e12) {
      return '${(marketCap! / 1e12).toStringAsFixed(2)}T';
    } else if (marketCap! >= 1e9) {
      return '${(marketCap! / 1e9).toStringAsFixed(2)}B';
    } else if (marketCap! >= 1e6) {
      return '${(marketCap! / 1e6).toStringAsFixed(2)}M';
    }
    return marketCap!.toStringAsFixed(0);
  }

  bool get isUSStock => marketRegion.toUpperCase() == 'US';
}

/// 篩選響應
class ScreenResponse {
  final int total;
  final List<ScreenResultItem> stocks;

  ScreenResponse({
    required this.total,
    required this.stocks,
  });

  factory ScreenResponse.fromJson(Map<String, dynamic> json) {
    return ScreenResponse(
      total: json['total'] ?? 0,
      stocks: (json['stocks'] as List?)
              ?.map((e) => ScreenResultItem.fromJson(e))
              .toList() ??
          [],
    );
  }
}
