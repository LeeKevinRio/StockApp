import 'package:flutter/material.dart';

/// 延遲載入畫面包裝器
///
/// 在背景載入該畫面對應的程式碼分塊(deferred library)，載入完成後再顯示畫面。
/// 用於把「重、且非主要分頁」的畫面從首次載入的主包(main.dart.js)分離出去，
/// 加快第一次開啟網頁的速度；使用者真正進到該頁時才下載那一塊。
class DeferredScreen extends StatefulWidget {
  /// 對應 deferred import 前綴的 loadLibrary 函式
  final Future<void> Function() loadLibrary;

  /// 載入完成後要顯示的畫面
  final WidgetBuilder builder;

  const DeferredScreen({
    super.key,
    required this.loadLibrary,
    required this.builder,
  });

  @override
  State<DeferredScreen> createState() => _DeferredScreenState();
}

class _DeferredScreenState extends State<DeferredScreen> {
  late Future<void> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.loadLibrary();
  }

  void _retry() {
    setState(() {
      _future = widget.loadLibrary();
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.done) {
          if (snapshot.hasError) {
            return Scaffold(
              appBar: AppBar(),
              body: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline, size: 48, color: Colors.grey),
                    const SizedBox(height: 12),
                    const Text('頁面載入失敗，請檢查網路後重試'),
                    const SizedBox(height: 12),
                    ElevatedButton(
                      onPressed: _retry,
                      child: const Text('重試'),
                    ),
                  ],
                ),
              ),
            );
          }
          return widget.builder(context);
        }
        // 載入中
        return const Scaffold(
          body: Center(child: CircularProgressIndicator()),
        );
      },
    );
  }
}
