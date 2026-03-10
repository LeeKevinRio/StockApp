import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../config/app_config.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _isGoogleLoading = false;

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    clientId: AppConfig.googleClientId,
    scopes: ['openid', 'email', 'profile'],
  );

  Future<void> _handleGoogleSignIn() async {
    setState(() {
      _isGoogleLoading = true;
    });

    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        setState(() {
          _isGoogleLoading = false;
        });
        return;
      }

      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      final String? idToken = googleAuth.idToken;
      final String? accessToken = googleAuth.accessToken;

      if (!mounted) return;
      final authProvider = context.read<AuthProvider>();

      if (idToken != null) {
        await authProvider.googleLogin(idToken);
      } else if (accessToken != null) {
        await authProvider.googleLoginWithAccessToken(
          accessToken: accessToken,
          email: googleUser.email,
          displayName: googleUser.displayName,
          photoUrl: googleUser.photoUrl,
        );
      } else {
        throw Exception('無法取得 Google 認證資訊');
      }

      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/home');
      }
    } catch (e) {
      if (mounted) {
        String errorMsg = e.toString();
        // 顯示白名單拒絕的友善訊息
        if (errorMsg.contains('403') || errorMsg.contains('僅開放特定帳號')) {
          errorMsg = '目前僅開放特定帳號登入，正式上線後將開放註冊';
        }
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(errorMsg)),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isGoogleLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo
              Semantics(
                label: 'StockAI 應用程式標誌',
                excludeSemantics: true,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: colorScheme.primary.withAlpha(20),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Icon(
                    Icons.trending_up,
                    size: 48,
                    color: colorScheme.primary,
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                '台股智慧助手',
                style: theme.textTheme.headlineMedium,
              ),
              const SizedBox(height: 4),
              Text(
                'AI 驅動投資分析',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.textTheme.bodySmall?.color,
                ),
              ),
              const SizedBox(height: 48),

              // Google 登入按鈕
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton.icon(
                  onPressed: _isGoogleLoading ? null : _handleGoogleSignIn,
                  icon: _isGoogleLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.g_mobiledata, size: 28),
                  label: const Text(
                    '使用 Google 帳號登入',
                    style: TextStyle(fontSize: 16),
                  ),
                  style: ElevatedButton.styleFrom(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // 提示文字
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: colorScheme.surfaceContainerHighest.withAlpha(80),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.info_outline,
                      size: 16,
                      color: theme.textTheme.bodySmall?.color,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '目前為內測階段，僅開放受邀帳號登入',
                        style: theme.textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // 版本資訊
              Text(
                '免費版使用 Gemini Flash 模型\nPro 版使用 Gemini Pro 模型',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodySmall?.copyWith(fontSize: 12),
              ),
              const SizedBox(height: 16),

              // 條款連結
              Wrap(
                alignment: WrapAlignment.center,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Text(
                    '登入即表示您同意 ',
                    style: theme.textTheme.bodySmall?.copyWith(fontSize: 12),
                  ),
                  Semantics(
                    label: '使用條款',
                    link: true,
                    child: GestureDetector(
                      onTap: () => Navigator.pushNamed(context, '/terms'),
                      child: Text(
                        '使用條款',
                        style: TextStyle(
                          fontSize: 12,
                          color: colorScheme.primary,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                    ),
                  ),
                  Text(
                    ' 和 ',
                    style: theme.textTheme.bodySmall?.copyWith(fontSize: 12),
                  ),
                  Semantics(
                    label: '隱私權政策',
                    link: true,
                    child: GestureDetector(
                      onTap: () => Navigator.pushNamed(context, '/privacy'),
                      child: Text(
                        '隱私權政策',
                        style: TextStyle(
                          fontSize: 12,
                          color: colorScheme.primary,
                          decoration: TextDecoration.underline,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
