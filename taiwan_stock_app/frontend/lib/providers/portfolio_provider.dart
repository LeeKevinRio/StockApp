import 'package:flutter/foundation.dart';
import '../models/portfolio.dart';
import '../services/api_service.dart';

class PortfolioProvider with ChangeNotifier {
  final ApiService _apiService;
  List<Portfolio> _portfolios = [];
  Portfolio? _selectedPortfolio;
  List<Position> _positions = [];
  List<Transaction> _transactions = [];
  PortfolioSummary? _summary;
  List<PositionAllocation> _allocations = [];
  bool _isLoading = false;
  String? _error;

  PortfolioProvider(this._apiService);

  // Getters
  List<Portfolio> get portfolios => _portfolios;
  Portfolio? get selectedPortfolio => _selectedPortfolio;
  List<Position> get positions => _positions;
  List<Transaction> get transactions => _transactions;
  PortfolioSummary? get summary => _summary;
  List<PositionAllocation> get allocations => _allocations;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// 是否有選中的投資組合
  bool get hasSelectedPortfolio => _selectedPortfolio != null;

  /// 總市值
  double get totalValue => _summary?.totalValue ?? 0;

  /// 總損益
  double get totalPnl => _summary?.totalPnl ?? 0;

  /// 總損益百分比
  double get totalPnlPercent => _summary?.totalPnlPercent ?? 0;

  /// 載入所有投資組合
  Future<void> loadPortfolios() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _portfolios = await _apiService.getPortfolios();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 刷新
  Future<void> refresh() async {
    await loadPortfolios();
    if (_selectedPortfolio != null) {
      await selectPortfolio(_selectedPortfolio!.id);
    }
  }

  /// 選擇投資組合
  Future<void> selectPortfolio(int portfolioId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _selectedPortfolio = await _apiService.getPortfolio(portfolioId);
      _positions = await _apiService.getPositions(portfolioId);
      _summary = await _apiService.getPortfolioSummary(portfolioId);
      _allocations = await _apiService.getPositionAllocation(portfolioId);
      _transactions = await _apiService.getTransactions(portfolioId);
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 創建投資組合
  Future<Portfolio> createPortfolio(CreatePortfolioRequest request) async {
    try {
      final portfolio = await _apiService.createPortfolio(request);
      _portfolios.add(portfolio);
      notifyListeners();
      return portfolio;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 更新投資組合
  Future<void> updatePortfolio(int portfolioId, {String? name, String? description}) async {
    try {
      final updated = await _apiService.updatePortfolio(
        portfolioId,
        name: name,
        description: description,
      );
      final index = _portfolios.indexWhere((p) => p.id == portfolioId);
      if (index != -1) {
        _portfolios[index] = updated;
      }
      if (_selectedPortfolio?.id == portfolioId) {
        _selectedPortfolio = updated;
      }
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 刪除投資組合
  Future<void> deletePortfolio(int portfolioId) async {
    try {
      await _apiService.deletePortfolio(portfolioId);
      _portfolios.removeWhere((p) => p.id == portfolioId);
      if (_selectedPortfolio?.id == portfolioId) {
        _selectedPortfolio = null;
        _positions = [];
        _transactions = [];
        _summary = null;
        _allocations = [];
      }
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 新增交易
  Future<Transaction> addTransaction(CreateTransactionRequest request) async {
    if (_selectedPortfolio == null) {
      throw Exception('請先選擇投資組合');
    }

    try {
      final transaction = await _apiService.addTransaction(
        _selectedPortfolio!.id,
        request,
      );
      _transactions.insert(0, transaction);
      // 刷新持倉和摘要
      await _refreshPortfolioData();
      return transaction;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      rethrow;
    }
  }

  /// 刷新投資組合數據
  Future<void> _refreshPortfolioData() async {
    if (_selectedPortfolio == null) return;

    try {
      _positions = await _apiService.getPositions(_selectedPortfolio!.id);
      _summary = await _apiService.getPortfolioSummary(_selectedPortfolio!.id);
      _allocations = await _apiService.getPositionAllocation(_selectedPortfolio!.id);
      _selectedPortfolio = await _apiService.getPortfolio(_selectedPortfolio!.id);

      // 更新 portfolios 列表中對應的項目
      final index = _portfolios.indexWhere((p) => p.id == _selectedPortfolio!.id);
      if (index != -1) {
        _portfolios[index] = _selectedPortfolio!;
      }

      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  /// 載入交易記錄
  Future<void> loadTransactions({int limit = 50}) async {
    if (_selectedPortfolio == null) return;

    try {
      _transactions = await _apiService.getTransactions(
        _selectedPortfolio!.id,
        limit: limit,
      );
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  /// 清除選擇
  void clearSelection() {
    _selectedPortfolio = null;
    _positions = [];
    _transactions = [];
    _summary = null;
    _allocations = [];
    notifyListeners();
  }

  /// 清除錯誤
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// 獲取盈利持倉
  List<Position> get profitablePositions =>
      _positions.where((p) => p.isProfitable).toList();

  /// 獲取虧損持倉
  List<Position> get losingPositions =>
      _positions.where((p) => p.isLosing).toList();
}
