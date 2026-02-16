import 'package:flutter/material.dart';

/// Sort options for stock lists
enum SortOption {
  nameAsc('名稱 A-Z', Icons.sort_by_alpha),
  nameDesc('名稱 Z-A', Icons.sort_by_alpha),
  priceHigh('價格由高到低', Icons.arrow_downward),
  priceLow('價格由低到高', Icons.arrow_upward),
  changeHigh('漲幅由高到低', Icons.trending_up),
  changeLow('漲幅由低到高', Icons.trending_down),
  volumeHigh('成交量由高到低', Icons.bar_chart),
  addedRecent('最近加入', Icons.access_time);

  final String label;
  final IconData icon;

  const SortOption(this.label, this.icon);
}

/// A reusable sort and filter bar widget
class SortFilterBar extends StatelessWidget {
  final SortOption currentSort;
  final ValueChanged<SortOption> onSortChanged;
  final VoidCallback? onFilterPressed;
  final bool showFilterButton;
  final int? filterCount;

  const SortFilterBar({
    super.key,
    required this.currentSort,
    required this.onSortChanged,
    this.onFilterPressed,
    this.showFilterButton = false,
    this.filterCount,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          // Sort dropdown
          Expanded(
            child: _SortDropdown(
              currentSort: currentSort,
              onSortChanged: onSortChanged,
            ),
          ),
          if (showFilterButton) ...[
            const SizedBox(width: 8),
            _FilterButton(
              onPressed: onFilterPressed,
              filterCount: filterCount,
            ),
          ],
        ],
      ),
    );
  }
}

class _SortDropdown extends StatelessWidget {
  final SortOption currentSort;
  final ValueChanged<SortOption> onSortChanged;

  const _SortDropdown({
    required this.currentSort,
    required this.onSortChanged,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => _showSortBottomSheet(context),
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          border: Border.all(color: Theme.of(context).dividerColor),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(currentSort.icon, size: 18, color: Theme.of(context).primaryColor),
            const SizedBox(width: 8),
            Text(
              currentSort.label,
              style: TextStyle(
                fontSize: 14,
                color: Theme.of(context).textTheme.bodyMedium?.color,
              ),
            ),
            const SizedBox(width: 4),
            Icon(
              Icons.arrow_drop_down,
              size: 20,
              color: Theme.of(context).textTheme.bodySmall?.color,
            ),
          ],
        ),
      ),
    );
  }

  void _showSortBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => SortOptionsBottomSheet(
        currentSort: currentSort,
        onSortSelected: (option) {
          onSortChanged(option);
          Navigator.pop(context);
        },
      ),
    );
  }
}

class _FilterButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final int? filterCount;

  const _FilterButton({
    this.onPressed,
    this.filterCount,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        IconButton(
          icon: const Icon(Icons.filter_list),
          onPressed: onPressed,
          style: IconButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: BorderSide(color: Theme.of(context).dividerColor),
            ),
          ),
        ),
        if (filterCount != null && filterCount! > 0)
          Positioned(
            right: 4,
            top: 4,
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor,
                shape: BoxShape.circle,
              ),
              child: Text(
                filterCount.toString(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
      ],
    );
  }
}

/// Bottom sheet for selecting sort options
class SortOptionsBottomSheet extends StatelessWidget {
  final SortOption currentSort;
  final ValueChanged<SortOption> onSortSelected;

  const SortOptionsBottomSheet({
    super.key,
    required this.currentSort,
    required this.onSortSelected,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '排序方式',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Flexible(
            child: ListView(
              shrinkWrap: true,
              children: SortOption.values.map((option) {
                final isSelected = option == currentSort;
                return ListTile(
                  leading: Icon(
                    option.icon,
                    color: isSelected ? Theme.of(context).primaryColor : null,
                  ),
                  title: Text(
                    option.label,
                    style: TextStyle(
                      color: isSelected ? Theme.of(context).primaryColor : null,
                      fontWeight: isSelected ? FontWeight.bold : null,
                    ),
                  ),
                  trailing: isSelected
                      ? Icon(Icons.check, color: Theme.of(context).primaryColor)
                      : null,
                  onTap: () => onSortSelected(option),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

/// A chip-style filter selector
class FilterChips extends StatelessWidget {
  final List<String> options;
  final Set<String> selectedOptions;
  final ValueChanged<String> onToggle;

  const FilterChips({
    super.key,
    required this.options,
    required this.selectedOptions,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: options.map((option) {
        final isSelected = selectedOptions.contains(option);
        return FilterChip(
          label: Text(option),
          selected: isSelected,
          onSelected: (_) => onToggle(option),
          selectedColor: Theme.of(context).primaryColor.withValues(alpha: 0.2),
          checkmarkColor: Theme.of(context).primaryColor,
        );
      }).toList(),
    );
  }
}
