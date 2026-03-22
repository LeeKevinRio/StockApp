"""
宏觀經濟儀表板路由
提供經濟健康評分、市場制度、扇區衝擊分析等端點
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.routers.auth import get_current_user
from app.models.user import User
from app.database import get_db

router = APIRouter(prefix="/api/macro", tags=["macro"])


def get_macro_service():
    """
    惰性載入宏觀經濟服務
    避免循環依賴與啟動時的初始化問題
    """
    from app.services.macro_dashboard_service import macro_dashboard_service
    return macro_dashboard_service


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取得完整儀表板數據

    包含：經濟健康評分、市場制度、美國/台灣經濟指標、
    全球資產價格、扇區衝擊分析、歷史背景、關鍵要點

    Returns:
        包含所有指標與分析的完整儀表板字典
    """
    try:
        service = get_macro_service()
        dashboard_data = service.get_dashboard_data()
        return {
            "success": True,
            "data": dashboard_data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得儀表板數據失敗: {str(e)}",
        )


@router.get("/health-score")
async def get_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取得經濟健康評分

    Returns:
        包含美國、台灣、全球風險評分，以及殖利率曲線狀態、通膨趨勢

        Example response:
        {
            "us_score": 35.5,           # -100 ~ +100
            "taiwan_score": 20.3,       # -100 ~ +100
            "global_risk_score": -15.2, # 負數表示高風險
            "yield_curve_status": "normal",  # normal/flat/inverted
            "inflation_trend": "stable"  # rising/stable/falling
        }
    """
    try:
        service = get_macro_service()
        health_score = service.calculate_economic_health()

        return {
            "success": True,
            "data": {
                "us_score": health_score.us_score,
                "taiwan_score": health_score.taiwan_score,
                "global_risk_score": health_score.global_risk_score,
                "yield_curve_status": health_score.yield_curve_status,
                "inflation_trend": health_score.inflation_trend,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"計算經濟健康評分失敗: {str(e)}",
        )


@router.get("/market-regime")
async def get_market_regime(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取得當前市場制度

    Returns:
        市場風險偏好狀態（risk_on/risk_off/transitioning）、VIX 水準、
        殖利率曲線信號、Fed 政策方向、信心度

        Example response:
        {
            "regime": "risk_on",
            "vix_level": "medium",
            "yield_curve_signal": "normal",
            "fed_direction": "neutral",
            "confidence": 0.75
        }
    """
    try:
        service = get_macro_service()
        regime = service.detect_market_regime()

        return {
            "success": True,
            "data": {
                "regime": regime.regime,
                "vix_level": regime.vix_level,
                "yield_curve_signal": regime.yield_curve_signal,
                "fed_direction": regime.fed_direction,
                "confidence": regime.confidence,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"偵測市場制度失敗: {str(e)}",
        )


@router.get("/sector-impact")
async def get_sector_impact(
    market: str = Query("TW", pattern="^(TW|US)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取得扇區衝擊分析

    Args:
        market: 市場代碼 (TW=台灣, US=美國)

    Returns:
        扇區列表，各包含衝擊評估 (positive/neutral/negative)、
        評分 (-100~+100)、詳細說明

        Example response:
        {
            "success": true,
            "data": [
                {
                    "sector": "Semiconductors (TSMC)",
                    "impact": "positive",
                    "score": 25,
                    "rationale": "全球需求強勁，台積電受益"
                },
                ...
            ]
        }
    """
    try:
        # 統一市場代碼為小寫
        market_lower = market.lower()
        if market_lower not in ["tw", "us"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="市場代碼必須為 TW 或 US",
            )

        service = get_macro_service()
        impacts = service.analyze_macro_impact_on_stocks(market_lower)

        # 將 dataclass 轉換為字典
        impact_dicts = [
            {
                "sector": impact.sector,
                "impact": impact.impact,
                "score": impact.score,
                "rationale": impact.rationale,
            }
            for impact in impacts
        ]

        return {
            "success": True,
            "data": impact_dicts,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析扇區衝擊失敗: {str(e)}",
        )


@router.get("/historical-context")
async def get_historical_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取得歷史背景與百分位排名

    比較當前經濟指標與歷史平均值，提供百分位排名與
    歷史極值分析，幫助判斷當前環境的相對位置

    Returns:
        包含各指標當前值、百分位排名、歷史評估的字典

        Example response:
        {
            "success": true,
            "data": {
                "cpi": {
                    "current_value": 310.5,
                    "change_pct": 0.18,
                    "percentile": 55,
                    "assessment": "正常"
                },
                "unemployment": {
                    "current_value": 4.2,
                    "percentile": 45,
                    "assessment": "良好就業"
                },
                ...
                "updated_at": "2026-03-22 10:30:45"
            }
        }
    """
    try:
        service = get_macro_service()
        context = service.get_historical_context()

        return {
            "success": True,
            "data": context,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得歷史背景失敗: {str(e)}",
        )
