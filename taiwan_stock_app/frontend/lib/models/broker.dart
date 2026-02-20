/// 券商帳戶連動資料模型

class BrokerAccount {
  final bool linked;
  final String? brokerType;
  final String? status;
  final String? accountNumber;
  final DateTime? lastSynced;

  BrokerAccount({
    required this.linked,
    this.brokerType,
    this.status,
    this.accountNumber,
    this.lastSynced,
  });

  factory BrokerAccount.fromJson(Map<String, dynamic> json) {
    return BrokerAccount(
      linked: json['linked'] ?? false,
      brokerType: json['broker_type'],
      status: json['status'],
      accountNumber: json['account_number'],
      lastSynced: json['last_synced'] != null
          ? DateTime.tryParse(json['last_synced'])
          : null,
    );
  }

  factory BrokerAccount.unlinked() => BrokerAccount(linked: false);
}

class BrokerPosition {
  final String symbol;
  final double quantity;
  final double avgCost;
  final double marketValue;
  final double unrealizedPnl;
  final DateTime? lastUpdated;

  BrokerPosition({
    required this.symbol,
    required this.quantity,
    required this.avgCost,
    required this.marketValue,
    required this.unrealizedPnl,
    this.lastUpdated,
  });

  factory BrokerPosition.fromJson(Map<String, dynamic> json) {
    return BrokerPosition(
      symbol: json['symbol'] ?? '',
      quantity: (json['quantity'] ?? 0).toDouble(),
      avgCost: (json['avg_cost'] ?? 0).toDouble(),
      marketValue: (json['market_value'] ?? 0).toDouble(),
      unrealizedPnl: (json['unrealized_pnl'] ?? 0).toDouble(),
      lastUpdated: json['last_updated'] != null
          ? DateTime.tryParse(json['last_updated'])
          : null,
    );
  }

  double get pnlPercent =>
      avgCost > 0 ? (unrealizedPnl / (avgCost * quantity)) * 100 : 0;
  bool get isProfit => unrealizedPnl > 0;
  bool get isLoss => unrealizedPnl < 0;
}

class BrokerLinkResponse {
  final int accountId;
  final String status;
  final String message;

  BrokerLinkResponse({
    required this.accountId,
    required this.status,
    required this.message,
  });

  factory BrokerLinkResponse.fromJson(Map<String, dynamic> json) {
    return BrokerLinkResponse(
      accountId: json['account_id'] ?? 0,
      status: json['status'] ?? '',
      message: json['message'] ?? '',
    );
  }

  bool get needsVerification => status == 'needs_2fa';
  bool get isActive => status == 'active';
  bool get isError => status == 'error';
}
