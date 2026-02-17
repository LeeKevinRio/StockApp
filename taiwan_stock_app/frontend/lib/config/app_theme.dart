import 'package:flutter/material.dart';

/// App 主題配置 — 深色金融風格
class AppTheme {
  // Brand colors
  static const Color primaryColor = Color(0xFF1B5E20); // 深綠（金融穩重）
  static const Color accentColor = Color(0xFF66BB6A); // 亮綠（行動按鈕）
  static const Color goldAccent = Color(0xFFFFB300); // 金色點綴

  // Stock colors (台灣行情：紅漲綠跌)
  static const Color stockRise = Color(0xFFEF5350);
  static const Color stockFall = Color(0xFF26A69A);
  static const Color stockFlat = Color(0xFF9E9E9E);

  // Chart colors
  static const Color chartMA5 = Color(0xFF42A5F5);
  static const Color chartMA10 = Color(0xFFFF9800);
  static const Color chartMA20 = Color(0xFFAB47BC);
  static const Color chartMA60 = Color(0xFF66BB6A);

  // ============ LIGHT THEME（深底金融風） ============
  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    primaryColor: primaryColor,
    colorScheme: const ColorScheme.light(
      primary: Color(0xFF1B5E20),
      onPrimary: Colors.white,
      secondary: Color(0xFF66BB6A),
      onSecondary: Colors.white,
      tertiary: Color(0xFFFFB300),
      surface: Color(0xFF1E272E),        // Card 深灰藍
      onSurface: Color(0xFFECEFF1),      // 淺色文字
      surfaceContainerHighest: Color(0xFF2C3A47), // 容器背景
      error: Color(0xFFEF5350),
      outline: Color(0xFF455A64),
    ),
    scaffoldBackgroundColor: const Color(0xFF151C23), // 很深的背景
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF1E272E),
      foregroundColor: Color(0xFFECEFF1),
      elevation: 0,
      centerTitle: true,
      titleTextStyle: TextStyle(
        color: Color(0xFFECEFF1),
        fontSize: 18,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: Color(0xFFECEFF1)),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: const Color(0xFF1E272E),
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: Color(0xFF2C3A47), width: 1),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF66BB6A),
        foregroundColor: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: const Color(0xFF66BB6A),
        side: const BorderSide(color: Color(0xFF455A64)),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: const Color(0xFF66BB6A),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF455A64)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF455A64)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF66BB6A), width: 2),
      ),
      filled: true,
      fillColor: const Color(0xFF1E272E),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      labelStyle: const TextStyle(color: Color(0xFFB0BEC5)),
      hintStyle: const TextStyle(color: Color(0xFF78909C)),
      prefixIconColor: const Color(0xFF90A4AE),
      suffixIconColor: const Color(0xFF90A4AE),
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(color: Color(0xFFECEFF1), fontWeight: FontWeight.bold),
      headlineMedium: TextStyle(color: Color(0xFFECEFF1), fontWeight: FontWeight.bold),
      titleLarge: TextStyle(color: Color(0xFFECEFF1), fontWeight: FontWeight.w600),
      titleMedium: TextStyle(color: Color(0xFFCFD8DC), fontWeight: FontWeight.w500),
      bodyLarge: TextStyle(color: Color(0xFFCFD8DC)),
      bodyMedium: TextStyle(color: Color(0xFFB0BEC5)),
      bodySmall: TextStyle(color: Color(0xFF90A4AE)),
      labelLarge: TextStyle(color: Color(0xFFCFD8DC), fontWeight: FontWeight.w500),
      labelSmall: TextStyle(color: Color(0xFF90A4AE)),
    ),
    iconTheme: const IconThemeData(color: Color(0xFFB0BEC5)),
    tabBarTheme: const TabBarThemeData(
      labelColor: Color(0xFF66BB6A),
      unselectedLabelColor: Color(0xFF90A4AE),
      indicatorColor: Color(0xFF66BB6A),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: Color(0xFF66BB6A),
      unselectedItemColor: Color(0xFF78909C),
      backgroundColor: Color(0xFF1E272E),
      type: BottomNavigationBarType.fixed,
      elevation: 8,
      selectedLabelStyle: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
    ),
    dividerTheme: const DividerThemeData(
      space: 1,
      thickness: 1,
      color: Color(0xFF2C3A47),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: const Color(0xFF2C3A47),
      selectedColor: const Color(0xFF1B5E20),
      labelStyle: const TextStyle(fontSize: 12, color: Color(0xFFCFD8DC)),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      side: const BorderSide(color: Color(0xFF455A64), width: 1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
    ),
    listTileTheme: const ListTileThemeData(
      iconColor: Color(0xFF90A4AE),
      textColor: Color(0xFFCFD8DC),
      titleTextStyle: TextStyle(fontSize: 15, color: Color(0xFFECEFF1)),
      subtitleTextStyle: TextStyle(fontSize: 13, color: Color(0xFF90A4AE)),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: const Color(0xFF1E272E),
      surfaceTintColor: Colors.transparent,
      titleTextStyle: const TextStyle(
        color: Color(0xFFECEFF1),
        fontSize: 20,
        fontWeight: FontWeight.w600,
      ),
      contentTextStyle: const TextStyle(color: Color(0xFFB0BEC5), fontSize: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: const Color(0xFF2C3A47),
      contentTextStyle: const TextStyle(color: Color(0xFFECEFF1)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
    popupMenuTheme: const PopupMenuThemeData(
      color: Color(0xFF1E272E),
      surfaceTintColor: Colors.transparent,
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: Color(0xFF1E272E),
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
    ),
    drawerTheme: const DrawerThemeData(
      backgroundColor: Color(0xFF1E272E),
      surfaceTintColor: Colors.transparent,
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return const Color(0xFF66BB6A);
        return const Color(0xFF78909C);
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return const Color(0xFF66BB6A).withAlpha(80);
        return const Color(0xFF455A64);
      }),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: Color(0xFF66BB6A),
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: Color(0xFF66BB6A),
      foregroundColor: Colors.white,
    ),
  );

  // ============ DARK THEME（更深的暗色） ============
  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    primaryColor: accentColor,
    colorScheme: const ColorScheme.dark(
      primary: Color(0xFF66BB6A),
      onPrimary: Colors.white,
      secondary: Color(0xFF66BB6A),
      onSecondary: Colors.white,
      tertiary: Color(0xFFFFB300),
      surface: Color(0xFF1A1A1A),
      onSurface: Color(0xFFE0E0E0),
      surfaceContainerHighest: Color(0xFF252525),
      error: Color(0xFFEF5350),
      outline: Color(0xFF404040),
    ),
    scaffoldBackgroundColor: const Color(0xFF0D0D0D),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF1A1A1A),
      foregroundColor: Color(0xFFE0E0E0),
      elevation: 0,
      centerTitle: true,
      titleTextStyle: TextStyle(
        color: Color(0xFFE0E0E0),
        fontSize: 18,
        fontWeight: FontWeight.w600,
      ),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: const Color(0xFF1A1A1A),
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: Color(0xFF2A2A2A), width: 1),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF66BB6A),
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
        foregroundColor: const Color(0xFF66BB6A),
        side: const BorderSide(color: Color(0xFF404040)),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: const Color(0xFF66BB6A),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF404040)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF404040)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF66BB6A), width: 2),
      ),
      filled: true,
      fillColor: const Color(0xFF1A1A1A),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      labelStyle: const TextStyle(color: Color(0xFF9E9E9E)),
      hintStyle: const TextStyle(color: Color(0xFF757575)),
      prefixIconColor: const Color(0xFF9E9E9E),
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
    iconTheme: const IconThemeData(color: Color(0xFFBDBDBD)),
    tabBarTheme: const TabBarThemeData(
      labelColor: Color(0xFF66BB6A),
      unselectedLabelColor: Color(0xFF757575),
      indicatorColor: Color(0xFF66BB6A),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: Color(0xFF66BB6A),
      unselectedItemColor: Color(0xFF757575),
      type: BottomNavigationBarType.fixed,
      backgroundColor: Color(0xFF1A1A1A),
      elevation: 8,
      selectedLabelStyle: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
    ),
    dividerTheme: const DividerThemeData(
      space: 1,
      thickness: 1,
      color: Color(0xFF2A2A2A),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: const Color(0xFF252525),
      selectedColor: const Color(0xFF1B5E20),
      labelStyle: const TextStyle(fontSize: 12, color: Color(0xFFE0E0E0)),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      side: const BorderSide(color: Color(0xFF404040), width: 1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
    ),
    listTileTheme: const ListTileThemeData(
      iconColor: Color(0xFF9E9E9E),
      textColor: Color(0xFFE0E0E0),
      titleTextStyle: TextStyle(fontSize: 15, color: Color(0xFFE0E0E0)),
      subtitleTextStyle: TextStyle(fontSize: 13, color: Color(0xFF9E9E9E)),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: const Color(0xFF1A1A1A),
      surfaceTintColor: Colors.transparent,
      titleTextStyle: const TextStyle(
        color: Color(0xFFE0E0E0),
        fontSize: 20,
        fontWeight: FontWeight.w600,
      ),
      contentTextStyle: const TextStyle(color: Color(0xFFBDBDBD), fontSize: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: const Color(0xFF2A2A2A),
      contentTextStyle: const TextStyle(color: Colors.white),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
    popupMenuTheme: const PopupMenuThemeData(
      color: Color(0xFF1A1A1A),
      surfaceTintColor: Colors.transparent,
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: Color(0xFF1A1A1A),
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
    ),
    drawerTheme: const DrawerThemeData(
      backgroundColor: Color(0xFF1A1A1A),
      surfaceTintColor: Colors.transparent,
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return const Color(0xFF66BB6A);
        return const Color(0xFF757575);
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return const Color(0xFF66BB6A).withAlpha(80);
        return const Color(0xFF404040);
      }),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: Color(0xFF66BB6A),
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: Color(0xFF66BB6A),
      foregroundColor: Colors.white,
    ),
  );

  // Helper method to get stock color
  static Color getStockColor(double? change) {
    if (change == null) return stockFlat;
    if (change > 0) return stockRise;
    if (change < 0) return stockFall;
    return stockFlat;
  }

  static Color getStockColorForContext(BuildContext context, double? change) {
    if (change == null) return Theme.of(context).disabledColor;
    if (change > 0) return stockRise;
    if (change < 0) return stockFall;
    return Theme.of(context).disabledColor;
  }

  static Color secondaryTextColor(BuildContext context) {
    return Theme.of(context).textTheme.bodySmall?.color ?? const Color(0xFF90A4AE);
  }

  static Color dividerColor(BuildContext context) {
    return Theme.of(context).dividerTheme.color ?? const Color(0xFF2C3A47);
  }
}
