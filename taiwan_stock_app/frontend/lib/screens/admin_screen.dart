import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  List<Map<String, dynamic>> _users = [];
  Map<String, dynamic>? _stats;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final results = await Future.wait([
        apiService.getAdminUsers(),
        apiService.getAdminStats(),
      ]);

      setState(() {
        _users = results[0] as List<Map<String, dynamic>>;
        _stats = results[1] as Map<String, dynamic>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _updateSubscription(int userId, String tier) async {
    try {
      final apiService = context.read<ApiService>();
      await apiService.updateUserSubscription(userId, tier);
      await _loadData();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('訂閱等級已更新')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('更新失敗: $e')),
        );
      }
    }
  }

  Future<void> _toggleAdmin(int userId, bool isAdmin) async {
    try {
      final apiService = context.read<ApiService>();
      await apiService.updateUserAdmin(userId, isAdmin);
      await _loadData();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(isAdmin ? '已設為管理員' : '已移除管理員權限')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('更新失敗: $e')),
        );
      }
    }
  }

  /// 將最後登入時間格式化為相對時間
  String _formatLastLogin(String? lastLoginAt) {
    if (lastLoginAt == null) return '從未登入';
    try {
      final dt = DateTime.parse(lastLoginAt).toLocal();
      final now = DateTime.now();
      final diff = now.difference(dt);

      if (diff.inMinutes < 1) return '剛剛';
      if (diff.inMinutes < 60) return '${diff.inMinutes} 分鐘前';
      if (diff.inHours < 24) return '${diff.inHours} 小時前';
      if (diff.inDays < 7) return '${diff.inDays} 天前';
      if (diff.inDays < 30) return '${(diff.inDays / 7).floor()} 週前';
      return '${dt.month}/${dt.day}';
    } catch (_) {
      return '未知';
    }
  }

  /// 判斷用戶是否為活躍狀態（24小時內登入）
  bool _isActiveRecently(String? lastLoginAt) {
    if (lastLoginAt == null) return false;
    try {
      final dt = DateTime.parse(lastLoginAt);
      return DateTime.now().toUtc().difference(dt).inHours < 24;
    } catch (_) {
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();

    if (!authProvider.isAdmin) {
      return Scaffold(
        appBar: AppBar(title: const Text('管理後台')),
        body: const Center(
          child: Text('您沒有權限訪問此頁面'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('管理後台'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('錯誤: $_error'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadData,
                        child: const Text('重試'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildStatsSection(),
                        const SizedBox(height: 16),
                        _buildActivitySection(),
                        const SizedBox(height: 24),
                        _buildUsersSection(),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildStatsSection() {
    if (_stats == null) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '統計資訊',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildStatCard(
                  '總用戶數',
                  '${_stats!['total_users'] ?? 0}',
                  Icons.people,
                  Colors.blue,
                ),
                const SizedBox(width: 16),
                _buildStatCard(
                  'Pro 用戶',
                  '${_stats!['pro_users'] ?? 0}',
                  Icons.star,
                  Colors.amber,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildStatCard(
                  'Google 用戶',
                  '${_stats!['google_users'] ?? 0}',
                  Icons.g_mobiledata,
                  Colors.red,
                ),
                const SizedBox(width: 16),
                _buildStatCard(
                  '本地用戶',
                  '${_stats!['local_users'] ?? 0}',
                  Icons.email,
                  Colors.green,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// 活躍度統計區塊
  Widget _buildActivitySection() {
    if (_stats == null) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '用戶活躍度',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildStatCard(
                  '今日活躍',
                  '${_stats!['active_today'] ?? 0}',
                  Icons.flash_on,
                  Colors.orange,
                ),
                const SizedBox(width: 16),
                _buildStatCard(
                  '7日活躍',
                  '${_stats!['active_7d'] ?? 0}',
                  Icons.date_range,
                  Colors.teal,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildStatCard(
                  '30日活躍',
                  '${_stats!['active_30d'] ?? 0}',
                  Icons.calendar_month,
                  Colors.purple,
                ),
                const SizedBox(width: 16),
                const Expanded(child: SizedBox.shrink()),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(
    String label,
    String value,
    IconData icon,
    Color color,
  ) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).textTheme.bodySmall?.color,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUsersSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '用戶列表',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  '共 ${_users.length} 位用戶',
                  style: TextStyle(
                    color: Theme.of(context).textTheme.bodySmall?.color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _users.length,
              separatorBuilder: (context, index) => const Divider(),
              itemBuilder: (context, index) {
                final user = _users[index];
                return _buildUserTile(user);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUserTile(Map<String, dynamic> user) {
    final authProvider = context.read<AuthProvider>();
    final currentUserId = authProvider.user?.id;
    final isCurrentUser = user['id'] == currentUserId;
    final lastLogin = user['last_login_at'] as String?;
    final isActive = _isActiveRecently(lastLogin);

    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Stack(
        children: [
          CircleAvatar(
            backgroundColor: Colors.blue.shade100,
            backgroundImage: user['avatar_url'] != null
                ? NetworkImage(user['avatar_url'])
                : null,
            child: user['avatar_url'] == null
                ? Text(
                    (user['email'] as String).substring(0, 1).toUpperCase(),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  )
                : null,
          ),
          // 線上狀態指示器
          Positioned(
            right: 0,
            bottom: 0,
            child: Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: isActive ? Colors.green : Colors.grey,
                shape: BoxShape.circle,
                border: Border.all(
                  color: Theme.of(context).cardColor,
                  width: 2,
                ),
              ),
            ),
          ),
        ],
      ),
      title: Row(
        children: [
          Expanded(
            child: Text(
              user['display_name'] ?? user['email'],
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (user['is_admin'] == true)
            Container(
              margin: const EdgeInsets.only(left: 8),
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.red,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text(
                'Admin',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                ),
              ),
            ),
        ],
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            user['email'],
            style: const TextStyle(fontSize: 12),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: user['subscription_tier'] == 'pro'
                      ? Colors.amber
                      : const Color(0xFF455A64),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  user['subscription_tier']?.toUpperCase() ?? 'FREE',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: user['subscription_tier'] == 'pro'
                        ? Colors.black
                        : Theme.of(context).hintColor,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: user['auth_provider'] == 'google'
                      ? Colors.red.shade100
                      : Colors.blue.shade100,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  user['auth_provider'] == 'google' ? 'Google' : 'Local',
                  style: TextStyle(
                    fontSize: 10,
                    color: user['auth_provider'] == 'google'
                        ? Colors.red.shade700
                        : Colors.blue.shade700,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              // 最後登入時間
              Icon(
                Icons.access_time,
                size: 12,
                color: Theme.of(context).textTheme.bodySmall?.color,
              ),
              const SizedBox(width: 2),
              Text(
                _formatLastLogin(lastLogin),
                style: TextStyle(
                  fontSize: 10,
                  color: isActive ? Colors.green : Theme.of(context).textTheme.bodySmall?.color,
                ),
              ),
            ],
          ),
        ],
      ),
      trailing: isCurrentUser
          ? const Chip(
              label: Text('你', style: TextStyle(fontSize: 12)),
              backgroundColor: Colors.blue,
              labelStyle: TextStyle(color: Colors.white),
            )
          : PopupMenuButton<String>(
              onSelected: (value) {
                switch (value) {
                  case 'set_pro':
                    _updateSubscription(user['id'], 'pro');
                    break;
                  case 'set_free':
                    _updateSubscription(user['id'], 'free');
                    break;
                  case 'toggle_admin':
                    _toggleAdmin(user['id'], !(user['is_admin'] ?? false));
                    break;
                }
              },
              itemBuilder: (context) => [
                if (user['subscription_tier'] != 'pro')
                  const PopupMenuItem(
                    value: 'set_pro',
                    child: Row(
                      children: [
                        Icon(Icons.star, color: Colors.amber),
                        SizedBox(width: 8),
                        Text('升級為 Pro'),
                      ],
                    ),
                  ),
                if (user['subscription_tier'] == 'pro')
                  const PopupMenuItem(
                    value: 'set_free',
                    child: Row(
                      children: [
                        Icon(Icons.star_border),
                        SizedBox(width: 8),
                        Text('降級為 Free'),
                      ],
                    ),
                  ),
                PopupMenuItem(
                  value: 'toggle_admin',
                  child: Row(
                    children: [
                      Icon(
                        user['is_admin'] == true
                            ? Icons.remove_moderator
                            : Icons.admin_panel_settings,
                        color: user['is_admin'] == true
                            ? Colors.grey
                            : Colors.red,
                      ),
                      const SizedBox(width: 8),
                      Text(user['is_admin'] == true ? '移除管理員' : '設為管理員'),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
