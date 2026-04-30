import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/market_provider.dart';

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _earningsData;
  Map<String, dynamic>? _dividendsData;
  Map<String, dynamic>? _economicData;
  Map<String, dynamic>? _holidaysData;
  bool _isLoading = true;
  String? _error;
  late DateTime _selectedMonth;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _selectedMonth = DateTime.now();
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final api = context.read<ApiService>();
      final market = context.read<MarketProvider>().marketCode;
      final results = await Future.wait([
        api.getEarningsCalendar(
            market: market,
            month: _selectedMonth.month,
            year: _selectedMonth.year),
        api.getDividendCalendar(
            market: market,
            month: _selectedMonth.month,
            year: _selectedMonth.year),
        api.getEconomicCalendar(
            market: market,
            month: _selectedMonth.month,
            year: _selectedMonth.year),
        api.getMarketHolidays(market: market, days: 180),
      ]);

      if (mounted) {
        setState(() {
          _earningsData = results[0];
          _dividendsData = results[1];
          _economicData = results[2];
          _holidaysData = results[3];
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _changeMonth(int delta) {
    setState(() {
      _selectedMonth = DateTime(
          _selectedMonth.year, _selectedMonth.month + delta);
    });
    _loadData();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (Navigator.of(context).canPop()) {
              Navigator.of(context).pop();
            } else {
              Navigator.of(context).pushReplacementNamed('/home');
            }
          },
        ),
        title: const Text('財報 / 除息日曆'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(text: '財報日曆'),
            Tab(text: '除息日曆'),
            Tab(text: '經濟行事曆'),
            Tab(text: '休市日'),
          ],
        ),
      ),
      body: Column(
        children: [
          // 月份選擇器
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Theme.of(context).cardColor,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                IconButton(
                  icon: const Icon(Icons.chevron_left),
                  onPressed: () => _changeMonth(-1),
                ),
                Text(
                  '${_selectedMonth.year} 年 ${_selectedMonth.month} 月',
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: const Icon(Icons.chevron_right),
                  onPressed: () => _changeMonth(1),
                ),
              ],
            ),
          ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text('載入失敗: $_error'),
                            ElevatedButton(
                                onPressed: _loadData,
                                child: const Text('重試')),
                          ],
                        ),
                      )
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildEventList(_earningsData),
                          _buildEventList(_dividendsData),
                          _buildEventList(_economicData),
                          _buildHolidaysList(_holidaysData),
                        ],
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildEventList(Map<String, dynamic>? data) {
    final events = (data?['events'] as List?) ?? [];

    if (events.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.event_busy, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('本月無相關事件', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(12),
        itemCount: events.length,
        itemBuilder: (context, index) {
          final event = events[index];
          return _buildEventCard(event);
        },
      ),
    );
  }

  /// 建構未來休市日列表（含日期、星期、假日名稱）
  Widget _buildHolidaysList(Map<String, dynamic>? data) {
    final holidays = (data?['holidays'] as List?) ?? [];
    final fromDate = data?['from_date'] ?? '';
    final toDate = data?['to_date'] ?? '';

    if (holidays.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.celebration, size: 64, color: Colors.green),
            const SizedBox(height: 12),
            Text('$fromDate ~ $toDate',
                style: const TextStyle(color: Colors.grey, fontSize: 12)),
            const SizedBox(height: 4),
            const Text('未來無國定休市日',
                style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(12),
        itemCount: holidays.length + 1,
        itemBuilder: (context, index) {
          if (index == 0) {
            // 標頭：說明範圍與用途
            return Padding(
              padding: const EdgeInsets.only(bottom: 8, left: 4),
              child: Text(
                '$fromDate ~ $toDate · 共 ${holidays.length} 個休市日',
                style: const TextStyle(color: Colors.grey, fontSize: 12),
              ),
            );
          }
          final h = holidays[index - 1] as Map<String, dynamic>;
          final dateStr = h['date'] ?? '';
          final weekday = h['weekday'] ?? '';
          final name = h['name'] ?? '市場休市';
          // 計算距離今天天數
          int? daysFromNow;
          try {
            final d = DateTime.parse(dateStr);
            final now = DateTime.now();
            final t0 = DateTime(now.year, now.month, now.day);
            daysFromNow = d.difference(t0).inDays;
          } catch (_) {}
          return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: Colors.orange.withValues(alpha: 0.15),
                child: Icon(Icons.event_busy, color: Colors.orange.shade800),
              ),
              title: Text(name,
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text('$dateStr · $weekday',
                  style: const TextStyle(color: Colors.grey)),
              trailing: daysFromNow != null
                  ? Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: daysFromNow <= 7
                            ? Colors.red.withValues(alpha: 0.1)
                            : Colors.grey.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        daysFromNow == 0
                            ? '今日'
                            : daysFromNow < 0
                                ? '已過'
                                : '$daysFromNow 天後',
                        style: TextStyle(
                          fontSize: 11,
                          color: daysFromNow <= 7
                              ? Colors.red.shade700
                              : Colors.grey.shade700,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    )
                  : null,
            ),
          );
        },
      ),
    );
  }

  Widget _buildEventCard(Map<String, dynamic> event) {
    final type = event['type'] ?? '';
    final importance = event['importance'] ?? 'medium';
    final dateStr = event['date'] ?? '';

    IconData icon;
    Color iconColor;
    if (type == 'earnings') {
      icon = Icons.assessment;
      iconColor = Colors.blue;
    } else if (type == 'revenue') {
      icon = Icons.bar_chart;
      iconColor = Colors.orange;
    } else if (type == 'cpi' || type == 'ppi') {
      icon = Icons.show_chart;
      iconColor = Colors.red;
    } else if (type == 'gdp') {
      icon = Icons.trending_up;
      iconColor = Colors.indigo;
    } else if (type == 'interest_rate' || type == 'fomc') {
      icon = Icons.account_balance;
      iconColor = Colors.purple;
    } else if (type == 'nonfarm_payrolls') {
      icon = Icons.people;
      iconColor = Colors.teal;
    } else if (type == 'pmi') {
      icon = Icons.factory;
      iconColor = Colors.brown;
    } else if (type == 'institutional') {
      icon = Icons.business;
      iconColor = Colors.blueGrey;
    } else if (type == 'dividend') {
      icon = Icons.payments;
      iconColor = Colors.green;
    } else {
      icon = Icons.event;
      iconColor = Colors.grey;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: importance == 'critical'
            ? const BorderSide(color: Colors.red, width: 1.5)
            : BorderSide.none,
      ),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: iconColor.withValues(alpha: 0.1),
          child: Icon(icon, color: iconColor),
        ),
        title: Text(event['title'] ?? '',
            style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(dateStr, style: const TextStyle(color: Colors.grey)),
            if (event['description'] != null)
              Text(event['description'],
                  style: const TextStyle(fontSize: 12)),
            if (event['cash_dividend'] != null)
              Text('現金股利: \$${event["cash_dividend"]}',
                  style: const TextStyle(
                      fontSize: 12, color: Colors.green)),
            if (event['eps_actual'] != null)
              Text(
                  'EPS: \$${event["eps_actual"]} (預估: \$${event["eps_estimate"] ?? "N/A"})',
                  style: const TextStyle(fontSize: 12)),
          ],
        ),
        trailing: importance == 'critical'
            ? const Icon(Icons.priority_high, color: Colors.red)
            : importance == 'high'
                ? const Icon(Icons.star, color: Colors.amber)
                : null,
        onTap: event['stock_id'] != null
            ? () {
                final market =
                    context.read<MarketProvider>().marketCode;
                Navigator.pushNamed(context, '/stock-detail',
                    arguments: {
                      'stockId': event['stock_id'],
                      'market': market,
                    });
              }
            : null,
      ),
    );
  }
}
