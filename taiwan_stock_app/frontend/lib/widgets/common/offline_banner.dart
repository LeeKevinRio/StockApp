import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/connectivity_provider.dart';

/// 離線狀態橫幅
/// 當網路斷線時顯示在畫面頂部
class OfflineBanner extends StatelessWidget {
  final Widget child;

  const OfflineBanner({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Consumer<ConnectivityProvider>(
      builder: (context, connectivity, _) {
        return Column(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              height: connectivity.isOffline ? null : 0,
              child: connectivity.isOffline
                  ? MaterialBanner(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      leading: const Icon(
                        Icons.wifi_off,
                        color: Colors.white,
                      ),
                      backgroundColor: Colors.red.shade700,
                      content: const Text(
                        '網路連線中斷，部分功能可能無法使用',
                        style: TextStyle(color: Colors.white, fontSize: 13),
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => connectivity.retry(),
                          child: const Text(
                            '重試',
                            style: TextStyle(color: Colors.white),
                          ),
                        ),
                      ],
                    )
                  : const SizedBox.shrink(),
            ),
            Expanded(child: child),
          ],
        );
      },
    );
  }
}
