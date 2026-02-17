import 'package:flutter/material.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _currentPage = 0;
  bool _disclaimerAccepted = false;

  static const _featurePages = [
    _OnboardingPage(
      icon: Icons.show_chart,
      color: Colors.blue,
      title: '即時行情追蹤',
      subtitle: '台股、美股雙市場支援\n自選股即時報價與 K 線圖',
    ),
    _OnboardingPage(
      icon: Icons.psychology,
      color: Colors.purple,
      title: 'AI 智慧分析',
      subtitle: '6 維度綜合分析雷達圖\nAI 每日建議 + 隔日漲跌預測',
    ),
    _OnboardingPage(
      icon: Icons.pie_chart,
      color: Colors.green,
      title: '投資組合管理',
      subtitle: '損益追蹤、持股配置分析\n交易日記記錄心得與情緒',
    ),
    _OnboardingPage(
      icon: Icons.forum,
      color: Colors.orange,
      title: '社群情緒 + 新聞',
      subtitle: 'PTT / Dcard / Reddit 輿情分析\n即時財經新聞與情感摘要',
    ),
  ];

  // 總頁數 = 功能頁 + 免責聲明頁
  int get _totalPages => _featurePages.length + 1;
  bool get _isDisclaimerPage => _currentPage == _totalPages - 1;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // 跳過按鈕（免責聲明頁不顯示）
            Align(
              alignment: Alignment.topRight,
              child: _isDisclaimerPage
                  ? const SizedBox(height: 48)
                  : TextButton(
                      onPressed: () => _goToDisclaimer(),
                      child: const Text('跳過'),
                    ),
            ),
            // 頁面
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _totalPages,
                onPageChanged: (i) => setState(() => _currentPage = i),
                physics: _isDisclaimerPage
                    ? const NeverScrollableScrollPhysics()
                    : null,
                itemBuilder: (ctx, i) {
                  if (i < _featurePages.length) {
                    return _buildFeaturePage(_featurePages[i]);
                  }
                  return _buildDisclaimerPage();
                },
              ),
            ),
            // 指示器 + 按鈕
            Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                children: [
                  // 點點指示器
                  Row(
                    children: List.generate(
                      _totalPages,
                      (i) => Container(
                        width: i == _currentPage ? 24 : 8,
                        height: 8,
                        margin: const EdgeInsets.only(right: 6),
                        decoration: BoxDecoration(
                          color: i == _currentPage
                              ? (_isDisclaimerPage
                                  ? Colors.orange
                                  : Theme.of(context).primaryColor)
                              : const Color(0xFF455A64),
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                    ),
                  ),
                  const Spacer(),
                  // 下一步 / 開始按鈕
                  FilledButton(
                    onPressed: _isDisclaimerPage
                        ? (_disclaimerAccepted ? _goToLogin : null)
                        : _nextPage,
                    child: Text(
                      _isDisclaimerPage ? '我已瞭解，開始使用' : '下一步',
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeaturePage(_OnboardingPage p) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              color: p.color.withAlpha(30),
              shape: BoxShape.circle,
            ),
            child: Icon(p.icon, size: 60, color: p.color),
          ),
          const SizedBox(height: 40),
          Text(
            p.title,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            p.subtitle,
            style: TextStyle(fontSize: 16, color: Colors.grey[600], height: 1.5),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildDisclaimerPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        children: [
          const SizedBox(height: 24),
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: Colors.orange.withAlpha(30),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.warning_amber_rounded,
                size: 50, color: Colors.orange),
          ),
          const SizedBox(height: 24),
          const Text(
            '投資風險聲明',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.orange.withAlpha(15),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.orange.withAlpha(50)),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _DisclaimerItem(
                  text: '本應用程式提供之所有資訊與 AI 分析結果僅供參考，'
                      '不構成任何投資建議或要約。',
                ),
                SizedBox(height: 12),
                _DisclaimerItem(
                  text: '投資涉及風險，過去的表現不代表未來的結果。'
                      '您可能損失部分或全部投入的資金。',
                ),
                SizedBox(height: 12),
                _DisclaimerItem(
                  text: '在做出任何投資決策前，請諮詢合格的財務顧問，'
                      '並評估個人風險承受能力。',
                ),
                SizedBox(height: 12),
                _DisclaimerItem(
                  text: '本應用程式並非經政府核准之投資顧問服務，'
                      '使用者須年滿 18 歲。',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          CheckboxListTile(
            value: _disclaimerAccepted,
            onChanged: (v) => setState(() => _disclaimerAccepted = v ?? false),
            title: const Text(
              '我已閱讀並瞭解上述投資風險聲明',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
            ),
            controlAffinity: ListTileControlAffinity.leading,
            contentPadding: EdgeInsets.zero,
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  void _nextPage() {
    _controller.nextPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _goToDisclaimer() {
    _controller.animateToPage(
      _totalPages - 1,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _goToLogin() {
    Navigator.of(context).pushReplacementNamed('/login');
  }
}

class _OnboardingPage {
  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;

  const _OnboardingPage({
    required this.icon,
    required this.color,
    required this.title,
    required this.subtitle,
  });
}

class _DisclaimerItem extends StatelessWidget {
  final String text;

  const _DisclaimerItem({required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('⚠ ', style: TextStyle(fontSize: 14)),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade800,
              height: 1.5,
            ),
          ),
        ),
      ],
    );
  }
}
