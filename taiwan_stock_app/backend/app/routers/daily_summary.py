"""
每日盤前摘要 API 路由
- 管理用戶訂閱與取消訂閱
- 預覽摘要內容
- 手動觸發發送
- 管理員批次發送
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.routers.auth import get_current_user, get_admin_user
from app.models.user import User
from app.database import get_db

router = APIRouter(prefix="/api/daily-summary", tags=["daily-summary"])


@router.get("/preview")
async def preview_summary(
    current_user: User = Depends(get_current_user),
):
    """
    預覽今日摘要數據（需要驗證）

    返回摘要 JSON，不發送郵件
    """
    # 延遲導入以避免循環依賴
    from app.services.daily_summary_service import DailySummaryService

    service = DailySummaryService()

    try:
        summary_data = await service.generate_summary()
        return {
            "status": "success",
            "user_email": current_user.email,
            "summary": summary_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成摘要失敗: {str(e)}"
        )


@router.post("/subscribe")
def subscribe_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    訂閱每日盤前摘要郵件

    將用戶的 daily_summary_enabled 設為 True
    """
    try:
        current_user.daily_summary_enabled = True
        db.commit()

        return {
            "status": "subscribed",
            "email": current_user.email,
            "message": "已成功訂閱每日盤前摘要"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"訂閱失敗: {str(e)}"
        )


@router.post("/unsubscribe")
def unsubscribe_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取消訂閱每日盤前摘要郵件

    將用戶的 daily_summary_enabled 設為 False
    """
    try:
        current_user.daily_summary_enabled = False
        db.commit()

        return {
            "status": "unsubscribed",
            "email": current_user.email,
            "message": "已成功取消訂閱每日盤前摘要"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"取消訂閱失敗: {str(e)}"
        )


@router.get("/status")
def get_subscription_status(
    current_user: User = Depends(get_current_user),
):
    """
    檢查用戶訂閱狀態

    返回用戶是否已訂閱每日盤前摘要
    """
    return {
        "subscribed": current_user.daily_summary_enabled,
        "email": current_user.email,
        "user_id": current_user.id
    }


@router.post("/send-now")
async def send_summary_now(
    current_user: User = Depends(get_current_user),
):
    """
    手動觸發發送摘要到當前用戶郵件

    立即生成並發送盤前摘要
    """
    # 延遲導入以避免循環依賴
    from app.services.daily_summary_service import DailySummaryService

    service = DailySummaryService()

    try:
        sent = await service.send_to_user(current_user.email)

        if sent:
            return {
                "status": "sent",
                "email": current_user.email,
                "message": f"摘要已發送到 {current_user.email}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="發送郵件失敗，請稍後重試"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"發送摘要失敗: {str(e)}"
        )


@router.post("/send-all")
async def send_summary_to_all(
    admin_user: User = Depends(get_admin_user),
):
    """
    管理員功能：觸發發送摘要到所有已訂閱用戶

    需要管理員權限（is_admin=True）
    """
    # 延遲導入以避免循環依賴
    from app.services.daily_summary_service import DailySummaryService

    service = DailySummaryService()

    try:
        success = await service.schedule_daily_summary()

        if success:
            return {
                "status": "completed",
                "admin_email": admin_user.email,
                "message": "已向所有訂閱用戶發送摘要"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="發送摘要失敗或無訂閱用戶"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批次發送失敗: {str(e)}"
        )
