"""
AI router - AI 建議與問答
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.models import User, Watchlist, Stock, AIReport, AIChatHistory
from app.schemas import AISuggestion, AIChatRequest, AIChatResponse, ChatMessage
from app.services import AISuggestionService, AIChatService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai"])
suggestion_service = AISuggestionService()
chat_service = AIChatService()


@router.get("/suggestions", response_model=List[AISuggestion])
def get_ai_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得 AI 每日建議（所有自選股）"""
    # Get user's watchlist
    watchlist = (
        db.query(Watchlist, Stock)
        .join(Stock, Watchlist.stock_id == Stock.stock_id)
        .filter(Watchlist.user_id == current_user.id)
        .all()
    )

    results = []
    today = date.today()

    for wl, stock in watchlist:
        # Check if report already exists for today
        existing_report = (
            db.query(AIReport)
            .filter(
                AIReport.user_id == current_user.id,
                AIReport.stock_id == stock.stock_id,
                AIReport.report_date == today,
            )
            .first()
        )

        if existing_report:
            results.append(
                AISuggestion(
                    stock_id=existing_report.stock_id,
                    name=stock.name,
                    suggestion=existing_report.suggestion,
                    confidence=float(existing_report.confidence),
                    target_price=existing_report.target_price,
                    stop_loss_price=existing_report.stop_loss_price,
                    reasoning=existing_report.reasoning,
                    key_factors=existing_report.key_factors,
                    report_date=existing_report.report_date,
                )
            )
        else:
            # Generate new suggestion
            try:
                suggestion_data = suggestion_service.generate_suggestion(
                    stock.stock_id, stock.name
                )

                # Save to database
                report = AIReport(
                    user_id=current_user.id,
                    stock_id=stock.stock_id,
                    report_date=today,
                    suggestion=suggestion_data["suggestion"],
                    confidence=suggestion_data["confidence"],
                    target_price=suggestion_data.get("target_price"),
                    stop_loss_price=suggestion_data.get("stop_loss_price"),
                    reasoning=suggestion_data["reasoning"],
                    key_factors=suggestion_data["key_factors"],
                )
                db.add(report)
                db.commit()

                results.append(AISuggestion(**suggestion_data))
            except Exception as e:
                # Skip if error
                continue

    return results


@router.get("/suggestions/{stock_id}", response_model=AISuggestion)
def get_stock_suggestion(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得單一股票 AI 建議"""
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    today = date.today()

    # Check if report already exists for today
    existing_report = (
        db.query(AIReport)
        .filter(
            AIReport.user_id == current_user.id,
            AIReport.stock_id == stock_id,
            AIReport.report_date == today,
        )
        .first()
    )

    if existing_report:
        return AISuggestion(
            stock_id=existing_report.stock_id,
            name=stock.name,
            suggestion=existing_report.suggestion,
            confidence=float(existing_report.confidence),
            target_price=existing_report.target_price,
            stop_loss_price=existing_report.stop_loss_price,
            reasoning=existing_report.reasoning,
            key_factors=existing_report.key_factors,
            report_date=existing_report.report_date,
        )

    # Generate new suggestion
    suggestion_data = suggestion_service.generate_suggestion(stock.stock_id, stock.name)

    # Save to database
    report = AIReport(
        user_id=current_user.id,
        stock_id=stock.stock_id,
        report_date=today,
        suggestion=suggestion_data["suggestion"],
        confidence=suggestion_data["confidence"],
        target_price=suggestion_data.get("target_price"),
        stop_loss_price=suggestion_data.get("stop_loss_price"),
        reasoning=suggestion_data["reasoning"],
        key_factors=suggestion_data["key_factors"],
    )
    db.add(report)
    db.commit()

    return AISuggestion(**suggestion_data)


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 問答"""
    # Get chat history
    history = (
        db.query(AIChatHistory)
        .filter(AIChatHistory.user_id == current_user.id)
        .order_by(AIChatHistory.created_at.desc())
        .limit(10)
        .all()
    )
    history.reverse()

    chat_history = [{"role": msg.role, "content": msg.content} for msg in history]

    # Get AI response
    response_data = chat_service.chat(request.message, request.stock_id, chat_history)

    # Save to database
    user_msg = AIChatHistory(
        user_id=current_user.id,
        stock_id=request.stock_id,
        role="user",
        content=request.message,
    )
    assistant_msg = AIChatHistory(
        user_id=current_user.id,
        stock_id=request.stock_id,
        role="assistant",
        content=response_data["response"],
    )
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()

    return AIChatResponse(**response_data)


@router.get("/chat/history", response_model=List[ChatMessage])
def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得對話歷史"""
    history = (
        db.query(AIChatHistory)
        .filter(AIChatHistory.user_id == current_user.id)
        .order_by(AIChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    history.reverse()

    return [
        ChatMessage(
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat(),
        )
        for msg in history
    ]
