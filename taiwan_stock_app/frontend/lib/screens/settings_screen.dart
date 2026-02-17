import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';
import '../providers/market_provider.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('設定')),
      body: ListView(
        children: [
          // 個人資料
          _buildProfileSection(context),
          const Divider(height: 1),
          // 外觀
          _buildAppearanceSection(context),
          const Divider(height: 1),
          // 偏好
          _buildPreferencesSection(context),
          const Divider(height: 1),
          // 關於
          _buildAboutSection(context),
          const Divider(height: 1),
          // 帳號操作
          _buildAccountSection(context),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.bold,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  Widget _buildProfileSection(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, _) {
        final user = auth.user;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle(context, '個人資料'),
            ListTile(
              leading: CircleAvatar(
                radius: 24,
                backgroundColor: Colors.blue.shade100,
                child: user?.avatarUrl != null && user!.avatarUrl!.isNotEmpty
                    ? ClipOval(
                        child: Image.network(user.avatarUrl!, width: 48, height: 48, fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => const Icon(Icons.person)),
                      )
                    : const Icon(Icons.person),
              ),
              title: Text(user?.displayName ?? '使用者'),
              subtitle: Text(user?.email ?? ''),
              trailing: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: user?.isPro == true ? Colors.amber : Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  user?.isPro == true ? 'PRO' : 'FREE',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: user?.isPro == true ? Colors.black : Colors.grey,
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildAppearanceSection(BuildContext context) {
    return Consumer<ThemeProvider>(
      builder: (context, theme, _) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle(context, '外觀'),
            ListTile(
              leading: Icon(theme.themeModeIcon),
              title: const Text('主題模式'),
              subtitle: Text(theme.themeModeLabel),
              trailing: SegmentedButton<ThemeMode>(
                segments: const [
                  ButtonSegment(value: ThemeMode.light, icon: Icon(Icons.light_mode, size: 18)),
                  ButtonSegment(value: ThemeMode.system, icon: Icon(Icons.brightness_auto, size: 18)),
                  ButtonSegment(value: ThemeMode.dark, icon: Icon(Icons.dark_mode, size: 18)),
                ],
                selected: {theme.themeMode},
                onSelectionChanged: (set) => theme.setThemeMode(set.first),
                showSelectedIcon: false,
                style: const ButtonStyle(
                  visualDensity: VisualDensity.compact,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildPreferencesSection(BuildContext context) {
    return Consumer<MarketProvider>(
      builder: (context, market, _) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle(context, '偏好設定'),
            ListTile(
              leading: const Icon(Icons.language),
              title: const Text('預設市場'),
              subtitle: Text(market.isUSMarket ? '美股' : '台股'),
              trailing: Switch(
                value: market.isUSMarket,
                onChanged: (_) => market.toggleMarket(),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildAboutSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionTitle(context, '關於'),
        ListTile(
          leading: const Icon(Icons.info_outline),
          title: const Text('關於台股智慧助手'),
          subtitle: const Text('版本 1.0.0'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => Navigator.pushNamed(context, '/about'),
        ),
        ListTile(
          leading: const Icon(Icons.privacy_tip_outlined),
          title: const Text('隱私權政策'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => Navigator.pushNamed(context, '/privacy'),
        ),
        ListTile(
          leading: const Icon(Icons.description_outlined),
          title: const Text('使用條款'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => Navigator.pushNamed(context, '/terms'),
        ),
      ],
    );
  }

  Widget _buildAccountSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionTitle(context, '帳號'),
        ListTile(
          leading: const Icon(Icons.logout, color: Colors.orange),
          title: const Text('登出'),
          onTap: () async {
            final confirm = await showDialog<bool>(
              context: context,
              builder: (ctx) => AlertDialog(
                title: const Text('確認登出'),
                content: const Text('確定要登出嗎？'),
                actions: [
                  TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
                  TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('登出')),
                ],
              ),
            );
            if (confirm == true && context.mounted) {
              await context.read<AuthProvider>().logout();
              if (context.mounted) {
                Navigator.of(context).pushReplacementNamed('/login');
              }
            }
          },
        ),
        ListTile(
          leading: const Icon(Icons.delete_forever, color: Colors.red),
          title: const Text('刪除帳號', style: TextStyle(color: Colors.red)),
          subtitle: const Text('此操作無法復原'),
          onTap: () {
            showDialog(
              context: context,
              builder: (ctx) => AlertDialog(
                title: const Text('刪除帳號'),
                content: const Text(
                  '確定要永久刪除帳號嗎？\n\n'
                  '以下資料將被清除且無法復原：\n'
                  '• 自選股清單\n'
                  '• 投資組合\n'
                  '• AI 分析紀錄\n'
                  '• 交易日記\n'
                  '• 所有警示設定',
                ),
                actions: [
                  TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
                  TextButton(
                    onPressed: () async {
                      Navigator.pop(ctx);
                      try {
                        await context.read<AuthProvider>().deleteAccount();
                        if (context.mounted) {
                          Navigator.of(context).pushReplacementNamed('/login');
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('帳號已成功刪除')),
                          );
                        }
                      } catch (e) {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('刪除失敗：$e')),
                          );
                        }
                      }
                    },
                    child: const Text('確認刪除', style: TextStyle(color: Colors.red)),
                  ),
                ],
              ),
            );
          },
        ),
      ],
    );
  }
}
