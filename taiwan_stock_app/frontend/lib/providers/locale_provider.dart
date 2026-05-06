import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 系統級語系設定
/// - 預設中文 (zh-TW)
/// - 可切換英文 (en-US)
/// - **不應隨市場切換而變化**：市場（台股/美股）只決定資料與貨幣，不決定 UI 語言
class LocaleProvider with ChangeNotifier {
  static const String _key = 'app_locale';

  static const Locale zhTW = Locale('zh', 'TW');
  static const Locale enUS = Locale('en', 'US');

  Locale _locale = zhTW;
  bool _initialized = false;

  Locale get locale => _locale;
  bool get isEnglish => _locale.languageCode == 'en';
  bool get isChinese => _locale.languageCode == 'zh';
  bool get initialized => _initialized;

  String get displayName => isEnglish ? 'English' : '繁體中文';

  LocaleProvider() {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final code = prefs.getString(_key);
      if (code == 'en') {
        _locale = enUS;
      } else {
        _locale = zhTW;
      }
    } catch (_) {
      // 讀取失敗時保留預設值
    }
    _initialized = true;
    notifyListeners();
  }

  Future<void> setLocale(Locale locale) async {
    if (_locale == locale) return;
    _locale = locale;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_key, locale.languageCode);
    } catch (_) {
      // 儲存失敗仍保留 in-memory 設定
    }
  }

  /// 取得對應語系字串。
  /// - zh 為必填（預設語系）
  /// - en 可選；當前為英文且 en 有提供時回傳 en，否則 fallback 到 zh
  String tr(String zh, [String? en]) {
    if (isEnglish && en != null) return en;
    return zh;
  }
}
