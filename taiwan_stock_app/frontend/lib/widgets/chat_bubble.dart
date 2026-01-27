import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';

class ChatBubble extends StatefulWidget {
  final String message;
  final bool isUser;
  final List<String>? sources;
  final bool isLoading;
  final DateTime? timestamp;
  final VoidCallback? onCopy;

  const ChatBubble({
    super.key,
    required this.message,
    required this.isUser,
    this.sources,
    this.isLoading = false,
    this.timestamp,
    this.onCopy,
  });

  @override
  State<ChatBubble> createState() => _ChatBubbleState();
}

class _ChatBubbleState extends State<ChatBubble> {
  bool _showActions = false;

  void _copyToClipboard(BuildContext context) {
    Clipboard.setData(ClipboardData(text: widget.message));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('已複製到剪貼簿'),
        duration: Duration(seconds: 1),
      ),
    );
    widget.onCopy?.call();
  }

  String _formatTimestamp(DateTime? timestamp) {
    if (timestamp == null) return '';
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final messageDate = DateTime(timestamp.year, timestamp.month, timestamp.day);

    if (messageDate == today) {
      return DateFormat('HH:mm').format(timestamp);
    } else {
      return DateFormat('MM/dd HH:mm').format(timestamp);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bubbleColor = widget.isUser
        ? Theme.of(context).primaryColor
        : (isDark ? Colors.grey[800] : Colors.grey[200]);
    final textColor = widget.isUser
        ? Colors.white
        : (isDark ? Colors.white : Colors.black87);

    return GestureDetector(
      onLongPress: () => setState(() => _showActions = !_showActions),
      onTap: () {
        if (_showActions) setState(() => _showActions = false);
      },
      child: Align(
        alignment: widget.isUser ? Alignment.centerRight : Alignment.centerLeft,
        child: Column(
          crossAxisAlignment:
              widget.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Container(
              margin: const EdgeInsets.symmetric(vertical: 4),
              padding: const EdgeInsets.all(12),
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.85,
              ),
              decoration: BoxDecoration(
                color: bubbleColor,
                borderRadius: BorderRadius.circular(16).copyWith(
                  bottomRight: widget.isUser ? const Radius.circular(4) : null,
                  bottomLeft: !widget.isUser ? const Radius.circular(4) : null,
                ),
              ),
              child: widget.isLoading
                  ? _buildLoadingIndicator(context)
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SelectableText(
                          widget.message,
                          maxLines: null,
                          style: TextStyle(
                            color: textColor,
                            height: 1.5,
                          ),
                        ),
                        if (widget.sources != null && widget.sources!.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(
                            '資料來源：${widget.sources!.join(', ')}',
                            style: TextStyle(
                              fontSize: 12,
                              color: widget.isUser ? Colors.white70 : Colors.grey[600],
                            ),
                          ),
                        ],
                      ],
                    ),
            ),
            // Timestamp and actions row
            if (!widget.isLoading)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (widget.timestamp != null)
                      Text(
                        _formatTimestamp(widget.timestamp),
                        style: TextStyle(
                          fontSize: 10,
                          color: Theme.of(context).textTheme.bodySmall?.color,
                        ),
                      ),
                    if (_showActions || !widget.isUser) ...[
                      const SizedBox(width: 8),
                      InkWell(
                        onTap: () => _copyToClipboard(context),
                        borderRadius: BorderRadius.circular(4),
                        child: Padding(
                          padding: const EdgeInsets.all(4),
                          child: Icon(
                            Icons.copy,
                            size: 14,
                            color: Theme.of(context).textTheme.bodySmall?.color,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoadingIndicator(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 16,
          height: 16,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(
              Theme.of(context).disabledColor,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          'AI 思考中...',
          style: TextStyle(
            color: Theme.of(context).textTheme.bodySmall?.color,
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }
}

class TypewriterText extends StatefulWidget {
  final String text;
  final TextStyle? style;
  final VoidCallback? onComplete;

  const TypewriterText({
    super.key,
    required this.text,
    this.style,
    this.onComplete,
  });

  @override
  State<TypewriterText> createState() => _TypewriterTextState();
}

class _TypewriterTextState extends State<TypewriterText> {
  String _displayedText = '';
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _startTyping();
  }

  void _startTyping() {
    Future.doWhile(() async {
      if (_currentIndex >= widget.text.length) {
        widget.onComplete?.call();
        return false;
      }

      await Future.delayed(const Duration(milliseconds: 15));

      if (mounted) {
        setState(() {
          _currentIndex += 1;
          _displayedText = widget.text.substring(0, _currentIndex);
        });
      }
      return mounted && _currentIndex < widget.text.length;
    });
  }

  @override
  Widget build(BuildContext context) {
    return SelectableText(
      _displayedText,
      maxLines: null,
      style: widget.style,
    );
  }
}
