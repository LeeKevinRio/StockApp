import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/notification.dart' hide TimeOfDay;
import '../models/notification.dart' as notif;
import '../providers/notification_provider.dart';
import '../widgets/notification/notification_item.dart';

/// 通知中心頁面
class NotificationCenterScreen extends StatefulWidget {
  const NotificationCenterScreen({super.key});

  @override
  State<NotificationCenterScreen> createState() => _NotificationCenterScreenState();
}

class _NotificationCenterScreenState extends State<NotificationCenterScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('通知中心'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => _showSettingsSheet(context),
            tooltip: '通知設置',
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (value) => _handleMenuAction(context, value),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'read_all',
                child: Row(
                  children: [
                    Icon(Icons.done_all, size: 20),
                    SizedBox(width: 12),
                    Text('全部標為已讀'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'clear_all',
                child: Row(
                  children: [
                    Icon(Icons.delete_sweep, size: 20),
                    SizedBox(width: 12),
                    Text('清除所有通知'),
                  ],
                ),
              ),
            ],
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '全部'),
            Tab(text: '未讀'),
            Tab(text: '警報'),
          ],
        ),
      ),
      body: Consumer<NotificationProvider>(
        builder: (context, provider, child) {
          return TabBarView(
            controller: _tabController,
            children: [
              _NotificationList(
                notifications: provider.notifications,
                emptyMessage: '暫無通知',
              ),
              _NotificationList(
                notifications: provider.notifications.where((n) => !n.isRead).toList(),
                emptyMessage: '沒有未讀通知',
              ),
              _NotificationList(
                notifications: provider.notifications
                    .where((n) =>
                        n.type == NotificationType.priceAlert ||
                        n.type == NotificationType.percentChangeAlert ||
                        n.type == NotificationType.volumeAlert ||
                        n.type == NotificationType.signalAlert)
                    .toList(),
                emptyMessage: '沒有警報通知',
              ),
            ],
          );
        },
      ),
    );
  }

  void _handleMenuAction(BuildContext context, String action) {
    final provider = context.read<NotificationProvider>();

    switch (action) {
      case 'read_all':
        provider.markAllAsRead();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('已將所有通知標為已讀')),
        );
        break;
      case 'clear_all':
        _showClearConfirmDialog(context);
        break;
    }
  }

  void _showClearConfirmDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('清除所有通知'),
        content: const Text('確定要清除所有通知嗎？此操作無法復原。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              context.read<NotificationProvider>().clearAll();
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('已清除所有通知')),
              );
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('清除'),
          ),
        ],
      ),
    );
  }

  void _showSettingsSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => const _NotificationSettingsSheet(),
    );
  }
}

/// 通知列表組件
class _NotificationList extends StatelessWidget {
  final List<AppNotification> notifications;
  final String emptyMessage;

  const _NotificationList({
    required this.notifications,
    required this.emptyMessage,
  });

  @override
  Widget build(BuildContext context) {
    if (notifications.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.notifications_off_outlined,
              size: 64,
              color: Colors.grey.shade400,
            ),
            const SizedBox(height: 16),
            Text(
              emptyMessage,
              style: TextStyle(
                color: Colors.grey.shade600,
                fontSize: 16,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: notifications.length,
      itemBuilder: (context, index) {
        final notification = notifications[index];
        return NotificationItem(
          notification: notification,
          onTap: () => _handleNotificationTap(context, notification),
          onDismiss: () => _handleNotificationDismiss(context, notification),
        );
      },
    );
  }

  void _handleNotificationTap(BuildContext context, AppNotification notification) {
    final provider = context.read<NotificationProvider>();
    provider.markAsRead(notification.id);

    // 導航到目標頁面
    final route = notification.targetRoute;
    final arguments = notification.targetArguments;

    if (route != null) {
      Navigator.pushNamed(context, route, arguments: arguments);
    }
  }

  void _handleNotificationDismiss(BuildContext context, AppNotification notification) {
    context.read<NotificationProvider>().removeNotification(notification.id);
  }
}

/// 通知設置面板
class _NotificationSettingsSheet extends StatelessWidget {
  const _NotificationSettingsSheet();

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.5,
      maxChildSize: 0.9,
      expand: false,
      builder: (context, scrollController) {
        return Consumer<NotificationProvider>(
          builder: (context, provider, child) {
            final prefs = provider.preferences;

            return Column(
              children: [
                // 標題欄
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: Theme.of(context).dividerColor,
                        width: 0.5,
                      ),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Text(
                        '通知設置',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                ),
                // 設置列表
                Expanded(
                  child: ListView(
                    controller: scrollController,
                    padding: const EdgeInsets.all(16),
                    children: [
                      // 通用設置
                      _SectionTitle(title: '通用設置'),
                      _SettingsSwitch(
                        title: '啟用本地通知',
                        subtitle: '在應用內顯示通知',
                        value: prefs.enableLocal,
                        onChanged: provider.toggleLocalNotification,
                      ),
                      _SettingsSwitch(
                        title: '通知聲音',
                        subtitle: '播放通知提示音',
                        value: prefs.enableSound,
                        onChanged: provider.toggleSound,
                      ),
                      _SettingsSwitch(
                        title: '震動',
                        subtitle: '收到通知時震動',
                        value: prefs.enableVibration,
                        onChanged: provider.toggleVibration,
                      ),

                      const SizedBox(height: 24),

                      // 通知類型設置
                      _SectionTitle(title: '通知類型'),
                      _SettingsSwitch(
                        title: '價格警報',
                        subtitle: '股票價格達到目標時通知',
                        value: prefs.isTypeEnabled(NotificationType.priceAlert),
                        onChanged: (v) => provider.toggleTypeNotification(
                            NotificationType.priceAlert, v),
                      ),
                      _SettingsSwitch(
                        title: '漲跌幅警報',
                        subtitle: '股票漲跌幅達到閾值時通知',
                        value: prefs.isTypeEnabled(NotificationType.percentChangeAlert),
                        onChanged: (v) => provider.toggleTypeNotification(
                            NotificationType.percentChangeAlert, v),
                      ),
                      _SettingsSwitch(
                        title: 'AI 建議',
                        subtitle: 'AI 投資建議更新時通知',
                        value: prefs.isTypeEnabled(NotificationType.aiSuggestion),
                        onChanged: (v) => provider.toggleTypeNotification(
                            NotificationType.aiSuggestion, v),
                      ),
                      _SettingsSwitch(
                        title: '形態識別',
                        subtitle: '檢測到技術形態時通知',
                        value: prefs.isTypeEnabled(NotificationType.patternDetected),
                        onChanged: (v) => provider.toggleTypeNotification(
                            NotificationType.patternDetected, v),
                      ),
                      _SettingsSwitch(
                        title: '交易信號',
                        subtitle: '交易信號提醒',
                        value: prefs.isTypeEnabled(NotificationType.signalAlert),
                        onChanged: (v) => provider.toggleTypeNotification(
                            NotificationType.signalAlert, v),
                      ),
                      _SettingsSwitch(
                        title: '新聞資訊',
                        subtitle: '重要財經新聞通知',
                        value: prefs.isTypeEnabled(NotificationType.news),
                        onChanged: (v) =>
                            provider.toggleTypeNotification(NotificationType.news, v),
                      ),

                      const SizedBox(height: 24),

                      // 勿擾時段
                      _SectionTitle(title: '勿擾時段'),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('設置勿擾時段'),
                        subtitle: Text(
                          prefs.quietHoursStart != null && prefs.quietHoursEnd != null
                              ? '${prefs.quietHoursStart} - ${prefs.quietHoursEnd}'
                              : '未設置',
                        ),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => _showQuietHoursDialog(context, provider, prefs),
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _showQuietHoursDialog(
    BuildContext context,
    NotificationProvider provider,
    notif.NotificationPreferences prefs,
  ) {
    TimeOfDay? startTime = prefs.quietHoursStart != null
        ? TimeOfDay(
            hour: prefs.quietHoursStart!.hour,
            minute: prefs.quietHoursStart!.minute,
          )
        : null;
    TimeOfDay? endTime = prefs.quietHoursEnd != null
        ? TimeOfDay(
            hour: prefs.quietHoursEnd!.hour,
            minute: prefs.quietHoursEnd!.minute,
          )
        : null;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('勿擾時段'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                title: const Text('開始時間'),
                trailing: Text(
                  startTime != null
                      ? '${startTime!.hour.toString().padLeft(2, '0')}:${startTime!.minute.toString().padLeft(2, '0')}'
                      : '未設置',
                ),
                onTap: () async {
                  final time = await showTimePicker(
                    context: context,
                    initialTime: startTime ?? const TimeOfDay(hour: 22, minute: 0),
                  );
                  if (time != null) {
                    setState(() => startTime = time);
                  }
                },
              ),
              ListTile(
                title: const Text('結束時間'),
                trailing: Text(
                  endTime != null
                      ? '${endTime!.hour.toString().padLeft(2, '0')}:${endTime!.minute.toString().padLeft(2, '0')}'
                      : '未設置',
                ),
                onTap: () async {
                  final time = await showTimePicker(
                    context: context,
                    initialTime: endTime ?? const TimeOfDay(hour: 8, minute: 0),
                  );
                  if (time != null) {
                    setState(() => endTime = time);
                  }
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                provider.setQuietHours(null, null);
                Navigator.pop(context);
              },
              child: const Text('清除'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('取消'),
            ),
            TextButton(
              onPressed: () {
                if (startTime != null && endTime != null) {
                  provider.setQuietHours(
                    notif.QuietHoursTime(hour: startTime!.hour, minute: startTime!.minute),
                    notif.QuietHoursTime(hour: endTime!.hour, minute: endTime!.minute),
                  );
                }
                Navigator.pop(context);
              },
              child: const Text('確定'),
            ),
          ],
        ),
      ),
    );
  }
}

/// 設置區塊標題
class _SectionTitle extends StatelessWidget {
  final String title;

  const _SectionTitle({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: Theme.of(context).primaryColor,
        ),
      ),
    );
  }
}

/// 設置開關項
class _SettingsSwitch extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _SettingsSwitch({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SwitchListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(title),
      subtitle: Text(
        subtitle,
        style: TextStyle(
          fontSize: 12,
          color: Theme.of(context).textTheme.bodySmall?.color,
        ),
      ),
      value: value,
      onChanged: onChanged,
    );
  }
}
