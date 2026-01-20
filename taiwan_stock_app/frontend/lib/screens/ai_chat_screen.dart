import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ai_provider.dart';
import '../widgets/chat_bubble.dart';

class AIChatScreen extends StatefulWidget {
  final String? stockId;

  const AIChatScreen({super.key, this.stockId});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AIProvider>().loadChatHistory(stockId: widget.stockId);
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.stockId != null ? 'AI 問答 - ${widget.stockId}' : 'AI 問答'),
      ),
      body: Column(
        children: [
          Expanded(
            child: Consumer<AIProvider>(
              builder: (context, provider, child) {
                if (provider.messages.isEmpty && !provider.isLoading) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.chat_bubble_outline,
                            size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 16),
                        const Text('有什麼投資問題想問我嗎？'),
                        const SizedBox(height: 8),
                        Text(
                          '例如：台積電最近外資動向如何？',
                          style:
                              TextStyle(color: Colors.grey[600], fontSize: 14),
                        ),
                      ],
                    ),
                  );
                }

                final itemCount = provider.messages.length + (provider.isLoading ? 1 : 0);

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: itemCount,
                  itemBuilder: (context, index) {
                    // 如果是最後一個且正在 loading，顯示 loading 氣泡
                    if (provider.isLoading && index == itemCount - 1) {
                      return const ChatBubble(
                        message: '',
                        isUser: false,
                        isLoading: true,
                      );
                    }

                    final message = provider.messages[index];
                    return ChatBubble(
                      message: message.content,
                      isUser: message.role == 'user',
                      sources: message.sources,
                    );
                  },
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.2),
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      decoration: InputDecoration(
                        hintText: '輸入你的問題...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide.none,
                        ),
                        filled: true,
                        fillColor: Colors.grey[100],
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                      ),
                      maxLines: null,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Consumer<AIProvider>(
                    builder: (context, provider, child) {
                      return IconButton(
                        icon: provider.isLoading
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.send),
                        onPressed: provider.isLoading ? null : _sendMessage,
                        color: Theme.of(context).primaryColor,
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _sendMessage() {
    final message = _messageController.text.trim();
    if (message.isEmpty) return;

    context.read<AIProvider>().sendMessage(
          message,
          stockId: widget.stockId,
        );

    _messageController.clear();

    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }
}
