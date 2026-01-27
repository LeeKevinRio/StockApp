"""
Fundamental data schemas - 基本面、股息、法人、籌碼相關Schema
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class FundamentalResponse(BaseModel):
    """基本面數據響應"""
    stock_id: str
    report_date: Optional[str] = None

    # Valuation metrics
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None

    # Profitability metrics
    eps: Optional[float] = None
    forward_eps: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None

    # Revenue metrics
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None

    # Market data
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None

    # 52-week range
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None

    class Config:
        from_attributes = True


class IncomeStatementItem(BaseModel):
    """損益表項目"""
    period: str
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expense: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None


class BalanceSheetItem(BaseModel):
    """資產負債表項目"""
    period: str
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    cash: Optional[float] = None
    total_debt: Optional[float] = None


class CashFlowItem(BaseModel):
    """現金流量表項目"""
    period: str
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None


class FinancialStatementsResponse(BaseModel):
    """財務報表響應"""
    stock_id: str
    income_statement: List[IncomeStatementItem] = []
    balance_sheet: List[BalanceSheetItem] = []
    cash_flow: List[CashFlowItem] = []


class DividendPayment(BaseModel):
    """單次股息發放"""
    date: str
    amount: float


class DividendResponse(BaseModel):
    """股息歷史響應"""
    stock_id: str
    year: int
    cash_dividend: float = 0
    stock_dividend: float = 0
    total_dividend: float = 0
    ex_dividend_date: Optional[str] = None
    payment_date: Optional[str] = None
    dividend_yield: Optional[float] = None
    payment_count: Optional[int] = None
    payments: List[DividendPayment] = []

    class Config:
        from_attributes = True


class InstitutionalResponse(BaseModel):
    """法人買賣超響應"""
    date: str
    foreign_buy: Optional[int] = None
    foreign_sell: Optional[int] = None
    foreign_net: int
    trust_buy: Optional[int] = None
    trust_sell: Optional[int] = None
    trust_net: int
    dealer_buy: Optional[int] = None
    dealer_sell: Optional[int] = None
    dealer_net: int
    total_net: int


class MarginResponse(BaseModel):
    """融資融券響應"""
    date: str
    margin_buy: Optional[int] = None
    margin_sell: Optional[int] = None
    margin_balance: int
    margin_limit: Optional[int] = None
    margin_utilization: Optional[float] = None
    short_sell: Optional[int] = None
    short_buy: Optional[int] = None
    short_balance: int


class ScreenCriteria(BaseModel):
    """股票篩選條件"""
    pe_min: Optional[float] = None
    pe_max: Optional[float] = None
    pb_min: Optional[float] = None
    pb_max: Optional[float] = None
    dividend_yield_min: Optional[float] = None
    roe_min: Optional[float] = None
    roa_min: Optional[float] = None
    gross_margin_min: Optional[float] = None
    revenue_growth_min: Optional[float] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    industry: Optional[str] = None


class ScreenResultItem(BaseModel):
    """篩選結果項目"""
    stock_id: str
    name: str
    industry: Optional[str] = None
    market: Optional[str] = None
    market_region: str = "TW"
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    eps: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    market_cap: Optional[float] = None
    dividend_yield: Optional[float] = None
    total_dividend: Optional[float] = None
    report_date: Optional[str] = None


class PresetScreen(BaseModel):
    """預設篩選條件"""
    id: str
    name: str
    name_en: str
    description: str
    criteria: ScreenCriteria


class ScreenResponse(BaseModel):
    """篩選響應"""
    total: int
    stocks: List[ScreenResultItem]
