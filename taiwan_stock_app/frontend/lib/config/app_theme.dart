import 'package:flutter/material.dart';

/// App theme configuration for light and dark modes
class AppTheme {
  // Brand colors
  static const Color primaryColor = Color(0xFF1976D2);
  static const Color primaryColorDark = Color(0xFF1565C0);
  static const Color accentColor = Color(0xFF42A5F5);

  // Stock colors
  static const Color stockRise = Color(0xFFE53935); // Red for rising
  static const Color stockFall = Color(0xFF43A047); // Green for falling
  static const Color stockFlat = Color(0xFF757575); // Grey for no change

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
      secondary: accentColor,
      surface: Colors.white,
      error: Colors.red.shade700,
    ),
    scaffoldBackgroundColor: const Color(0xFFF5F5F5),
    appBarTheme: const AppBarTheme(
      backgroundColor: primaryColor,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: true,
    ),
    cardTheme: CardThemeData(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: Colors.white,
      unselectedLabelColor: Colors.white70,
      indicatorColor: Colors.white,
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: primaryColor,
      unselectedItemColor: Colors.grey,
      type: BottomNavigationBarType.fixed,
    ),
    dividerTheme: const DividerThemeData(
      space: 1,
      thickness: 1,
      color: Color(0xFFE0E0E0),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: Colors.grey.shade100,
      labelStyle: const TextStyle(fontSize: 12),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
    ),
  );

  // Dark theme
  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    primaryColor: primaryColorDark,
    colorScheme: ColorScheme.dark(
      primary: accentColor,
      secondary: accentColor,
      surface: const Color(0xFF1E1E1E),
      error: Colors.red.shade400,
    ),
    scaffoldBackgroundColor: const Color(0xFF121212),
    appBarTheme: const AppBarTheme(
      backgroundColor: Color(0xFF1E1E1E),
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: true,
    ),
    cardTheme: CardThemeData(
      elevation: 2,
      color: const Color(0xFF2C2C2C),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
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
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      filled: true,
      fillColor: const Color(0xFF2C2C2C),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    tabBarTheme: const TabBarThemeData(
      labelColor: Colors.white,
      unselectedLabelColor: Colors.white60,
      indicatorColor: accentColor,
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: accentColor,
      unselectedItemColor: Colors.grey,
      type: BottomNavigationBarType.fixed,
      backgroundColor: Color(0xFF1E1E1E),
    ),
    dividerTheme: const DividerThemeData(
      space: 1,
      thickness: 1,
      color: Color(0xFF424242),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: const Color(0xFF424242),
      labelStyle: const TextStyle(fontSize: 12, color: Colors.white),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
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
    // In Taiwan, red means up, green means down
    if (change == null) return Theme.of(context).disabledColor;
    if (change > 0) return stockRise;
    if (change < 0) return stockFall;
    return Theme.of(context).disabledColor;
  }
}
