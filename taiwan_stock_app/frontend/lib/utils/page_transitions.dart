import 'package:flutter/material.dart';

/// Custom page route with slide transition
class SlidePageRoute<T> extends PageRouteBuilder<T> {
  final Widget page;
  final SlideDirection direction;

  SlidePageRoute({
    required this.page,
    this.direction = SlideDirection.right,
    super.settings,
  }) : super(
          pageBuilder: (context, animation, secondaryAnimation) => page,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            Offset begin;
            switch (direction) {
              case SlideDirection.right:
                begin = const Offset(1.0, 0.0);
                break;
              case SlideDirection.left:
                begin = const Offset(-1.0, 0.0);
                break;
              case SlideDirection.up:
                begin = const Offset(0.0, 1.0);
                break;
              case SlideDirection.down:
                begin = const Offset(0.0, -1.0);
                break;
            }

            final offsetAnimation = Tween<Offset>(
              begin: begin,
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOutCubic,
            ));

            return SlideTransition(
              position: offsetAnimation,
              child: child,
            );
          },
          transitionDuration: const Duration(milliseconds: 300),
        );
}

enum SlideDirection { right, left, up, down }

/// Custom page route with fade transition
class FadePageRoute<T> extends PageRouteBuilder<T> {
  final Widget page;

  FadePageRoute({
    required this.page,
    super.settings,
  }) : super(
          pageBuilder: (context, animation, secondaryAnimation) => page,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: Curves.easeOut,
              ),
              child: child,
            );
          },
          transitionDuration: const Duration(milliseconds: 250),
        );
}

/// Custom page route with scale and fade transition
class ScaleFadePageRoute<T> extends PageRouteBuilder<T> {
  final Widget page;

  ScaleFadePageRoute({
    required this.page,
    super.settings,
  }) : super(
          pageBuilder: (context, animation, secondaryAnimation) => page,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            final scaleAnimation = Tween<double>(
              begin: 0.95,
              end: 1.0,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOutCubic,
            ));

            final fadeAnimation = Tween<double>(
              begin: 0.0,
              end: 1.0,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOut,
            ));

            return FadeTransition(
              opacity: fadeAnimation,
              child: ScaleTransition(
                scale: scaleAnimation,
                child: child,
              ),
            );
          },
          transitionDuration: const Duration(milliseconds: 300),
        );
}

/// Custom page route with shared axis transition (Material Design)
class SharedAxisPageRoute<T> extends PageRouteBuilder<T> {
  final Widget page;
  final SharedAxisType type;

  SharedAxisPageRoute({
    required this.page,
    this.type = SharedAxisType.horizontal,
    super.settings,
  }) : super(
          pageBuilder: (context, animation, secondaryAnimation) => page,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            Offset begin;
            switch (type) {
              case SharedAxisType.horizontal:
                begin = const Offset(0.3, 0.0);
                break;
              case SharedAxisType.vertical:
                begin = const Offset(0.0, 0.3);
                break;
              case SharedAxisType.scaled:
                return _buildScaledTransition(animation, child);
            }

            final offsetAnimation = Tween<Offset>(
              begin: begin,
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOutCubic,
            ));

            final fadeAnimation = Tween<double>(
              begin: 0.0,
              end: 1.0,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
            ));

            return FadeTransition(
              opacity: fadeAnimation,
              child: SlideTransition(
                position: offsetAnimation,
                child: child,
              ),
            );
          },
          transitionDuration: const Duration(milliseconds: 300),
        );

  static Widget _buildScaledTransition(Animation<double> animation, Widget child) {
    final scaleAnimation = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: animation,
      curve: Curves.easeOutCubic,
    ));

    final fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: animation,
      curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
    ));

    return FadeTransition(
      opacity: fadeAnimation,
      child: ScaleTransition(
        scale: scaleAnimation,
        child: child,
      ),
    );
  }
}

enum SharedAxisType { horizontal, vertical, scaled }

/// Extension on Navigator for easy navigation with transitions
extension NavigatorExtension on NavigatorState {
  Future<T?> pushWithSlide<T>(Widget page, {SlideDirection direction = SlideDirection.right}) {
    return push<T>(SlidePageRoute(page: page, direction: direction));
  }

  Future<T?> pushWithFade<T>(Widget page) {
    return push<T>(FadePageRoute(page: page));
  }

  Future<T?> pushWithScaleFade<T>(Widget page) {
    return push<T>(ScaleFadePageRoute(page: page));
  }

  Future<T?> pushReplacementWithFade<T, TO>(Widget page) {
    return pushReplacement<T, TO>(FadePageRoute(page: page));
  }
}

/// A helper class for creating page routes
class AppPageRoute {
  static Route<T> slide<T>(Widget page, {SlideDirection direction = SlideDirection.right, RouteSettings? settings}) {
    return SlidePageRoute<T>(page: page, direction: direction, settings: settings);
  }

  static Route<T> fade<T>(Widget page, {RouteSettings? settings}) {
    return FadePageRoute<T>(page: page, settings: settings);
  }

  static Route<T> scaleFade<T>(Widget page, {RouteSettings? settings}) {
    return ScaleFadePageRoute<T>(page: page, settings: settings);
  }

  static Route<T> sharedAxis<T>(Widget page, {SharedAxisType type = SharedAxisType.horizontal, RouteSettings? settings}) {
    return SharedAxisPageRoute<T>(page: page, type: type, settings: settings);
  }

  /// Standard page route with platform-appropriate transition
  static Route<T> adaptive<T>(Widget page, {RouteSettings? settings}) {
    return MaterialPageRoute<T>(builder: (_) => page, settings: settings);
  }
}
