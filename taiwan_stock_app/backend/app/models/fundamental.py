"""
Fundamental data models - 基本面、股息、法人買賣超、融資融券
"""
from sqlalchemy import Column, String, Integer, Date, DateTime, BigInteger, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class StockFundamental(Base):
    """基本面數據"""
    __tablename__ = "stock_fundamentals"
    __table_args__ = (UniqueConstraint('stock_id', 'report_date', name='uix_fundamental_stock_date'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)

    # 估值指標
    pe_ratio = Column(Numeric(10, 2))        # 本益比
    pb_ratio = Column(Numeric(10, 2))        # 股價淨值比
    ps_ratio = Column(Numeric(10, 2))        # 股價營收比

    # 獲利指標
    eps = Column(Numeric(10, 2))             # 每股盈餘
    roe = Column(Numeric(10, 2))             # 股東權益報酬率 (%)
    roa = Column(Numeric(10, 2))             # 資產報酬率 (%)

    # 營收指標
    revenue = Column(Numeric(18, 2))         # 營收
    gross_margin = Column(Numeric(10, 2))    # 毛利率 (%)
    operating_margin = Column(Numeric(10, 2)) # 營業利益率 (%)
    net_margin = Column(Numeric(10, 2))      # 淨利率 (%)

    # 市值
    market_cap = Column(Numeric(18, 2))      # 市值

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StockDividend(Base):
    """股息資訊"""
    __tablename__ = "stock_dividends"
    __table_args__ = (UniqueConstraint('stock_id', 'year', name='uix_dividend_stock_year'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)

    cash_dividend = Column(Numeric(10, 4))    # 現金股利
    stock_dividend = Column(Numeric(10, 4))   # 股票股利
    total_dividend = Column(Numeric(10, 4))   # 合計股利
    ex_dividend_date = Column(Date)           # 除息日
    payment_date = Column(Date)               # 發放日
    dividend_yield = Column(Numeric(10, 2))   # 殖利率 (%)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InstitutionalTrading(Base):
    """法人買賣超 (台股專用)"""
    __tablename__ = "institutional_trading"
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uix_institutional_stock_date'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    foreign_buy = Column(BigInteger)          # 外資買
    foreign_sell = Column(BigInteger)         # 外資賣
    foreign_net = Column(BigInteger)          # 外資淨買賣

    trust_buy = Column(BigInteger)            # 投信買
    trust_sell = Column(BigInteger)           # 投信賣
    trust_net = Column(BigInteger)            # 投信淨買賣

    dealer_buy = Column(BigInteger)           # 自營商買
    dealer_sell = Column(BigInteger)          # 自營商賣
    dealer_net = Column(BigInteger)           # 自營商淨買賣

    total_net = Column(BigInteger)            # 三大法人合計

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarginTrading(Base):
    """融資融券 (台股專用)"""
    __tablename__ = "margin_trading"
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uix_margin_stock_date'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    margin_buy = Column(BigInteger)           # 融資買進
    margin_sell = Column(BigInteger)          # 融資賣出
    margin_balance = Column(BigInteger)       # 融資餘額
    margin_limit = Column(BigInteger)         # 融資限額
    margin_utilization = Column(Numeric(10, 2)) # 融資使用率 (%)

    short_sell = Column(BigInteger)           # 融券賣出
    short_buy = Column(BigInteger)            # 融券買進
    short_balance = Column(BigInteger)        # 融券餘額

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FinancialStatement(Base):
    """財務報表數據"""
    __tablename__ = "financial_statements"
    __table_args__ = (UniqueConstraint('stock_id', 'report_year', 'report_quarter', name='uix_fs_stock_period'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    report_year = Column(Integer, nullable=False, index=True)
    report_quarter = Column(Integer, nullable=False)  # 1, 2, 3, 4

    # 損益表項目
    revenue = Column(Numeric(18, 2))          # 營收
    cost_of_revenue = Column(Numeric(18, 2))  # 營業成本
    gross_profit = Column(Numeric(18, 2))     # 毛利
    operating_expense = Column(Numeric(18, 2)) # 營業費用
    operating_income = Column(Numeric(18, 2)) # 營業利益
    net_income = Column(Numeric(18, 2))       # 淨利

    # 資產負債表項目
    total_assets = Column(Numeric(18, 2))     # 總資產
    total_liabilities = Column(Numeric(18, 2)) # 總負債
    total_equity = Column(Numeric(18, 2))     # 股東權益
    current_assets = Column(Numeric(18, 2))   # 流動資產
    current_liabilities = Column(Numeric(18, 2)) # 流動負債

    # 現金流量表項目
    operating_cash_flow = Column(Numeric(18, 2))  # 營業現金流
    investing_cash_flow = Column(Numeric(18, 2))  # 投資現金流
    financing_cash_flow = Column(Numeric(18, 2))  # 融資現金流
    free_cash_flow = Column(Numeric(18, 2))       # 自由現金流

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
