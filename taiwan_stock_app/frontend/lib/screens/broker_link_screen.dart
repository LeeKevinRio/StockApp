import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/broker_provider.dart';
import '../models/broker.dart';

class BrokerLinkScreen extends StatefulWidget {
  const BrokerLinkScreen({super.key});

  @override
  State<BrokerLinkScreen> createState() => _BrokerLinkScreenState();
}

class _BrokerLinkScreenState extends State<BrokerLinkScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _pinController = TextEditingController();
  final _codeController = TextEditingController();

  int _step = 0; // 0: 輸入帳密, 1: 2FA, 2: 完成
  int? _pendingAccountId;
  bool _obscurePassword = true;
  bool _obscurePin = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _pinController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _submitCredentials() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      final provider = context.read<BrokerProvider>();
      final result = await provider.linkAccount(
        _usernameController.text.trim(),
        _passwordController.text,
        _pinController.text.trim(),
      );

      if (!mounted) return;

      if (result.isActive) {
        setState(() => _step = 2);
      } else if (result.needsVerification) {
        _pendingAccountId = result.accountId;
        setState(() => _step = 1);
      } else {
        _showError(result.message);
      }
    } catch (e) {
      if (mounted) _showError('連結失敗：$e');
    }
  }

  Future<void> _submit2FA() async {
    final code = _codeController.text.trim();
    if (code.isEmpty || _pendingAccountId == null) return;

    try {
      final provider = context.read<BrokerProvider>();
      final result = await provider.verify2FA(_pendingAccountId!, code);

      if (!mounted) return;

      if (result.isActive) {
        setState(() => _step = 2);
      } else {
        _showError(result.message);
      }
    } catch (e) {
      if (mounted) _showError('驗證失敗：$e');
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('連結 Firstrade')),
      body: Consumer<BrokerProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 步驟指示器
                _buildStepIndicator(theme),
                const SizedBox(height: 32),

                if (_step == 0) _buildCredentialsForm(theme),
                if (_step == 1) _buildVerifyForm(theme),
                if (_step == 2) _buildSuccessView(theme),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildStepIndicator(ThemeData theme) {
    return Row(
      children: [
        _stepCircle(0, '帳密', theme),
        Expanded(child: Divider(color: _step > 0 ? theme.colorScheme.primary : Colors.grey)),
        _stepCircle(1, '2FA', theme),
        Expanded(child: Divider(color: _step > 1 ? theme.colorScheme.primary : Colors.grey)),
        _stepCircle(2, '完成', theme),
      ],
    );
  }

  Widget _stepCircle(int step, String label, ThemeData theme) {
    final isActive = _step >= step;
    return Column(
      children: [
        CircleAvatar(
          radius: 16,
          backgroundColor: isActive ? theme.colorScheme.primary : theme.colorScheme.outline,
          child: isActive
              ? (_step > step
                  ? const Icon(Icons.check, size: 16, color: Colors.white)
                  : Text('${step + 1}', style: const TextStyle(color: Colors.white, fontSize: 12)))
              : Text('${step + 1}', style: TextStyle(color: Theme.of(context).hintColor, fontSize: 12)),
        ),
        const SizedBox(height: 4),
        Text(label, style: TextStyle(fontSize: 11, color: isActive ? theme.colorScheme.primary : Colors.grey)),
      ],
    );
  }

  Widget _buildCredentialsForm(ThemeData theme) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 安全提示
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withOpacity(0.3),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(Icons.shield, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '您的憑證將以加密方式儲存，僅用於同步持倉資料。',
                    style: TextStyle(fontSize: 13, color: theme.colorScheme.onSurface),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          TextFormField(
            controller: _usernameController,
            decoration: const InputDecoration(
              labelText: 'Firstrade 帳號',
              prefixIcon: Icon(Icons.person),
              border: OutlineInputBorder(),
            ),
            validator: (v) => v == null || v.trim().isEmpty ? '請輸入帳號' : null,
          ),
          const SizedBox(height: 16),

          TextFormField(
            controller: _passwordController,
            obscureText: _obscurePassword,
            decoration: InputDecoration(
              labelText: '密碼',
              prefixIcon: const Icon(Icons.lock),
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(
                icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
              ),
            ),
            validator: (v) => v == null || v.isEmpty ? '請輸入密碼' : null,
          ),
          const SizedBox(height: 16),

          TextFormField(
            controller: _pinController,
            obscureText: _obscurePin,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: 'PIN 碼',
              prefixIcon: const Icon(Icons.pin),
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(
                icon: Icon(_obscurePin ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _obscurePin = !_obscurePin),
              ),
            ),
            validator: (v) => v == null || v.trim().isEmpty ? '請輸入 PIN 碼' : null,
          ),
          const SizedBox(height: 24),

          SizedBox(
            width: double.infinity,
            height: 48,
            child: FilledButton(
              onPressed: _submitCredentials,
              child: const Text('連結帳戶'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVerifyForm(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.orange.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Row(
            children: [
              Icon(Icons.sms, color: Colors.orange),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  '請輸入 Firstrade 發送到您手機/郵箱的驗證碼。',
                  style: TextStyle(fontSize: 13),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),

        TextFormField(
          controller: _codeController,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
            labelText: '驗證碼',
            prefixIcon: Icon(Icons.verified_user),
            border: OutlineInputBorder(),
          ),
          autofocus: true,
        ),
        const SizedBox(height: 24),

        SizedBox(
          width: double.infinity,
          height: 48,
          child: FilledButton(
            onPressed: _submit2FA,
            child: const Text('驗證'),
          ),
        ),
      ],
    );
  }

  Widget _buildSuccessView(ThemeData theme) {
    return Column(
      children: [
        const SizedBox(height: 32),
        Icon(Icons.check_circle, size: 80, color: theme.colorScheme.primary),
        const SizedBox(height: 16),
        Text('連結成功！', style: theme.textTheme.headlineSmall),
        const SizedBox(height: 8),
        Text('您的 Firstrade 帳戶已成功連結。',
            style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey)),
        const SizedBox(height: 32),
        SizedBox(
          width: double.infinity,
          height: 48,
          child: FilledButton(
            onPressed: () {
              Navigator.of(context).pushReplacementNamed('/broker');
            },
            child: const Text('查看持倉'),
          ),
        ),
      ],
    );
  }
}
