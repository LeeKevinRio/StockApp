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
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(20),
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
    final theme = Theme.of(context);

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
                ? theme.colorScheme.primary
                : Colors.transparent,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: isSelected
                  ? theme.colorScheme.onPrimary
                  : theme.colorScheme.onSurfaceVariant,
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
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
      decoration: BoxDecoration(
        color: isUS ? Colors.blue.shade100 : Colors.green.shade100,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        isUS ? 'US' : 'TW',
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.bold,
          color: isUS ? Colors.blue.shade800 : Colors.green.shade800,
        ),
      ),
    );
  }
}
