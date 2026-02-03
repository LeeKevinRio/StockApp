class User {
  final int id;
  final String email;
  final String? displayName;
  final DateTime createdAt;
  final String authProvider;
  final String? avatarUrl;
  final String subscriptionTier;
  final bool isAdmin;

  User({
    required this.id,
    required this.email,
    this.displayName,
    required this.createdAt,
    this.authProvider = 'local',
    this.avatarUrl,
    this.subscriptionTier = 'free',
    this.isAdmin = false,
  });

  bool get isPro => subscriptionTier == 'pro';
  bool get isGoogleUser => authProvider == 'google';

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      displayName: json['display_name'],
      createdAt: DateTime.parse(json['created_at']),
      authProvider: json['auth_provider'] ?? 'local',
      avatarUrl: json['avatar_url'],
      subscriptionTier: json['subscription_tier'] ?? 'free',
      isAdmin: json['is_admin'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'display_name': displayName,
      'created_at': createdAt.toIso8601String(),
      'auth_provider': authProvider,
      'avatar_url': avatarUrl,
      'subscription_tier': subscriptionTier,
      'is_admin': isAdmin,
    };
  }

  User copyWith({
    int? id,
    String? email,
    String? displayName,
    DateTime? createdAt,
    String? authProvider,
    String? avatarUrl,
    String? subscriptionTier,
    bool? isAdmin,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      createdAt: createdAt ?? this.createdAt,
      authProvider: authProvider ?? this.authProvider,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      subscriptionTier: subscriptionTier ?? this.subscriptionTier,
      isAdmin: isAdmin ?? this.isAdmin,
    );
  }
}
