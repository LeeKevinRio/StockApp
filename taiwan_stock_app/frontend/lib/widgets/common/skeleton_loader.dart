import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';

/// A skeleton loading widget that displays shimmer animation
class SkeletonLoader extends StatelessWidget {
  final double? width;
  final double? height;
  final double borderRadius;
  final EdgeInsetsGeometry? margin;

  const SkeletonLoader({
    super.key,
    this.width,
    this.height,
    this.borderRadius = 4,
    this.margin,
  });

  @override
  Widget build(BuildContext context) {
    // 兩個主題都是深色背景，統一使用深色骨架
    final baseColor = Colors.grey.shade800;
    final highlightColor = Colors.grey.shade700;

    return Shimmer.fromColors(
      baseColor: baseColor,
      highlightColor: highlightColor,
      child: Container(
        width: width,
        height: height,
        margin: margin,
        decoration: BoxDecoration(
          color: baseColor,
          borderRadius: BorderRadius.circular(borderRadius),
        ),
      ),
    );
  }
}

/// A skeleton card that mimics stock card loading state
class StockCardSkeleton extends StatelessWidget {
  const StockCardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SkeletonLoader(width: 80, height: 16),
                  const SizedBox(height: 8),
                  const SkeletonLoader(width: 120, height: 14),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                const SkeletonLoader(width: 60, height: 20),
                const SizedBox(height: 4),
                const SkeletonLoader(width: 50, height: 14),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// A skeleton list that shows multiple loading cards
class StockListSkeleton extends StatelessWidget {
  final int itemCount;

  const StockListSkeleton({super.key, this.itemCount = 5});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      physics: const NeverScrollableScrollPhysics(),
      itemCount: itemCount,
      itemBuilder: (context, index) => const StockCardSkeleton(),
    );
  }
}

/// A skeleton for search results
class SearchResultSkeleton extends StatelessWidget {
  const SearchResultSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        title: const SkeletonLoader(width: 150, height: 16),
        subtitle: const SkeletonLoader(width: 100, height: 14, margin: EdgeInsets.only(top: 8)),
        trailing: const SkeletonLoader(width: 60, height: 32, borderRadius: 16),
      ),
    );
  }
}

/// A skeleton for chart loading
class ChartSkeleton extends StatelessWidget {
  const ChartSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Chart area
          Expanded(
            child: SkeletonLoader(
              width: double.infinity,
              borderRadius: 8,
            ),
          ),
          const SizedBox(height: 16),
          // X-axis labels
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(
              5,
              (_) => const SkeletonLoader(width: 40, height: 12),
            ),
          ),
        ],
      ),
    );
  }
}

/// A skeleton for news item
class NewsItemSkeleton extends StatelessWidget {
  const NewsItemSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SkeletonLoader(width: double.infinity, height: 16),
            const SizedBox(height: 8),
            const SkeletonLoader(width: 200, height: 14),
            const SizedBox(height: 8),
            Row(
              children: [
                const SkeletonLoader(width: 60, height: 12),
                const SizedBox(width: 16),
                const SkeletonLoader(width: 80, height: 12),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// A skeleton for chat message bubble
class ChatBubbleSkeleton extends StatelessWidget {
  final bool isUser;

  const ChatBubbleSkeleton({super.key, this.isUser = false});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        child: Column(
          crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            SkeletonLoader(
              width: isUser ? 150 : 200,
              height: 40,
              borderRadius: 12,
            ),
          ],
        ),
      ),
    );
  }
}

/// A skeleton for indicator data panel
class IndicatorPanelSkeleton extends StatelessWidget {
  const IndicatorPanelSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SkeletonLoader(width: 100, height: 16),
          const SizedBox(height: 12),
          Wrap(
            spacing: 16,
            runSpacing: 8,
            children: List.generate(
              6,
              (_) => const SkeletonLoader(width: 70, height: 24, borderRadius: 4),
            ),
          ),
        ],
      ),
    );
  }
}
