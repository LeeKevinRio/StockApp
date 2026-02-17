import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/market_provider.dart';

/// Market switcher widget - allows switching between Taiwan and US markets
class MarketSwitcher extends StatelessWidget {
  final VoidCallback? onMarketChanged;

  const MarketSwitcher({
    super.key,
    this.onMarketChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<MarketProvider>(
      builder: (context, marketProvider, child) {
        return SegmentedButton<StockMarket>(
          segments: const [
            ButtonSegment<StockMarket>(
              value: StockMarket.taiwan,
              label: Text('台股'),
              icon: Icon(Icons.flag, size: 16),
            ),
            ButtonSegment<StockMarket>(
              value: StockMarket.us,
              label: Text('美股'),
              icon: Icon(Icons.public, size: 16),
            ),
          ],
          selected: {marketProvider.currentMarket},
          onSelectionChanged: (Set<StockMarket> newSelection) {
            marketProvider.switchMarket(newSelection.first);
            onMarketChanged?.call();
          },
          style: ButtonStyle(
            visualDensity: VisualDensity.compact,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
        );
      },
    );
  }
}

/// Compact market switcher for use in app bars
class CompactMarketSwitcher extends StatelessWidget {
  final VoidCallback? onMarketChanged;

  const CompactMarketSwitcher({
    super.key,
    this.onMarketChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<MarketProvider>(
      builder: (context, marketProvider, child) {
        return Container(
          decoration: BoxDecoration(
            color: Colors.white.withAlpha(20),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.white.withAlpha(40)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _MarketChip(
                label: '台股',
                isSelected: marketProvider.isTaiwanMarket,
                onTap: () {
                  marketProvider.switchMarket(StockMarket.taiwan);
                  onMarketChanged?.call();
                },
              ),
              _MarketChip(
                label: '美股',
                isSelected: marketProvider.isUSMarket,
                onTap: () {
                  marketProvider.switchMarket(StockMarket.us);
                  onMarketChanged?.call();
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

class _MarketChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _MarketChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: '$label市場',
      selected: isSelected,
      button: true,
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: isSelected
                ? const Color(0xFF66BB6A) // 亮綠色，明顯突出
                : Colors.transparent,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSelected
                  ? Colors.white
                  : Colors.white.withAlpha(180),
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              fontSize: 13,
            ),
          ),
        ),
      ),
    );
  }
}

/// Market indicator badge - shows current market
class MarketBadge extends StatelessWidget {
  final String market;
  final double fontSize;

  const MarketBadge({
    super.key,
    required this.market,
    this.fontSize = 10,
  });

  @override
  Widget build(BuildContext context) {
    final isUS = market.toUpperCase() == 'US';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: isUS
            ? const Color(0xFF42A5F5).withAlpha(30)
            : const Color(0xFF66BB6A).withAlpha(30),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(
          color: isUS
              ? const Color(0xFF42A5F5).withAlpha(80)
              : const Color(0xFF66BB6A).withAlpha(80),
        ),
      ),
      child: Text(
        isUS ? 'US' : 'TW',
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.bold,
          color: isUS ? const Color(0xFF42A5F5) : const Color(0xFF66BB6A),
        ),
      ),
    );
  }
}
