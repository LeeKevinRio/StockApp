"""
AI router - AI 建議與問答（支援台股與美股）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from app.database import get_db
from app.models import User, Watchlist, Stock, AIReport, AIChatHistory
from app.schemas import AISuggestion, AIChatRequest, AIChatResponse, ChatMessage
from app.services import AISuggestionService, AIChatService, StockDataService
from app.services.prediction_tracker import PredictionTracker
from app.services.trading_calendar import get_next_trading_date
from app.routers.auth import get_current_user

prediction_tracker = PredictionTracker()

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _get_next_trading_date_str() -> str:
    """計算下一個交易日日期（含跳過國定假日）"""
    return get_next_trading_date().isoformat()


def _inject_target_date(suggestion_obj):
    """在 next_day_prediction 中注入 target_date"""
    if hasattr(suggestion_obj, 'next_day_prediction') and suggestion_obj.next_day_prediction:
        pred = suggestion_obj.next_day_prediction
        if isinstance(pred, dict) and 'target_date' not in pred:
            pred['target_date'] = _get_next_trading_date_str()
    return suggestion_obj
stock_service = StockDataService()


@router.get("/suggestions", response_model=List[AISuggestion])
def get_ai_suggestions(
    generate_missing: bool = Query(False, description="是否自動生成缺少的建議（會較慢）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得 AI 每日建議（所有自選股，包含台股與美股）

    預設只返回已有的建議（快速），設定 generate_missing=true 才會生成新建議
    """
    # Get user's watchlist with stock info
    watchlist = (
        db.query(Watchlist, Stock)
        .join(Stock, Watchlist.stock_id == Stock.stock_id)
        .filter(Watchlist.user_id == current_user.id)
        .all()
    )

    results = []
    today = date.today()

    for wl, stock in watchlist:
        # Determine market region from stock data
        market = stock.market_region if stock.market_region else "TW"

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
            # Calculate bullish probability from existing report
            confidence = float(existing_report.confidence)
            suggestion = existing_report.suggestion
            bullish_prob = confidence if suggestion == "BUY" else (1 - confidence)

            # Handle key_factors format conversion (old format was list of strings)
            key_factors = existing_report.key_factors or []
            if key_factors and isinstance(key_factors[0], str):
                # Convert old format to new format
                key_factors = [{"category": "分析", "factor": f, "impact": "neutral"} for f in key_factors]

            results.append(
                AISuggestion(
                    stock_id=existing_report.stock_id,
                    name=stock.name,
                    suggestion=existing_report.suggestion,
                    confidence=confidence,
                    bullish_probability=bullish_prob,
                    target_price=existing_report.target_price,
                    stop_loss_price=existing_report.stop_loss_price,
                    reasoning=existing_report.reasoning,
                    key_factors=key_factors,
                    report_date=existing_report.report_date,
                )
            )
        elif generate_missing:
            # Only generate new suggestion if explicitly requested
            try:
                # Create service instance based on user's subscription tier
                suggestion_service = AISuggestionService.for_user(current_user)
                suggestion_data = suggestion_service.generate_suggestion(
                    stock.stock_id, stock.name, market=market
                )

                # Check again if report exists (race condition protection)
                existing = (
                    db.query(AIReport)
                    .filter(
                        AIReport.user_id == current_user.id,
                        AIReport.stock_id == stock.stock_id,
                        AIReport.report_date == today,
                    )
                    .first()
                )

                if not existing:
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
                        key_factors=suggestion_data.get("key_factors", []),
                    )
                    db.add(report)
                    db.commit()

                results.append(AISuggestion(**suggestion_data))
            except Exception as e:
                db.rollback()  # Important: rollback on error
                print(f"Error generating suggestion for {stock.stock_id}: {e}")
                continue

    return results


@router.get("/suggestions/{stock_id}", response_model=AISuggestion)
def get_stock_suggestion(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    refresh: bool = Query(False, description="Force refresh, ignore cache"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得單一股票 AI 建議

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
        refresh: 是否強制刷新（忽略快取）
    """
    try:
        # Get stock info based on market
        if market == "US":
            stock_info = stock_service.get_stock(db, stock_id, market="US")
            if not stock_info:
                raise HTTPException(status_code=404, detail="Stock not found")
            stock_name = stock_info.get("name", stock_id)
        else:
            stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
            if not stock:
                raise HTTPException(status_code=404, detail="Stock not found")
            stock_name = stock.name

        today = date.today()

        # Check if report already exists for today (unless refresh is requested)
        existing_report = None
        if not refresh:
            existing_report = (
                db.query(AIReport)
                .filter(
                    AIReport.user_id == current_user.id,
                    AIReport.stock_id == stock_id,
                    AIReport.report_date == today,
                )
                .first()
            )
        else:
            # Delete existing report if refresh is requested
            db.query(AIReport).filter(
                AIReport.user_id == current_user.id,
                AIReport.stock_id == stock_id,
                AIReport.report_date == today,
            ).delete()
            db.commit()

        if existing_report:
            # Calculate bullish probability from existing report
            confidence = float(existing_report.confidence)
            suggestion = existing_report.suggestion
            bullish_prob = confidence if suggestion == "BUY" else (1 - confidence) if suggestion == "SELL" else 0.5

            # Handle key_factors format conversion (old format was list of strings)
            key_factors = existing_report.key_factors or []
            if key_factors and isinstance(key_factors[0], str):
                key_factors = [{"category": "分析", "factor": f, "impact": "neutral"} for f in key_factors]

            # 注入 target_date 到 next_day_prediction
            next_pred = existing_report.next_day_prediction
            if next_pred and isinstance(next_pred, dict) and 'target_date' not in next_pred:
                next_pred = {**next_pred, 'target_date': _get_next_trading_date_str()}

            return AISuggestion(
                stock_id=existing_report.stock_id,
                name=stock_name,
                suggestion=existing_report.suggestion,
                confidence=confidence,
                bullish_probability=bullish_prob,
                target_price=existing_report.target_price,
                stop_loss_price=existing_report.stop_loss_price,
                reasoning=existing_report.reasoning,
                key_factors=key_factors,
                report_date=existing_report.report_date,
                entry_price_min=existing_report.entry_price_min,
                entry_price_max=existing_report.entry_price_max,
                take_profit_targets=existing_report.take_profit_targets,
                risk_level=existing_report.risk_level,
                time_horizon=existing_report.time_horizon,
                predicted_change_percent=existing_report.predicted_change_percent,
                next_day_prediction=next_pred,
            )

        # Generate new suggestion with market parameter
        # Create service instance based on user's subscription tier
        suggestion_service = AISuggestionService.for_user(current_user)
        suggestion_data = suggestion_service.generate_suggestion(stock_id, stock_name, market=market, db=db)

        # Save to database with error handling
        try:
            # Rollback any pending transaction first
            db.rollback()

            # Delete any existing report first (in case of race condition)
            db.query(AIReport).filter(
                AIReport.user_id == current_user.id,
                AIReport.stock_id == stock_id,
                AIReport.report_date == today,
            ).delete()

            report = AIReport(
                user_id=current_user.id,
                stock_id=stock_id,
                report_date=today,
                suggestion=suggestion_data["suggestion"],
                confidence=suggestion_data["confidence"],
                target_price=suggestion_data.get("target_price"),
                stop_loss_price=suggestion_data.get("stop_loss_price"),
                reasoning=suggestion_data["reasoning"],
                key_factors=suggestion_data.get("key_factors", []),
                entry_price_min=suggestion_data.get("entry_price_min"),
                entry_price_max=suggestion_data.get("entry_price_max"),
                take_profit_targets=suggestion_data.get("take_profit_targets"),
                risk_level=suggestion_data.get("risk_level"),
                time_horizon=suggestion_data.get("time_horizon"),
                predicted_change_percent=suggestion_data.get("predicted_change_percent"),
                next_day_prediction=suggestion_data.get("next_day_prediction"),
            )
            db.add(report)
            db.commit()
        except Exception as db_error:
            # Database save failed, but we still have the suggestion data
            db.rollback()
            print(f"Warning: Failed to save AI report to database: {db_error}")

        # 儲存預測記錄（用於準確度追蹤）
        try:
            next_day_pred = suggestion_data.get("next_day_prediction")
            if next_day_pred:
                # 獲取最新收盤價
                analysis_scores = suggestion_data.get("analysis_scores", {})
                latest_price = analysis_scores.get("latest_price", 0) or 0
                ai_provider = suggestion_data.get("ai_provider", "Unknown")

                prediction_tracker.save_prediction(
                    db=db,
                    stock_id=stock_id,
                    stock_name=stock_name,
                    market=market,
                    prediction_data=next_day_pred,
                    base_close_price=latest_price,
                    ai_provider=ai_provider
                )
                print(f"Saved prediction record for {stock_id}")
        except Exception as pred_error:
            print(f"Warning: Failed to save prediction record: {pred_error}")

        # Fix report_date format - convert string to date if needed
        if isinstance(suggestion_data.get("report_date"), str):
            suggestion_data["report_date"] = today

        # 注入 target_date 到 next_day_prediction
        next_pred = suggestion_data.get("next_day_prediction")
        if next_pred and isinstance(next_pred, dict) and 'target_date' not in next_pred:
            next_pred['target_date'] = _get_next_trading_date_str()

        return AISuggestion(**suggestion_data)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"AI Suggestion Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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

    # Create chat service based on user's subscription tier
    chat_service = AIChatService.for_user(current_user)

    try:
        # Get AI response
        response_data = chat_service.chat(request.message, request.stock_id, chat_history)
    except Exception as e:
        error_str = str(e)
        print(f"AI Chat Error: {error_str}")
        # Handle quota exceeded error
        if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
            raise HTTPException(
                status_code=429,
                detail="AI 服務配額已達上限，請稍後再試。(API quota exceeded, please try again later.)"
            )
        raise HTTPException(status_code=500, detail=f"AI 服務暫時不可用: {error_str}")

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
