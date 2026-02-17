import 'package:flutter/material.dart';

/// App theme configuration for light and dark modes
class AppTheme {
  // Brand colors
  static const Color primaryColor = Color(0xFF0D47A1); // 深藍，辨識度高
  static const Color primaryColorDark = Color(0xFF1565C0);
  static const Color accentColor = Color(0xFF42A5F5);

  // Stock colors (台灣行情：紅漲綠跌)
  static const Color stockRise = Color(0xFFD32F2F);
  static const Color stockFall = Color(0xFF2E7D32);
  static const Color stockFlat = Color(0xFF757575);

  // Chart colors
  static const Color chartMA5 = Color(0xFF2196F3);
  static const Color chartMA10 = Color(0xFFFF9800);
  static const Color chartMA20 = Color(0xFF9C27B0);
  static const Color chartMA60 = Color(0xFF4CAF50);

  // Light theme
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    primaryColor: primaryColor,
    colorScheme: ColorScheme.light(
      primary: primaryColor,
      onPrimary: Colors.white,
      secondary: const Color(0xFF1976D2),
      onSecondary: Colors.white,
      surface: Colors.white,
      onSurface: const Color(0xFF1A1A1A),
      surfaceContainerHighest: const Color(0xFFF0F0F0),
      error: Colors.red.shade700,
      outline: const Color(0xFFBDBDBD),
    ),
    scaffoldBackgroundColor: const Color(0xFFEEF2F6), // 藍灰底，和白 Card 拉開層次
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF0D47A1),
      foregroundColor: Colors.white,
      elevation: 1,
      centerTitle: true,
      titleTextStyle: TextStyle(
        color: Colors.white,
        fontSize: 18,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: Colors.white),
    ),
    cardTheme: CardThemeData(
      elevation: 1,
      color: Colors.white,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: primaryColor,
        side: const BorderSide(color: Color(0xFFBDBDBD)),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: primaryColor,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFBDBDBD)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFBDBDBD)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: primaryColor, width: 2),
      ),
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      labelStyle: const TextStyle(color: Color(0xFF616161)),
      hintStyle: const TextStyle(color: Color(0xFF9E9E9E)),
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(color: Color(0xFF1A1A1A), fontWeight: FontWeight.bold),
      headlineMedium: TextStyle(color: Color(0xFF1A1A1A), fontWeight: FontWeight.bold),
      titleLarge: TextStyle(color: Color(0xFF1A1A1A), fontWeight: FontWeight.w600),
      titleMedium: TextStyle(color: Color(0xFF1A1A1A), fontWeight: FontWeight.w500),
      bodyLarge: TextStyle(color: Color(0xFF333333)),
      bodyMedium: TextStyle(color: Color(0xFF333333)),
      bodySmall: TextStyle(color: Color(0xFF757575)),
      labelLarge: TextStyle(color: Color(0xFF333333), fontWeight: FontWeight.w500),
      labelSmall: TextStyle(color: Color(0xFF757575)),
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: Colors.white,
      unselectedLabelColor: Colors.white70,
      indicatorColor: Colors.white,
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: primaryColor,
      unselectedItemColor: Color(0xFF9E9E9E),
      backgroundColor: Colors.white,
      type: BottomNavigationBarType.fixed,
      elevation: 8,
      selectedLabelStyle: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
    ),
    dividerTheme: const DividerThemeData(
      space: 1,
      thickness: 1,
      color: Color(0xFFE0E0E0),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: const Color(0xFFE8EAF6),
      selectedColor: primaryColor.withAlpha(40),
      labelStyle: const TextStyle(fontSize: 12, color: Color(0xFF333333)),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
    listTileTheme: const ListTileThemeData(
      iconColor: Color(0xFF616161),
      titleTextStyle: TextStyle(fontSize: 15, color: Color(0xFF1A1A1A)),
      subtitleTextStyle: TextStyle(fontSize: 13, color: Color(0xFF757575)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: const Color(0xFF323232),
      contentTextStyle: const TextStyle(color: Colors.white),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
  );

  // Dark theme
  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    primaryColor: accentColor,
    colorScheme: ColorScheme.dark(
      primary: accentColor,
      onPrimary: Colors.white,
      secondary: accentColor,
      onSecondary: Colors.white,
      surface: const Color(0xFF1E1E1E),
      onSurface: const Color(0xFFE0E0E0),
      surfaceContainerHighest: const Color(0xFF2C2C2C),
      error: Colors.red.shade400,
      outline: const Color(0xFF424242),
    ),
    scaffoldBackgroundColor: const Color(0xFF121212),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF1E1E1E),
      foregroundColor: Colors.white,
      elevation: 1,
      centerTitle: true,
      titleTextStyle: TextStyle(
        color: Colors.white,
        fontSize: 18,
        fontWeight: FontWeight.w600,
      ),
    ),
    cardTheme: CardThemeData(
      elevation: 1,
      color: const Color(0xFF1E1E1E),
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: Color(0xFF333333), width: 0.5),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: accentColor,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: accentColor,
        side: const BorderSide(color: Color(0xFF555555)),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: accentColor,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF424242)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF424242)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: accentColor, width: 2),
      ),
      filled: true,
      fillColor: const Color(0xFF2C2C2C),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      labelStyle: const TextStyle(color: Color(0xFFBDBDBD)),
      hintStyle: const TextStyle(color: Color(0xFF757575)),
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
      headlineMedium: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
      titleLarge: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
      titleMedium: TextStyle(color: Color(0xFFE0E0E0), fontWeight: FontWeight.w500),
      bodyLarge: TextStyle(color: Color(0xFFE0E0E0)),
      bodyMedium: TextStyle(color: Color(0xFFBDBDBD)),
      bodySmall: TextStyle(color: Color(0xFF9E9E9E)),
      labelLarge: TextStyle(color: Color(0xFFE0E0E0), fontWeight: FontWeight.w500),
      labelSmall: TextStyle(color: Color(0xFF9E9E9E)),
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: Colors.white,
      unselectedLabelColor: Colors.white60,
      indicatorColor: accentColor,
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: accentColor,
      unselectedItemColor: Color(0xFF757575),
      type: BottomNavigationBarType.fixed,
      backgroundColor: Color(0xFF1E1E1E),
      elevation: 8,
      selectedLabelStyle: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
    ),
    dividerTheme: const DividerThemeData(
      space: 1,
      thickness: 1,
      color: Color(0xFF333333),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: const Color(0xFF2C2C2C),
      selectedColor: accentColor.withAlpha(40),
      labelStyle: const TextStyle(fontSize: 12, color: Color(0xFFE0E0E0)),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
    listTileTheme: const ListTileThemeData(
      iconColor: Color(0xFFBDBDBD),
      titleTextStyle: TextStyle(fontSize: 15, color: Color(0xFFE0E0E0)),
      subtitleTextStyle: TextStyle(fontSize: 13, color: Color(0xFF9E9E9E)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: const Color(0xFF424242),
      contentTextStyle: const TextStyle(color: Colors.white),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
  );

  // Helper method to get stock color
  static Color getStockColor(double? change) {
    if (change == null) return stockFlat;
    if (change > 0) return stockRise;
    if (change < 0) return stockFall;
    return stockFlat;
  }

  // Helper method to get stock color with custom context (for dark/light theme awareness)
  static Color getStockColorForContext(BuildContext context, double? change) {
    if (change == null) return Theme.of(context).disabledColor;
    if (change > 0) return stockRise;
    if (change < 0) return stockFall;
    return Theme.of(context).disabledColor;
  }

  /// 取得次要文字顏色（自動適配深淺主題）
  static Color secondaryTextColor(BuildContext context) {
    return Theme.of(context).textTheme.bodySmall?.color ?? const Color(0xFF757575);
  }

  /// 取得卡片分隔線顏色
  static Color dividerColor(BuildContext context) {
    return Theme.of(context).dividerTheme.color ?? const Color(0xFFE0E0E0);
  }
}
