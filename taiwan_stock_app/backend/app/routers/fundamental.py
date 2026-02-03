"""
Fundamental data router - 基本面數據、財務報表、股息、法人買賣超、融資融券 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas.fundamental import (
    FundamentalResponse,
    FinancialStatementsResponse,
    DividendResponse,
    InstitutionalResponse,
    MarginResponse,
)
from app.services.fundamental_service import fundamental_service
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/stocks", tags=["fundamental"])


@router.get("/{stock_id}/fundamental", response_model=FundamentalResponse)
async def get_stock_fundamental(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得股票基本面數據

    包含:
    - 估值指標: P/E, P/B, P/S, PEG
    - 獲利指標: EPS, ROE, ROA
    - 營收指標: 營收, 毛利率, 營業利益率, 淨利率
    - 市值相關: 市值, 企業價值

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    data = await fundamental_service.get_fundamentals(db, stock_id, market=market)
    if not data:
        raise HTTPException(status_code=404, detail="Fundamental data not available")

    # Map field names for response
    return FundamentalResponse(
        stock_id=data.get("stock_id", stock_id),
        report_date=data.get("report_date"),
        pe_ratio=data.get("pe_ratio"),
        forward_pe=data.get("forward_pe"),
        pb_ratio=data.get("pb_ratio"),
        ps_ratio=data.get("ps_ratio"),
        peg_ratio=data.get("peg_ratio"),
        eps=data.get("eps"),
        forward_eps=data.get("forward_eps"),
        roe=data.get("roe"),
        roa=data.get("roa"),
        revenue=data.get("revenue"),
        revenue_growth=data.get("revenue_growth"),
        gross_margin=data.get("gross_margin"),
        operating_margin=data.get("operating_margin"),
        net_margin=data.get("net_margin"),
        market_cap=data.get("market_cap"),
        enterprise_value=data.get("enterprise_value"),
        dividend_yield=data.get("dividend_yield"),
        beta=data.get("beta"),
        week_52_high=data.get("52_week_high"),
        week_52_low=data.get("52_week_low"),
    )


@router.get("/{stock_id}/financial-statements", response_model=FinancialStatementsResponse)
async def get_financial_statements(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得財務報表

    包含:
    - 損益表: 營收、毛利、營業利益、淨利、EBITDA
    - 資產負債表: 資產、負債、股東權益、流動資產/負債
    - 現金流量表: 營業/投資/融資現金流、自由現金流

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    data = await fundamental_service.get_financial_statements(db, stock_id, market=market)
    if not data:
        raise HTTPException(status_code=404, detail="Financial statements not available")

    return FinancialStatementsResponse(
        stock_id=stock_id,
        income_statement=data.get("income_statement", []),
        balance_sheet=data.get("balance_sheet", []),
        cash_flow=data.get("cash_flow", []),
    )


@router.get("/{stock_id}/dividends", response_model=List[DividendResponse])
async def get_dividends(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得股息歷史

    包含:
    - 年度現金股利
    - 年度股票股利
    - 除息日
    - 殖利率

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    data = await fundamental_service.get_dividends(db, stock_id, market=market)
    if not data:
        return []

    return [
        DividendResponse(
            stock_id=d.get("stock_id", stock_id),
            year=d.get("year", 0),
            cash_dividend=d.get("cash_dividend", 0),
            stock_dividend=d.get("stock_dividend", 0),
            total_dividend=d.get("total_dividend", 0),
            ex_dividend_date=d.get("ex_dividend_date"),
            payment_date=d.get("payment_date"),
            dividend_yield=d.get("dividend_yield"),
            payment_count=d.get("payment_count"),
            payments=d.get("payments", []),
        )
        for d in data
    ]


@router.get("/{stock_id}/institutional", response_model=List[InstitutionalResponse])
async def get_institutional_trading(
    stock_id: str,
    days: int = Query(30, description="Number of days to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得法人買賣超 (僅限台股)

    包含:
    - 外資買賣超
    - 投信買賣超
    - 自營商買賣超
    - 三大法人合計

    Args:
        stock_id: 股票代碼
        days: 取得天數 (預設30天)

    Note:
        此 API 僅支援台股，美股無法人買賣超資料
    """
    data = await fundamental_service.get_institutional_trading(db, stock_id, days=days)
    if not data:
        return []

    return [
        InstitutionalResponse(
            date=d.get("date", ""),
            foreign_buy=d.get("foreign_buy"),
            foreign_sell=d.get("foreign_sell"),
            foreign_net=d.get("foreign_net", 0),
            trust_buy=d.get("trust_buy"),
            trust_sell=d.get("trust_sell"),
            trust_net=d.get("trust_net", 0),
            dealer_buy=d.get("dealer_buy"),
            dealer_sell=d.get("dealer_sell"),
            dealer_net=d.get("dealer_net", 0),
            total_net=d.get("total_net", 0),
        )
        for d in data
    ]


@router.get("/{stock_id}/margin", response_model=List[MarginResponse])
async def get_margin_trading(
    stock_id: str,
    days: int = Query(30, description="Number of days to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得融資融券 (僅限台股)

    包含:
    - 融資買進/賣出/餘額
    - 融資使用率
    - 融券賣出/買進/餘額

    Args:
        stock_id: 股票代碼
        days: 取得天數 (預設30天)

    Note:
        此 API 僅支援台股，美股無融資融券資料
    """
    data = await fundamental_service.get_margin_trading(db, stock_id, days=days)
    if not data:
        return []

    return [
        MarginResponse(
            date=d.get("date", ""),
            margin_buy=d.get("margin_buy"),
            margin_sell=d.get("margin_sell"),
            margin_balance=d.get("margin_balance", 0),
            margin_limit=d.get("margin_limit"),
            margin_utilization=d.get("margin_utilization"),
            short_sell=d.get("short_sell"),
            short_buy=d.get("short_buy"),
            short_balance=d.get("short_balance", 0),
        )
        for d in data
    ]
