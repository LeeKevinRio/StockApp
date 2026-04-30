"""
投資組合推薦路由
Portfolio Recommendation Router - 提供 AI 驅動的投資組合推薦和分析端點
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.routers.auth import get_current_user
from app.models.user import User
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio/recommend", tags=["portfolio-recommendation"])


# ==================== 依賴注入 ====================

def get_portfolio_recommendation_service():
    """延遲載入投資組合推薦服務"""
    from app.services.portfolio_recommendation_service import PortfolioRecommendationService
    return PortfolioRecommendationService()


# ==================== 端點定義 ====================

@router.get("/")
async def get_portfolio_recommendation(
    risk_level: str = Query(None, description="風險等級: conservative/moderate/aggressive（可選，若未提供則使用用戶設定或自動檢測）"),
    market: str = Query("台灣市場", description="市場: 台灣市場/美國市場"),
    budget: float = Query(100000, description="預算金額"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_portfolio_recommendation_service)
) -> dict:
    """
    取得 AI 投資組合推薦

    若未提供 risk_level，將使用用戶資料庫中的 risk_preference；
    若用戶無設定，則根據現有持倉自動檢測。
    """
    try:
        # 確定要使用的風險等級
        final_risk_level = risk_level

        if not final_risk_level:
            # 首先嘗試使用用戶資料庫中的偏好設定
            user_pref = current_user.risk_preference

            # 將英文 API 參數轉換為中文服務參數
            if user_pref == "conservative":
                final_risk_level = "保守型"
            elif user_pref == "aggressive":
                final_risk_level = "積極型"
            else:  # moderate 或 None
                final_risk_level = "穩健型"

            # 如果仍為 None，嘗試從現有持倉自動檢測
            if not final_risk_level:
                from app.services.portfolio_service import PortfolioService
                portfolio_service = PortfolioService()

                # 取得用戶的主投資組合
                portfolios = portfolio_service.get_user_portfolios(db, current_user.id)
                if portfolios and len(portfolios) > 0:
                    portfolio = portfolios[0]
                    positions = portfolio_service.get_positions(db, portfolio.id, current_user.id)
                    final_risk_level = service.detect_risk_profile(positions, db=db)
                else:
                    final_risk_level = "穩健型"

        # 將中文風險等級標準化
        if final_risk_level not in ["保守型", "穩健型", "積極型"]:
            # 嘗試從英文參數轉換
            if final_risk_level and final_risk_level.lower() == "conservative":
                final_risk_level = "保守型"
            elif final_risk_level and final_risk_level.lower() == "aggressive":
                final_risk_level = "積極型"
            else:
                final_risk_level = "穩健型"

        # 生成推薦
        result = service.generate_recommendation(
            risk_level=final_risk_level,
            market=market,
            budget=budget,
            db=db
        )

        return {
            "success": result.get("success", False),
            "user_id": current_user.id,
            "risk_level": final_risk_level,
            **result
        }

    except Exception as e:
        logger.error(f"取得投資組合推薦失敗 (用戶 {current_user.id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得推薦失敗: {str(e)}"
        )


@router.get("/risk-profile")
async def get_risk_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_portfolio_recommendation_service)
) -> dict:
    """
    取得用戶的風險偏好分析

    根據現有持倉分析用戶的實際風險偏好，並提供配置建議。
    """
    try:
        from app.services.portfolio_service import PortfolioService
        portfolio_service = PortfolioService()

        # 取得用戶的主投資組合
        portfolios = portfolio_service.get_user_portfolios(db, current_user.id)

        if not portfolios:
            return {
                "success": True,
                "user_id": current_user.id,
                "has_portfolio": False,
                "message": "用戶尚無投資組合",
                "detected_risk_level": "穩健型",
                "user_preference": current_user.risk_preference,
                "available_profiles": service.get_risk_profiles()
            }

        portfolio = portfolios[0]
        positions = portfolio_service.get_positions(db, portfolio.id, current_user.id)

        # 檢測風險偏好
        detected_risk = service.detect_risk_profile(positions, db=db)

        # 計算投資組合指標
        metrics = service.calculate_portfolio_metrics(positions)

        # 取得所有風險配置
        risk_profiles = service.get_risk_profiles()

        return {
            "success": True,
            "user_id": current_user.id,
            "has_portfolio": True,
            "user_preference": current_user.risk_preference,
            "detected_risk_level": detected_risk,
            "position_count": len(positions),
            "portfolio_metrics": metrics,
            "available_profiles": risk_profiles
        }

    except Exception as e:
        logger.error(f"取得風險偏好分析失敗 (用戶 {current_user.id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失敗: {str(e)}"
        )


@router.get("/rebalance")
async def get_rebalance_suggestions(
    portfolio_id: int = Query(..., description="投資組合 ID"),
    tolerance: float = Query(0.05, description="容許偏差比例，預設 0.05 (5%)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_portfolio_recommendation_service)
) -> dict:
    """
    取得投資組合再平衡建議

    檢查現有持倉是否超過目標配置的容許範圍，
    並提供具體的買賣建議。
    """
    try:
        # 檢查投資組合歸屬
        from app.services.portfolio_service import PortfolioService
        portfolio_service = PortfolioService()

        portfolio = portfolio_service.get_portfolio(db, portfolio_id, current_user.id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="投資組合不存在或無權限存取"
            )

        # 檢查再平衡狀態
        result = service.check_rebalance_needed(
            db=db,
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            tolerance=tolerance
        )

        return {
            "success": result.get("success", False),
            "user_id": current_user.id,
            "portfolio_id": portfolio_id,
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取得再平衡建議失敗 (用戶 {current_user.id}, 投資組合 {portfolio_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得建議失敗: {str(e)}"
        )


@router.put("/risk-preference")
async def update_risk_preference(
    request_body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    更新用戶的風險偏好設定

    請求體格式：
    {
        "risk_level": "conservative" | "moderate" | "aggressive"
    }
    """
    try:
        # 驗證請求體
        if not request_body or "risk_level" not in request_body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少必需的 risk_level 參數"
            )

        risk_level = request_body.get("risk_level", "").lower()

        # 驗證風險等級
        valid_levels = ["conservative", "moderate", "aggressive"]
        if risk_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無效的風險等級。允許的值: {', '.join(valid_levels)}"
            )

        # 更新用戶記錄
        current_user.risk_preference = risk_level
        db.commit()
        db.refresh(current_user)

        logger.info(f"用戶 {current_user.id} 的風險偏好已更新為: {risk_level}")

        return {
            "success": True,
            "user_id": current_user.id,
            "risk_preference": current_user.risk_preference,
            "message": f"風險偏好已更新為 {risk_level}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新風險偏好失敗 (用戶 {current_user.id}): {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失敗: {str(e)}"
        )
