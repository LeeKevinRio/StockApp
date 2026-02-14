import 'package:flutter/material.dart';

class TermsScreen extends StatelessWidget {
  const TermsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('使用條款'),
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
              'AI 投資建議 使用條款',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              '最後更新日期：2025 年 1 月 1 日',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
            const SizedBox(height: 24),
            _buildSection(
              '一、服務說明',
              '「AI 投資建議」（以下簡稱「本應用程式」）是一款提供台股及美股資訊查詢、AI 投資分析、自選股管理、價格警示等功能的行動應用程式。使用本應用程式前，請您仔細閱讀並同意以下使用條款。',
            ),
            _buildSection(
              '二、重要免責聲明 — 非投資建議',
              '本應用程式提供的所有資訊及 AI 分析結果僅供參考用途，不構成任何形式的投資建議、推薦或保證。\n\n'
                  '1. 本應用程式不是經政府主管機關核准之證券投資顧問事業，所提供之分析內容不應被視為專業投資建議。\n\n'
                  '2. AI 模型產生的預測、評分及建議具有不確定性，可能不準確或存在偏差，過去的表現不代表未來的結果。\n\n'
                  '3. 投資涉及風險，包括本金損失的風險。您應根據自身的財務狀況、投資目標及風險承受能力，獨立判斷是否進行任何投資。\n\n'
                  '4. 在做出投資決定前，建議您諮詢合格的財務顧問或證券投資顧問。\n\n'
                  '5. 本應用程式的開發者及營運者不對因依賴本應用程式提供的資訊或建議而導致的任何損失承擔責任。',
            ),
            _buildSection(
              '三、使用者責任',
              '使用本應用程式時，您同意遵守以下規範：\n\n'
                  '1. 您必須年滿 18 歲方可使用本應用程式。\n\n'
                  '2. 您應提供真實、準確的帳戶資訊，並負責維護帳戶安全。\n\n'
                  '3. 您不得利用本應用程式從事任何違法活動，包括但不限於內線交易、市場操縱等行為。\n\n'
                  '4. 您不得嘗試破解、反向工程、複製或未經授權存取本應用程式的系統或資料。\n\n'
                  '5. 您不得利用自動化工具大量擷取本應用程式的資料。\n\n'
                  '6. 您對使用本應用程式所做出的所有投資決策負完全責任。',
            ),
            _buildSection(
              '四、帳戶管理',
              '1. 您有責任保管好您的帳戶憑證，不得與他人分享。\n\n'
                  '2. 如發現帳戶有未經授權的使用情形，請立即通知我們。\n\n'
                  '3. 我們保留在特定情況下暫停或終止您帳戶的權利，包括違反本使用條款的情形。',
            ),
            _buildSection(
              '五、智慧財產權',
              '1. 本應用程式及其所有內容（包括但不限於軟體、設計、文字、圖形、介面、AI 模型及演算法）均為本應用程式開發者或其授權方所有，受著作權法及其他智慧財產權法律保護。\n\n'
                  '2. 您僅被授予有限的、非專屬的、不可轉讓的個人使用權利。\n\n'
                  '3. 未經書面同意，您不得複製、修改、散布、出售或以其他方式利用本應用程式的任何內容。\n\n'
                  '4. 股票資料來源於公開市場資料提供商，相關資料的智慧財產權歸屬原始資料提供方。',
            ),
            _buildSection(
              '六、服務可用性',
              '1. 我們將盡力維持本應用程式的正常運作，但不保證服務不會中斷。\n\n'
                  '2. 我們可能因維護、更新或其他原因暫時中止部分或全部服務。\n\n'
                  '3. 股票資料可能存在延遲，不保證為即時資料。\n\n'
                  '4. 我們保留隨時修改、更新或停止本應用程式任何功能的權利。',
            ),
            _buildSection(
              '七、責任限制',
              '在法律允許的最大範圍內：\n\n'
                  '1. 本應用程式以「現狀」及「可用狀態」提供，不做任何明示或暗示的保證。\n\n'
                  '2. 我們不保證本應用程式提供的資訊完整、準確、即時或可靠。\n\n'
                  '3. 我們不對因使用或無法使用本應用程式而產生的任何直接、間接、附帶、特殊或衍生性損害負責，包括但不限於投資損失、利潤損失或資料損失。\n\n'
                  '4. 在任何情況下，我們的總責任不超過您在過去十二個月內支付給我們的總金額。',
            ),
            _buildSection(
              '八、服務終止',
              '1. 您可以隨時停止使用本應用程式並刪除您的帳戶。\n\n'
                  '2. 我們保留因以下原因終止或暫停您使用本服務的權利：\n'
                  '   - 違反本使用條款\n'
                  '   - 從事欺詐或違法行為\n'
                  '   - 基於安全考量\n'
                  '   - 服務停止營運\n\n'
                  '3. 帳戶終止後，我們將依據隱私權政策處理您的個人資料。',
            ),
            _buildSection(
              '九、條款變更',
              '我們保留隨時修改本使用條款的權利。重大變更將透過應用程式內通知或其他適當方式告知您。繼續使用本應用程式即視為您同意修改後的條款。',
            ),
            _buildSection(
              '十、準據法與管轄',
              '本使用條款受中華民國法律規範。因本條款所生之任何爭議，雙方同意以台灣台北地方法院為第一審管轄法院。',
            ),
            _buildSection(
              '十一、聯絡方式',
              '如果您對本使用條款有任何疑問，請透過以下方式聯繫我們：\n\n'
                  '電子郵件：support@stockai-app.com\n\n'
                  '感謝您使用「AI 投資建議」。',
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
