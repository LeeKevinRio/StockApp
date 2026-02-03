"""
Stock Screener router - 股票篩選器 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas.fundamental import (
    ScreenCriteria,
    ScreenResultItem,
    ScreenResponse,
    PresetScreen,
)
from app.services.screener_service import screener_service
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.post("/search", response_model=ScreenResponse)
async def screen_stocks(
    criteria: ScreenCriteria,
    market: str = Query("TW", description="Market region: TW or US"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    依條件篩選股票

    支援的篩選條件:
    - pe_min, pe_max: 本益比範圍
    - pb_min, pb_max: 股價淨值比範圍
    - dividend_yield_min: 最低殖利率 (%)
    - roe_min: 最低 ROE (%)
    - roa_min: 最低 ROA (%)
    - gross_margin_min: 最低毛利率 (%)
    - revenue_growth_min: 最低營收成長率 (%)
    - market_cap_min, market_cap_max: 市值範圍
    - industry: 產業別

    Args:
        criteria: 篩選條件
        market: 市場 - "TW"(台股) 或 "US"(美股)
        limit: 最大結果數

    Example:
        ```json
        {
            "pe_max": 15,
            "dividend_yield_min": 5,
            "roe_min": 10
        }
        ```
    """
    criteria_dict = criteria.model_dump(exclude_none=True)

    stocks = await screener_service.screen_stocks(
        db=db,
        criteria=criteria_dict,
        market=market,
        limit=limit
    )

    result_items = [
        ScreenResultItem(
            stock_id=s.get("stock_id", ""),
            name=s.get("name", ""),
            industry=s.get("industry"),
            market=s.get("market"),
            market_region=s.get("market_region", market),
            pe_ratio=s.get("pe_ratio"),
            pb_ratio=s.get("pb_ratio"),
            eps=s.get("eps"),
            roe=s.get("roe"),
            roa=s.get("roa"),
            gross_margin=s.get("gross_margin"),
            market_cap=s.get("market_cap"),
            dividend_yield=s.get("dividend_yield"),
            total_dividend=s.get("total_dividend"),
            report_date=s.get("report_date"),
        )
        for s in stocks
    ]

    return ScreenResponse(
        total=len(result_items),
        stocks=result_items
    )


@router.get("/presets", response_model=List[PresetScreen])
async def get_preset_screens(
    current_user: User = Depends(get_current_user),
):
    """
    取得預設篩選條件列表

    提供常用的篩選策略:
    - high_dividend: 高殖利率 (殖利率 > 5%)
    - low_pe: 低本益比 (P/E < 15)
    - high_roe: 高ROE (ROE > 15%)
    - value_stocks: 價值股 (P/E < 12, P/B < 1.5, 殖利率 > 3%)
    - growth_stocks: 成長股 (ROE > 20%, 營收成長 > 10%)
    - blue_chip: 藍籌股 (市值 > 500億, ROE > 10%)
    """
    presets = await screener_service.get_preset_screens()

    return [
        PresetScreen(
            id=p["id"],
            name=p["name"],
            name_en=p["name_en"],
            description=p["description"],
            criteria=ScreenCriteria(**p["criteria"])
        )
        for p in presets
    ]


@router.get("/presets/{preset_id}", response_model=ScreenResponse)
async def get_preset_screen_results(
    preset_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    執行預設篩選

    Args:
        preset_id: 預設篩選 ID (如 'high_dividend', 'low_pe', 'high_roe' 等)
        market: 市場 - "TW"(台股) 或 "US"(美股)
        limit: 最大結果數
    """
    stocks = await screener_service.get_preset_screen_results(
        db=db,
        preset_id=preset_id,
        market=market,
        limit=limit
    )

    if not stocks and preset_id not in screener_service.PRESET_SCREENS:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

    result_items = [
        ScreenResultItem(
            stock_id=s.get("stock_id", ""),
            name=s.get("name", ""),
            industry=s.get("industry"),
            market=s.get("market"),
            market_region=s.get("market_region", market),
            pe_ratio=s.get("pe_ratio"),
            pb_ratio=s.get("pb_ratio"),
            eps=s.get("eps"),
            roe=s.get("roe"),
            roa=s.get("roa"),
            gross_margin=s.get("gross_margin"),
            market_cap=s.get("market_cap"),
            dividend_yield=s.get("dividend_yield"),
            total_dividend=s.get("total_dividend"),
            report_date=s.get("report_date"),
        )
        for s in stocks
    ]

    return ScreenResponse(
        total=len(result_items),
        stocks=result_items
    )


@router.get("/industries")
async def get_industries(
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得產業列表

    回傳指定市場的所有產業別，用於篩選條件的產業下拉選單

    Args:
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    industries = await screener_service.get_industries(db, market=market)
    return {"industries": industries}


@router.get("/top/{metric}")
async def get_top_by_metric(
    metric: str,
    market: str = Query("TW", description="Market region: TW or US"),
    ascending: bool = Query(False, description="Sort ascending if true"),
    limit: int = Query(20, description="Number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    依特定指標排名取得股票

    支援的指標:
    - pe_ratio: 本益比
    - pb_ratio: 股價淨值比
    - eps: 每股盈餘
    - roe: 股東權益報酬率
    - roa: 資產報酬率
    - gross_margin: 毛利率
    - market_cap: 市值

    Args:
        metric: 排名指標
        market: 市場 - "TW"(台股) 或 "US"(美股)
        ascending: 升序排列 (True) 或降序 (False)
        limit: 結果數量

    Example:
        - GET /api/screener/top/roe?ascending=false&limit=10 取得 ROE 前10名
        - GET /api/screener/top/pe_ratio?ascending=true&limit=20 取得本益比最低20名
    """
    valid_metrics = ["pe_ratio", "pb_ratio", "eps", "roe", "roa", "gross_margin", "market_cap"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
        )

    stocks = await screener_service.get_top_by_metric(
        db=db,
        metric=metric,
        market=market,
        ascending=ascending,
        limit=limit
    )

    return {
        "metric": metric,
        "ascending": ascending,
        "total": len(stocks),
        "stocks": stocks
    }
