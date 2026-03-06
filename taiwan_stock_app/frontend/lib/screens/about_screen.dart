import 'package:flutter/material.dart';

/// 關於本應用程式畫面
class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('關於')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // App 圖示與名稱
          Center(
            child: Column(
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: theme.primaryColor.withAlpha(25),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Icon(
                    Icons.show_chart,
                    size: 40,
                    color: theme.primaryColor,
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  '台股智慧助手',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  '版本 1.0.0',
                  style: TextStyle(fontSize: 14, color: theme.textTheme.bodySmall?.color),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),

          // 應用程式描述
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withAlpha(80),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              '台股智慧助手是一款 AI 驅動的投資分析工具，'
              '提供台股與美股的即時行情、技術分析、AI 建議、'
              '投資組合管理等功能。\n\n'
              '所有 AI 分析結果僅供參考，不構成投資建議。',
              style: TextStyle(fontSize: 14, height: 1.6),
            ),
          ),
          const SizedBox(height: 24),

          // 功能清單
          const _SectionTitle('主要功能'),
          const _FeatureRow(icon: Icons.show_chart, text: '台股 / 美股即時行情'),
          const _FeatureRow(icon: Icons.psychology, text: 'AI 智慧分析與每日建議'),
          const _FeatureRow(icon: Icons.pie_chart, text: '投資組合與損益追蹤'),
          const _FeatureRow(icon: Icons.candlestick_chart, text: 'K 線圖與技術指標'),
          const _FeatureRow(icon: Icons.forum, text: '社群情緒與財經新聞'),
          const _FeatureRow(icon: Icons.book, text: '交易日記與心得紀錄'),
          const SizedBox(height: 24),

          // 技術資訊
          const _SectionTitle('技術資訊'),
          _InfoRow(label: '前端框架', value: 'Flutter'),
          _InfoRow(label: '後端框架', value: 'FastAPI'),
          _InfoRow(label: 'AI 引擎', value: 'Google Gemini / Groq'),
          _InfoRow(label: '資料來源', value: 'TWSE / FinMind / Yahoo Finance'),
          const SizedBox(height: 24),

          // 法律資訊
          const _SectionTitle('法律資訊'),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('隱私權政策'),
            trailing: const Icon(Icons.chevron_right, size: 20),
            onTap: () => Navigator.pushNamed(context, '/privacy'),
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.description_outlined),
            title: const Text('使用條款'),
            trailing: const Icon(Icons.chevron_right, size: 20),
            onTap: () => Navigator.pushNamed(context, '/terms'),
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.source_outlined),
            title: const Text('開放原始碼授權'),
            trailing: const Icon(Icons.chevron_right, size: 20),
            onTap: () => showLicensePage(
              context: context,
              applicationName: '台股智慧助手',
              applicationVersion: '1.0.0',
            ),
          ),
          const SizedBox(height: 32),

          // 版權聲明
          Center(
            child: Text(
              '© 2026 台股智慧助手. All rights reserved.',
              style: TextStyle(fontSize: 12, color: theme.textTheme.bodySmall?.color),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
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
}

class _FeatureRow extends StatelessWidget {
  final IconData icon;
  final String text;
  const _FeatureRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Theme.of(context).primaryColor),
          const SizedBox(width: 12),
          Text(text, style: const TextStyle(fontSize: 14)),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(fontSize: 13, color: Theme.of(context).textTheme.bodySmall?.color),
            ),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 13)),
          ),
        ],
      ),
    );
  }
}
