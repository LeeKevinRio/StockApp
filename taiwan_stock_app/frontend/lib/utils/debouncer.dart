import 'dart:async';
import 'package:flutter/foundation.dart';

/// A utility class for debouncing function calls
/// Useful for search input to avoid excessive API requests
class Debouncer {
  final Duration delay;
  Timer? _timer;

  Debouncer({this.delay = const Duration(milliseconds: 300)});

  /// Run the action after the delay, cancelling any previous pending action
  void run(VoidCallback action) {
    _timer?.cancel();
    _timer = Timer(delay, action);
  }

  /// Cancel any pending action
  void cancel() {
    _timer?.cancel();
  }

  /// Dispose the debouncer (cancel any pending action)
  void dispose() {
    cancel();
  }

  /// Check if there's a pending action
  bool get isPending => _timer?.isActive ?? false;
}

/// A debouncer that can return a Future for async operations
class AsyncDebouncer<T> {
  final Duration delay;
  Timer? _timer;
  Completer<T>? _completer;

  AsyncDebouncer({this.delay = const Duration(milliseconds: 300)});

  /// Run the async action after the delay
  Future<T> run(Future<T> Function() action) {
    _timer?.cancel();
    _completer?.completeError(DebouncerCancelledException());

    _completer = Completer<T>();
    final currentCompleter = _completer!;

    _timer = Timer(delay, () async {
      try {
        final result = await action();
        if (!currentCompleter.isCompleted) {
          currentCompleter.complete(result);
        }
      } catch (e) {
        if (!currentCompleter.isCompleted) {
          currentCompleter.completeError(e);
        }
      }
    });

    return currentCompleter.future;
  }

  void cancel() {
    _timer?.cancel();
    _completer?.completeError(DebouncerCancelledException());
  }

  void dispose() {
    cancel();
  }
}

/// Exception thrown when a debounced action is cancelled
class DebouncerCancelledException implements Exception {
  @override
  String toString() => 'Debounced action was cancelled';
}

/// A throttler that ensures a function is called at most once per interval
class Throttler {
  final Duration interval;
  DateTime? _lastCallTime;
  Timer? _pendingTimer;

  Throttler({this.interval = const Duration(milliseconds: 300)});

  /// Run the action, throttled to at most once per interval
  void run(VoidCallback action) {
    final now = DateTime.now();

    if (_lastCallTime == null ||
        now.difference(_lastCallTime!) >= interval) {
      _lastCallTime = now;
      action();
    } else {
      // Schedule for the remaining time
      _pendingTimer?.cancel();
      final remaining = interval - now.difference(_lastCallTime!);
      _pendingTimer = Timer(remaining, () {
        _lastCallTime = DateTime.now();
        action();
      });
    }
  }

  void cancel() {
    _pendingTimer?.cancel();
  }

  void dispose() {
    cancel();
  }
}
