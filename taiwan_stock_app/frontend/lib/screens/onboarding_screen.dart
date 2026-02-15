import 'package:flutter/material.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _currentPage = 0;

  static const _pages = [
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
            // 跳過按鈕
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: () => _goToLogin(),
                child: const Text('跳過'),
              ),
            ),
            // 頁面
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _pages.length,
                onPageChanged: (i) => setState(() => _currentPage = i),
                itemBuilder: (ctx, i) {
                  final p = _pages[i];
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
                      _pages.length,
                      (i) => Container(
                        width: i == _currentPage ? 24 : 8,
                        height: 8,
                        margin: const EdgeInsets.only(right: 6),
                        decoration: BoxDecoration(
                          color: i == _currentPage
                              ? Theme.of(context).primaryColor
                              : Colors.grey.shade300,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                    ),
                  ),
                  const Spacer(),
                  // 下一步 / 開始按鈕
                  FilledButton(
                    onPressed: () {
                      if (_currentPage == _pages.length - 1) {
                        _goToLogin();
                      } else {
                        _controller.nextPage(
                          duration: const Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        );
                      }
                    },
                    child: Text(
                      _currentPage == _pages.length - 1 ? '開始使用' : '下一步',
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
