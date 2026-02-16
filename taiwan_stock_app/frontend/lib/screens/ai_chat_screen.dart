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

  // Prompt templates for quick questions
  static const List<PromptTemplate> _generalPrompts = [
    PromptTemplate('大盤走勢', '請分析今日台股大盤走勢和重點產業表現'),
    PromptTemplate('熱門股', '目前市場上有哪些熱門股票值得關注？'),
    PromptTemplate('技術分析', '請用技術分析解釋目前市場的支撐和壓力位'),
    PromptTemplate('投資建議', '對於新手投資人，你有什麼投資建議？'),
  ];

  List<PromptTemplate> get _stockPrompts => [
    PromptTemplate('股價分析', '請分析 ${widget.stockId} 的股價走勢'),
    PromptTemplate('技術指標', '${widget.stockId} 的技術指標顯示什麼訊號？'),
    PromptTemplate('外資動向', '${widget.stockId} 最近的外資買賣超情況如何？'),
    PromptTemplate('投資建議', '${widget.stockId} 現在適合買入嗎？'),
  ];

  List<PromptTemplate> get _currentPrompts =>
      widget.stockId != null ? _stockPrompts : _generalPrompts;

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
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.stockId != null ? 'AI 問答 - ${widget.stockId}' : 'AI 問答'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            onPressed: () => _confirmClearChat(context),
            tooltip: '清除對話',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: Consumer<AIProvider>(
              builder: (context, provider, child) {
                if (provider.messages.isEmpty && !provider.isLoading) {
                  return _buildEmptyState(context);
                }

                final itemCount = provider.messages.length + (provider.isLoading ? 1 : 0);

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: itemCount,
                  itemBuilder: (context, index) {
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
                      timestamp: message.timestamp,
                    );
                  },
                );
              },
            ),
          ),
          // Quick prompt templates
          Consumer<AIProvider>(
            builder: (context, provider, child) {
              if (provider.messages.isEmpty && !provider.isLoading) {
                return _buildPromptTemplates(context);
              }
              return const SizedBox.shrink();
            },
          ),
          // Input area
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isDark ? Theme.of(context).cardColor : Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.1),
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
                        fillColor: isDark ? Colors.grey[800] : Colors.grey[100],
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

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.chat_bubble_outline,
            size: 64,
            color: Theme.of(context).disabledColor,
          ),
          const SizedBox(height: 16),
          const Text(
            '有什麼投資問題想問我嗎？',
            style: TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            widget.stockId != null
                ? '你可以詢問關於 ${widget.stockId} 的任何問題'
                : '例如：台積電最近外資動向如何？',
            style: TextStyle(
              color: Theme.of(context).textTheme.bodySmall?.color,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPromptTemplates(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '快速提問',
            style: TextStyle(
              fontSize: 12,
              color: Theme.of(context).textTheme.bodySmall?.color,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _currentPrompts.map((prompt) {
              return ActionChip(
                label: Text(prompt.label),
                onPressed: () {
                  _messageController.text = prompt.question;
                  _sendMessage();
                },
                avatar: const Icon(Icons.lightbulb_outline, size: 16),
              );
            }).toList(),
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

  void _confirmClearChat(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('清除對話'),
        content: const Text('確定要清除所有對話記錄嗎？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              context.read<AIProvider>().loadChatHistory(stockId: widget.stockId);
              Navigator.pop(context);
            },
            child: Text(
              '清除',
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        ],
      ),
    );
  }
}

class PromptTemplate {
  final String label;
  final String question;

  const PromptTemplate(this.label, this.question);
}
