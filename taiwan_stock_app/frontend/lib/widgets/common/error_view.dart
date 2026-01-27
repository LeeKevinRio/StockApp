import 'package:flutter/material.dart';

/// A standardized error view widget with retry functionality
class ErrorView extends StatelessWidget {
  final String? message;
  final String? details;
  final VoidCallback? onRetry;
  final IconData icon;
  final Color? iconColor;
  final bool showRetryButton;
  final String retryButtonText;

  const ErrorView({
    super.key,
    this.message,
    this.details,
    this.onRetry,
    this.icon = Icons.error_outline,
    this.iconColor,
    this.showRetryButton = true,
    this.retryButtonText = '重試',
  });

  factory ErrorView.network({
    VoidCallback? onRetry,
    String? details,
  }) {
    return ErrorView(
      message: '網路連線錯誤',
      details: details ?? '請檢查網路連線後重試',
      icon: Icons.wifi_off,
      onRetry: onRetry,
    );
  }

  factory ErrorView.server({
    VoidCallback? onRetry,
    String? details,
  }) {
    return ErrorView(
      message: '伺服器錯誤',
      details: details ?? '伺服器暫時無法使用，請稍後再試',
      icon: Icons.cloud_off,
      onRetry: onRetry,
    );
  }

  factory ErrorView.notFound({
    String? message,
    VoidCallback? onRetry,
  }) {
    return ErrorView(
      message: message ?? '找不到資料',
      details: '請確認搜尋條件或稍後再試',
      icon: Icons.search_off,
      onRetry: onRetry,
    );
  }

  factory ErrorView.unauthorized({
    VoidCallback? onRetry,
  }) {
    return ErrorView(
      message: '登入已過期',
      details: '請重新登入',
      icon: Icons.lock_outline,
      onRetry: onRetry,
      retryButtonText: '重新登入',
    );
  }

  factory ErrorView.empty({
    String? message,
    IconData icon = Icons.inbox_outlined,
  }) {
    return ErrorView(
      message: message ?? '暫無資料',
      icon: icon,
      showRetryButton: false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final effectiveIconColor = iconColor ?? theme.colorScheme.error;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 64,
              color: effectiveIconColor,
            ),
            const SizedBox(height: 16),
            Text(
              message ?? '發生錯誤',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            if (details != null) ...[
              const SizedBox(height: 8),
              Text(
                details!,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.textTheme.bodySmall?.color,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            if (showRetryButton && onRetry != null) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: Text(retryButtonText),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 12,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// A compact inline error widget for smaller spaces
class InlineErrorView extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const InlineErrorView({
    super.key,
    required this.message,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(
            Icons.warning_amber_rounded,
            size: 20,
            color: Theme.of(context).colorScheme.error,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                fontSize: 14,
                color: Theme.of(context).colorScheme.onErrorContainer,
              ),
            ),
          ),
          if (onRetry != null)
            IconButton(
              icon: const Icon(Icons.refresh, size: 20),
              onPressed: onRetry,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
        ],
      ),
    );
  }
}

/// An error banner that can be shown at the top of a screen
class ErrorBanner extends StatelessWidget {
  final String message;
  final VoidCallback? onDismiss;
  final VoidCallback? onRetry;

  const ErrorBanner({
    super.key,
    required this.message,
    this.onDismiss,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialBanner(
      content: Text(message),
      leading: Icon(
        Icons.error_outline,
        color: Theme.of(context).colorScheme.error,
      ),
      backgroundColor: Theme.of(context).colorScheme.errorContainer,
      actions: [
        if (onRetry != null)
          TextButton(
            onPressed: onRetry,
            child: const Text('重試'),
          ),
        TextButton(
          onPressed: onDismiss,
          child: const Text('關閉'),
        ),
      ],
    );
  }
}
