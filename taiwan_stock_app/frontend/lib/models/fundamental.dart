/// Fundamental data models - 基本面數據相關模型

/// 基本面數據
class FundamentalData {
  final String stockId;
  final String? reportDate;

  // Valuation metrics - 估值指標
  final double? peRatio;          // 本益比
  final double? forwardPe;        // 預估本益比
  final double? pbRatio;          // 股價淨值比
  final double? psRatio;          // 股價營收比
  final double? pegRatio;         // PEG

  // Profitability metrics - 獲利指標
  final double? eps;              // 每股盈餘
  final double? forwardEps;       // 預估EPS
  final double? roe;              // 股東權益報酬率 (%)
  final double? roa;              // 資產報酬率 (%)

  // Revenue metrics - 營收指標
  final double? revenue;          // 營收
  final double? revenueGrowth;    // 營收成長率 (%)
  final double? grossMargin;      // 毛利率 (%)
  final double? operatingMargin;  // 營業利益率 (%)
  final double? netMargin;        // 淨利率 (%)

  // Market data - 市值相關
  final double? marketCap;        // 市值
  final double? enterpriseValue;  // 企業價值
  final double? dividendYield;    // 殖利率 (%)
  final double? beta;             // Beta

  // 52-week range
  final double? week52High;
  final double? week52Low;

  FundamentalData({
    required this.stockId,
    this.reportDate,
    this.peRatio,
    this.forwardPe,
    this.pbRatio,
    this.psRatio,
    this.pegRatio,
    this.eps,
    this.forwardEps,
    this.roe,
    this.roa,
    this.revenue,
    this.revenueGrowth,
    this.grossMargin,
    this.operatingMargin,
    this.netMargin,
    this.marketCap,
    this.enterpriseValue,
    this.dividendYield,
    this.beta,
    this.week52High,
    this.week52Low,
  });

  factory FundamentalData.fromJson(Map<String, dynamic> json) {
    return FundamentalData(
      stockId: json['stock_id'] ?? '',
      reportDate: json['report_date'],
      peRatio: (json['pe_ratio'] as num?)?.toDouble(),
      forwardPe: (json['forward_pe'] as num?)?.toDouble(),
      pbRatio: (json['pb_ratio'] as num?)?.toDouble(),
      psRatio: (json['ps_ratio'] as num?)?.toDouble(),
      pegRatio: (json['peg_ratio'] as num?)?.toDouble(),
      eps: (json['eps'] as num?)?.toDouble(),
      forwardEps: (json['forward_eps'] as num?)?.toDouble(),
      roe: (json['roe'] as num?)?.toDouble(),
      roa: (json['roa'] as num?)?.toDouble(),
      revenue: (json['revenue'] as num?)?.toDouble(),
      revenueGrowth: (json['revenue_growth'] as num?)?.toDouble(),
      grossMargin: (json['gross_margin'] as num?)?.toDouble(),
      operatingMargin: (json['operating_margin'] as num?)?.toDouble(),
      netMargin: (json['net_margin'] as num?)?.toDouble(),
      marketCap: (json['market_cap'] as num?)?.toDouble(),
      enterpriseValue: (json['enterprise_value'] as num?)?.toDouble(),
      dividendYield: (json['dividend_yield'] as num?)?.toDouble(),
      beta: (json['beta'] as num?)?.toDouble(),
      week52High: (json['week_52_high'] as num?)?.toDouble(),
      week52Low: (json['week_52_low'] as num?)?.toDouble(),
    );
  }

  /// Format market cap for display (e.g., 1.5B, 320M)
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

  /// Format revenue for display
  String get formattedRevenue {
    if (revenue == null) return '-';
    if (revenue! >= 1e12) {
      return '${(revenue! / 1e12).toStringAsFixed(2)}T';
    } else if (revenue! >= 1e9) {
      return '${(revenue! / 1e9).toStringAsFixed(2)}B';
    } else if (revenue! >= 1e6) {
      return '${(revenue! / 1e6).toStringAsFixed(2)}M';
    }
    return revenue!.toStringAsFixed(0);
  }
}

/// 股息數據
class DividendData {
  final String stockId;
  final int year;
  final double cashDividend;       // 現金股利
  final double stockDividend;      // 股票股利
  final double totalDividend;      // 合計股利
  final String? exDividendDate;    // 除息日
  final String? paymentDate;       // 發放日
  final double? dividendYield;     // 殖利率 (%)
  final int? paymentCount;         // 發放次數
  final List<DividendPayment> payments;  // 各次發放明細

  DividendData({
    required this.stockId,
    required this.year,
    this.cashDividend = 0,
    this.stockDividend = 0,
    this.totalDividend = 0,
    this.exDividendDate,
    this.paymentDate,
    this.dividendYield,
    this.paymentCount,
    this.payments = const [],
  });

  factory DividendData.fromJson(Map<String, dynamic> json) {
    List<DividendPayment> payments = [];
    if (json['payments'] != null) {
      payments = (json['payments'] as List)
          .map((p) => DividendPayment.fromJson(p))
          .toList();
    }

    return DividendData(
      stockId: json['stock_id'] ?? '',
      year: json['year'] ?? 0,
      cashDividend: (json['cash_dividend'] as num?)?.toDouble() ?? 0,
      stockDividend: (json['stock_dividend'] as num?)?.toDouble() ?? 0,
      totalDividend: (json['total_dividend'] as num?)?.toDouble() ?? 0,
      exDividendDate: json['ex_dividend_date'],
      paymentDate: json['payment_date'],
      dividendYield: (json['dividend_yield'] as num?)?.toDouble(),
      paymentCount: json['payment_count'],
      payments: payments,
    );
  }
}

/// 單次股息發放
class DividendPayment {
  final String date;
  final double amount;

  DividendPayment({
    required this.date,
    required this.amount,
  });

  factory DividendPayment.fromJson(Map<String, dynamic> json) {
    return DividendPayment(
      date: json['date'] ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
    );
  }
}

/// 法人買賣超數據 (台股專用)
class InstitutionalData {
  final String date;
  final int? foreignBuy;      // 外資買
  final int? foreignSell;     // 外資賣
  final int foreignNet;       // 外資淨買賣
  final int? trustBuy;        // 投信買
  final int? trustSell;       // 投信賣
  final int trustNet;         // 投信淨買賣
  final int? dealerBuy;       // 自營商買
  final int? dealerSell;      // 自營商賣
  final int dealerNet;        // 自營商淨買賣
  final int totalNet;         // 三大法人合計

  InstitutionalData({
    required this.date,
    this.foreignBuy,
    this.foreignSell,
    required this.foreignNet,
    this.trustBuy,
    this.trustSell,
    required this.trustNet,
    this.dealerBuy,
    this.dealerSell,
    required this.dealerNet,
    required this.totalNet,
  });

  factory InstitutionalData.fromJson(Map<String, dynamic> json) {
    return InstitutionalData(
      date: json['date'] ?? '',
      foreignBuy: json['foreign_buy'],
      foreignSell: json['foreign_sell'],
      foreignNet: json['foreign_net'] ?? 0,
      trustBuy: json['trust_buy'],
      trustSell: json['trust_sell'],
      trustNet: json['trust_net'] ?? 0,
      dealerBuy: json['dealer_buy'],
      dealerSell: json['dealer_sell'],
      dealerNet: json['dealer_net'] ?? 0,
      totalNet: json['total_net'] ?? 0,
    );
  }

  /// Format net value for display (e.g., +1,234 or -5,678)
  String formatNet(int value) {
    final prefix = value > 0 ? '+' : '';
    return '$prefix${_formatNumber(value)}';
  }

  String _formatNumber(int value) {
    final absValue = value.abs();
    if (absValue >= 1000000) {
      return '${(value / 1000000).toStringAsFixed(1)}M';
    } else if (absValue >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}K';
    }
    return value.toString();
  }
}

/// 融資融券數據 (台股專用)
class MarginData {
  final String date;
  final int? marginBuy;           // 融資買進
  final int? marginSell;          // 融資賣出
  final int marginBalance;        // 融資餘額
  final int? marginLimit;         // 融資限額
  final double? marginUtilization; // 融資使用率 (%)
  final int? shortSell;           // 融券賣出
  final int? shortBuy;            // 融券買進
  final int shortBalance;         // 融券餘額

  MarginData({
    required this.date,
    this.marginBuy,
    this.marginSell,
    required this.marginBalance,
    this.marginLimit,
    this.marginUtilization,
    this.shortSell,
    this.shortBuy,
    required this.shortBalance,
  });

  factory MarginData.fromJson(Map<String, dynamic> json) {
    return MarginData(
      date: json['date'] ?? '',
      marginBuy: json['margin_buy'],
      marginSell: json['margin_sell'],
      marginBalance: json['margin_balance'] ?? 0,
      marginLimit: json['margin_limit'],
      marginUtilization: (json['margin_utilization'] as num?)?.toDouble(),
      shortSell: json['short_sell'],
      shortBuy: json['short_buy'],
      shortBalance: json['short_balance'] ?? 0,
    );
  }

  /// 融資使用率顏色
  /// < 50%: 綠色, 50-70%: 黃色, > 70%: 紅色
  String get utilizationLevel {
    if (marginUtilization == null) return 'normal';
    if (marginUtilization! < 50) return 'low';
    if (marginUtilization! < 70) return 'medium';
    return 'high';
  }
}

/// 財務報表數據
class FinancialStatements {
  final String stockId;
  final List<IncomeStatementItem> incomeStatement;
  final List<BalanceSheetItem> balanceSheet;
  final List<CashFlowItem> cashFlow;

  FinancialStatements({
    required this.stockId,
    this.incomeStatement = const [],
    this.balanceSheet = const [],
    this.cashFlow = const [],
  });

  factory FinancialStatements.fromJson(Map<String, dynamic> json) {
    return FinancialStatements(
      stockId: json['stock_id'] ?? '',
      incomeStatement: (json['income_statement'] as List?)
              ?.map((e) => IncomeStatementItem.fromJson(e))
              .toList() ??
          [],
      balanceSheet: (json['balance_sheet'] as List?)
              ?.map((e) => BalanceSheetItem.fromJson(e))
              .toList() ??
          [],
      cashFlow: (json['cash_flow'] as List?)
              ?.map((e) => CashFlowItem.fromJson(e))
              .toList() ??
          [],
    );
  }
}

/// 損益表項目
class IncomeStatementItem {
  final String period;
  final double? revenue;
  final double? costOfRevenue;
  final double? grossProfit;
  final double? operatingExpense;
  final double? operatingIncome;
  final double? netIncome;
  final double? ebitda;

  IncomeStatementItem({
    required this.period,
    this.revenue,
    this.costOfRevenue,
    this.grossProfit,
    this.operatingExpense,
    this.operatingIncome,
    this.netIncome,
    this.ebitda,
  });

  factory IncomeStatementItem.fromJson(Map<String, dynamic> json) {
    return IncomeStatementItem(
      period: json['period'] ?? '',
      revenue: (json['revenue'] as num?)?.toDouble(),
      costOfRevenue: (json['cost_of_revenue'] as num?)?.toDouble(),
      grossProfit: (json['gross_profit'] as num?)?.toDouble(),
      operatingExpense: (json['operating_expense'] as num?)?.toDouble(),
      operatingIncome: (json['operating_income'] as num?)?.toDouble(),
      netIncome: (json['net_income'] as num?)?.toDouble(),
      ebitda: (json['ebitda'] as num?)?.toDouble(),
    );
  }
}

/// 資產負債表項目
class BalanceSheetItem {
  final String period;
  final double? totalAssets;
  final double? totalLiabilities;
  final double? totalEquity;
  final double? currentAssets;
  final double? currentLiabilities;
  final double? cash;
  final double? totalDebt;

  BalanceSheetItem({
    required this.period,
    this.totalAssets,
    this.totalLiabilities,
    this.totalEquity,
    this.currentAssets,
    this.currentLiabilities,
    this.cash,
    this.totalDebt,
  });

  factory BalanceSheetItem.fromJson(Map<String, dynamic> json) {
    return BalanceSheetItem(
      period: json['period'] ?? '',
      totalAssets: (json['total_assets'] as num?)?.toDouble(),
      totalLiabilities: (json['total_liabilities'] as num?)?.toDouble(),
      totalEquity: (json['total_equity'] as num?)?.toDouble(),
      currentAssets: (json['current_assets'] as num?)?.toDouble(),
      currentLiabilities: (json['current_liabilities'] as num?)?.toDouble(),
      cash: (json['cash'] as num?)?.toDouble(),
      totalDebt: (json['total_debt'] as num?)?.toDouble(),
    );
  }
}

/// 現金流量表項目
class CashFlowItem {
  final String period;
  final double? operatingCashFlow;
  final double? investingCashFlow;
  final double? financingCashFlow;
  final double? freeCashFlow;
  final double? capitalExpenditure;

  CashFlowItem({
    required this.period,
    this.operatingCashFlow,
    this.investingCashFlow,
    this.financingCashFlow,
    this.freeCashFlow,
    this.capitalExpenditure,
  });

  factory CashFlowItem.fromJson(Map<String, dynamic> json) {
    return CashFlowItem(
      period: json['period'] ?? '',
      operatingCashFlow: (json['operating_cash_flow'] as num?)?.toDouble(),
      investingCashFlow: (json['investing_cash_flow'] as num?)?.toDouble(),
      financingCashFlow: (json['financing_cash_flow'] as num?)?.toDouble(),
      freeCashFlow: (json['free_cash_flow'] as num?)?.toDouble(),
      capitalExpenditure: (json['capital_expenditure'] as num?)?.toDouble(),
    );
  }
}
