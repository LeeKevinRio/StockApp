import 'package:flutter/material.dart';

class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('隱私權政策'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (Navigator.of(context).canPop()) {
              Navigator.of(context).pop();
            } else {
              Navigator.of(context).pushReplacementNamed('/home');
            }
          },
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'AI 投資建議 隱私權政策',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              '最後更新日期：2026 年 2 月',
              style: TextStyle(fontSize: 14, color: Theme.of(context).textTheme.bodySmall?.color),
            ),
            const SizedBox(height: 24),
            _buildSection(
              '一、前言',
              '歡迎使用「AI 投資建議」（以下簡稱「本應用程式」）。我們非常重視您的隱私權，並致力於保護您的個人資料。本隱私權政策說明我們如何蒐集、使用、儲存及保護您的個人資訊。使用本應用程式即表示您同意本政策所述之資料處理方式。',
            ),
            _buildSection(
              '二、我們蒐集的資料',
              '我們可能蒐集以下類型的資料：\n\n'
                  '1. 帳戶資訊：當您註冊帳戶時，我們會蒐集您的電子郵件地址及您所設定的密碼（以加密方式儲存）。\n\n'
                  '2. Google 帳戶資訊：若您選擇使用 Google OAuth 登入，我們會透過 Google 取得您的姓名、電子郵件地址及個人頭像圖片網址。我們不會存取您的 Google 帳戶密碼。\n\n'
                  '3. 使用資料：包括您的自選股清單、警示設定、投資組合資料、交易日記、AI 對話紀錄等您在應用程式中主動輸入或操作產生的資料。\n\n'
                  '4. 裝置資訊：我們可能蒐集裝置類型、作業系統版本、應用程式版本等技術資訊，以改善服務品質。',
            ),
            _buildSection(
              '三、資料使用方式',
              '我們蒐集的資料將用於以下目的：\n\n'
                  '1. 提供及維護本應用程式的核心功能，包括股票資訊查詢、AI 投資分析建議、自選股管理、價格警示通知等服務。\n\n'
                  '2. 個人化您的使用體驗，例如根據您的偏好提供市場資訊與 AI 建議。\n\n'
                  '3. 改善應用程式效能與穩定性。\n\n'
                  '4. 與您聯繫有關服務更新、安全通知或技術支援相關事宜。\n\n'
                  '5. 遵守適用法令之要求。',
            ),
            _buildSection(
              '四、AI 分析服務',
              '本應用程式使用 Google Gemini AI 模型為您提供投資分析建議。當您使用 AI 相關功能時：\n\n'
                  '1. 您的查詢內容（如股票代碼、問題等）會傳送至 Google Gemini API 進行處理。\n\n'
                  '2. AI 產生的分析結果僅供參考，不構成任何投資建議或保證。\n\n'
                  '3. Google 可能依其自身隱私權政策處理透過 API 傳送的資料。詳情請參閱 Google 隱私權政策。',
            ),
            _buildSection(
              '五、第三方服務',
              '本應用程式使用以下第三方服務：\n\n'
                  '1. Google OAuth：用於提供 Google 帳號登入功能。相關資料處理受 Google 隱私權政策規範。\n\n'
                  '2. Google Gemini AI：用於提供 AI 投資分析服務。\n\n'
                  '3. 股票資料提供商：用於取得即時及歷史股價資料。\n\n'
                  '我們不會將您的個人資料出售予第三方。',
            ),
            _buildSection(
              '六、資料儲存與安全',
              '1. 您的資料儲存於受保護的伺服器上，我們採用業界標準的安全措施保護您的資料。\n\n'
                  '2. 密碼以雜湊加密方式儲存，我們無法讀取您的原始密碼。\n\n'
                  '3. 我們使用 HTTPS 加密傳輸所有網路通訊。\n\n'
                  '4. 儘管我們盡力保護您的資料安全，但無法保證在網際網路上的傳輸或電子儲存方式是百分之百安全的。',
            ),
            _buildSection(
              '七、資料保留',
              '我們將在您使用本服務期間保留您的個人資料。當您刪除帳戶時，我們將在合理時間內刪除或匿名化您的個人資料，但為遵守法律義務、解決爭議或執行協議所需之資料除外。',
            ),
            _buildSection(
              '八、您的權利',
              '您對您的個人資料享有以下權利：\n\n'
                  '1. 存取權：您可以隨時查看及存取您在應用程式中的個人資料。\n\n'
                  '2. 更正權：您可以更新或修正您的帳戶資訊。\n\n'
                  '3. 刪除權：您可以要求我們刪除您的帳戶及相關資料。\n\n'
                  '4. 撤回同意權：您可以隨時停止使用本應用程式並刪除帳戶。\n\n'
                  '5. 資料可攜權：您可以要求取得您的個人資料副本。',
            ),
            _buildSection(
              '九、兒童隱私',
              '本應用程式不針對未滿 18 歲之未成年人提供服務。我們不會故意蒐集未成年人的個人資料。若您發現有未成年人提供了個人資料給我們，請與我們聯繫，我們將盡速刪除該等資料。',
            ),
            _buildSection(
              '十、政策變更',
              '我們可能不定期更新本隱私權政策。當政策發生重大變更時，我們將透過應用程式內通知或其他適當方式通知您。建議您定期查閱本政策以了解最新內容。',
            ),
            _buildSection(
              '十一、聯絡我們',
              '如果您對本隱私權政策有任何疑問、建議或要求，請透過以下方式聯繫我們：\n\n'
                  '電子郵件：support@stockai-app.com\n\n'
                  '我們將在收到您的來信後，盡速回覆您的詢問。',
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, String content) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            content,
            style: const TextStyle(fontSize: 15, height: 1.6),
          ),
        ],
      ),
    );
  }
}
