import 'package:flutter/material.dart';
import '../models/watchlist_item.dart';

class StockCard extends StatelessWidget {
  final WatchlistItem stock;
  final VoidCallback onTap;
  final VoidCallback? onDelete;

  const StockCard({
    super.key,
    required this.stock,
    required this.onTap,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final priceColor = stock.isUp
        ? Colors.red
        : stock.isDown
            ? Colors.green
            : Colors.grey;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // 股票代碼與名稱
              Expanded(
                flex: 2,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      stock.stockId,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      stock.name,
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                      ),
                    ),
                    if (stock.industry != null)
                      Text(
                        stock.industry!,
                        style: TextStyle(
                          color: Colors.grey[500],
                          fontSize: 12,
                        ),
                      ),
                  ],
                ),
              ),
              // 股價
              if (stock.currentPrice != null)
                Expanded(
                  flex: 2,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        stock.currentPrice!.toStringAsFixed(2),
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: priceColor,
                        ),
                      ),
                      if (stock.changePercent != null)
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            Icon(
                              stock.isUp
                                  ? Icons.arrow_drop_up
                                  : stock.isDown
                                      ? Icons.arrow_drop_down
                                      : Icons.remove,
                              color: priceColor,
                              size: 20,
                            ),
                            Text(
                              '${stock.changePercent! >= 0 ? '+' : ''}${stock.changePercent!.toStringAsFixed(2)}%',
                              style: TextStyle(color: priceColor),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              // 刪除按鈕
              if (onDelete != null)
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.grey),
                  onPressed: onDelete,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
