import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/ai_config.dart';

class AISettingsScreen extends StatefulWidget {
  const AISettingsScreen({super.key});

  @override
  State<AISettingsScreen> createState() => _AISettingsScreenState();
}

class _AISettingsScreenState extends State<AISettingsScreen> {
  List<AIProviderInfo> _providers = [];
  AIConfig? _currentConfig;
  bool _loading = true;
  String? _error;

  String? _selectedProvider;
  String? _selectedModel;
  final _apiKeyController = TextEditingController();
  bool _obscureKey = true;
  bool _saving = false;
  bool _testing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadData());
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    final api = context.read<ApiService>();
    try {
      final results = await Future.wait([
        api.getAIProviders(),
        api.getAIConfig(),
      ]);

      final providersRaw = results[0] as List<Map<String, dynamic>>;
      final configRaw = results[1] as Map<String, dynamic>;

      final providers = providersRaw.map((p) => AIProviderInfo.fromJson(p)).toList();
      final config = AIConfig.fromJson(configRaw);

      setState(() {
        _providers = providers;
        _currentConfig = config;
        _loading = false;
        if (config.hasApiKey && config.provider != null) {
          _selectedProvider = config.provider;
          _selectedModel = config.model;
        }
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  List<AIModelInfo> get _availableModels {
    if (_selectedProvider == null) return [];
    final provider = _providers.where((p) => p.id == _selectedProvider).firstOrNull;
    return provider?.models ?? [];
  }

  Future<void> _save() async {
    if (_selectedProvider == null || _selectedModel == null) {
      _showSnack('請選擇 Provider 和 Model');
      return;
    }
    final apiKey = _apiKeyController.text.trim();
    if (apiKey.isEmpty && !(_currentConfig?.hasApiKey ?? false)) {
      _showSnack('請輸入 API Key');
      return;
    }

    // 如果沒有輸入新 key 但已有舊 key，只更新 provider/model
    // 後端要求 api_key，所以如果不輸入新 key 就不能改
    if (apiKey.isEmpty) {
      _showSnack('變更設定需要重新輸入 API Key');
      return;
    }

    setState(() => _saving = true);
    try {
      final api = context.read<ApiService>();
      await api.saveAIConfig(
        provider: _selectedProvider!,
        model: _selectedModel!,
        apiKey: apiKey,
      );
      _apiKeyController.clear();
      await _loadData();
      if (mounted) _showSnack('AI 設定已儲存', isError: false);
    } catch (e) {
      _showSnack('儲存失敗：$e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _test() async {
    if (_selectedProvider == null || _selectedModel == null) {
      _showSnack('請選擇 Provider 和 Model');
      return;
    }
    final apiKey = _apiKeyController.text.trim();
    if (apiKey.isEmpty) {
      _showSnack('請輸入 API Key 以進行測試');
      return;
    }

    setState(() => _testing = true);
    try {
      final api = context.read<ApiService>();
      final result = await api.testAIConfig(
        provider: _selectedProvider!,
        model: _selectedModel!,
        apiKey: apiKey,
      );
      final success = result['success'] == true;
      final message = result['message'] ?? '';
      if (mounted) {
        _showSnack(message, isError: !success);
      }
    } catch (e) {
      _showSnack('測試失敗：$e');
    } finally {
      if (mounted) setState(() => _testing = false);
    }
  }

  Future<void> _resetToDefault() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('恢復預設'),
        content: const Text('確定要刪除自訂 AI 設定，恢復使用系統預設嗎？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('確定')),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      final api = context.read<ApiService>();
      await api.deleteAIConfig();
      _apiKeyController.clear();
      setState(() {
        _selectedProvider = null;
        _selectedModel = null;
      });
      await _loadData();
      if (mounted) _showSnack('已恢復系統預設 AI 設定', isError: false);
    } catch (e) {
      _showSnack('操作失敗：$e');
    }
  }

  void _showSnack(String msg, {bool isError = true}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: isError ? Colors.red : Colors.green,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI 設定')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text('載入失敗：$_error'))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildStatusCard(),
                    const SizedBox(height: 20),
                    _buildConfigForm(),
                    const SizedBox(height: 24),
                    _buildActions(),
                    const SizedBox(height: 32),
                  ],
                ),
    );
  }

  Widget _buildStatusCard() {
    final config = _currentConfig;
    final isCustom = config?.hasApiKey ?? false;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              isCustom ? Icons.key : Icons.cloud,
              size: 32,
              color: isCustom ? Colors.amber : Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isCustom ? '使用自訂 API Key' : '使用系統預設',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    isCustom
                        ? '${config!.providerLabel ?? config.provider} / ${config.model}'
                        : '目前使用系統提供的 AI 服務',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            if (isCustom)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.amber.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text('BYOK', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildConfigForm() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('自訂 AI 設定', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 16),

            // Provider 下拉
            DropdownButtonFormField<String>(
              value: _selectedProvider,
              decoration: const InputDecoration(
                labelText: 'AI Provider',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.smart_toy),
              ),
              items: _providers.map((p) {
                return DropdownMenuItem(value: p.id, child: Text(p.label));
              }).toList(),
              onChanged: (val) {
                setState(() {
                  _selectedProvider = val;
                  _selectedModel = null; // 重選 provider 時清除 model
                });
              },
            ),
            const SizedBox(height: 16),

            // Model 下拉
            DropdownButtonFormField<String>(
              value: _selectedModel,
              decoration: const InputDecoration(
                labelText: 'Model',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.memory),
              ),
              items: _availableModels.map((m) {
                return DropdownMenuItem(value: m.id, child: Text(m.label));
              }).toList(),
              onChanged: _selectedProvider == null ? null : (val) {
                setState(() => _selectedModel = val);
              },
            ),
            const SizedBox(height: 16),

            // API Key
            TextField(
              controller: _apiKeyController,
              obscureText: _obscureKey,
              decoration: InputDecoration(
                labelText: 'API Key',
                hintText: (_currentConfig?.hasApiKey ?? false)
                    ? '已設定（輸入新 Key 可更換）'
                    : '輸入你的 API Key',
                border: const OutlineInputBorder(),
                prefixIcon: const Icon(Icons.vpn_key),
                suffixIcon: IconButton(
                  icon: Icon(_obscureKey ? Icons.visibility_off : Icons.visibility),
                  onPressed: () => setState(() => _obscureKey = !_obscureKey),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActions() {
    return Column(
      children: [
        // 測試 + 儲存
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _testing ? null : _test,
                icon: _testing
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.science),
                label: Text(_testing ? '測試中...' : '測試連線'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton.icon(
                onPressed: _saving ? null : _save,
                icon: _saving
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.save),
                label: Text(_saving ? '儲存中...' : '儲存設定'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        // 恢復預設
        if (_currentConfig?.hasApiKey ?? false)
          SizedBox(
            width: double.infinity,
            child: TextButton.icon(
              onPressed: _resetToDefault,
              icon: const Icon(Icons.restore, color: Colors.red),
              label: const Text('恢復系統預設', style: TextStyle(color: Colors.red)),
            ),
          ),
      ],
    );
  }
}
