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


def _validate_prices(data: dict, current_price: float) -> dict:
    """驗證並修正 AI 建議中偏離過大的價格欄位"""
    if not current_price or current_price <= 0:
        return data

    max_dev = 0.20  # 短線最多偏離 20%

    for key in ("target_price", "stop_loss_price", "entry_price_min", "entry_price_max"):
        val = data.get(key)
        if val is not None:
            try:
                val = float(val)
                if val <= 0 or abs(val - current_price) / current_price > max_dev:
                    pct = abs(float(data.get("predicted_change_percent", 3) or 3))
                    if key == "target_price":
                        data[key] = round(current_price * (1 + pct / 100), 2)
                    elif key == "stop_loss_price":
                        data[key] = round(current_price * (1 - pct / 100), 2)
                    elif key == "entry_price_min":
                        data[key] = round(current_price * 0.98, 2)
                    elif key == "entry_price_max":
                        data[key] = round(current_price * 1.02, 2)
            except (TypeError, ValueError):
                pass

    # 修正 take_profit_targets
    tpt = data.get("take_profit_targets")
    if isinstance(tpt, list):
        for i, item in enumerate(tpt):
            if isinstance(item, dict):
                p = item.get("price")
                if p is not None:
                    try:
                        p = float(p)
                        if p <= 0 or abs(p - current_price) / current_price > max_dev:
                            mult = 1.03 + i * 0.02
                            item["price"] = round(current_price * mult, 2)
                    except (TypeError, ValueError):
                        pass

    # 修正 next_day_prediction
    ndp = data.get("next_day_prediction")
    if isinstance(ndp, dict):
        pct = float(ndp.get("predicted_change_percent", 0) or 0)
        for pk in ("price_range_low", "price_range_high"):
            pv = ndp.get(pk)
            if pv is not None:
                try:
                    pv = float(pv)
                    if pv <= 0 or abs(pv - current_price) / current_price > max_dev:
                        offset = -0.015 if pk == "price_range_low" else 0.015
                        ndp[pk] = round(current_price * (1 + pct / 100 + offset), 2)
                except (TypeError, ValueError):
                    pass

    return data


def _get_next_trading_date_str(market: str = "TW") -> str:
    """計算下一個交易日日期（含跳過國定假日，支援台股/美股）"""
    return get_next_trading_date(market=market).isoformat()


def _inject_target_date(suggestion_obj, market: str = "TW"):
    """在 next_day_prediction 中注入 target_date"""
    if hasattr(suggestion_obj, 'next_day_prediction') and suggestion_obj.next_day_prediction:
        pred = suggestion_obj.next_day_prediction
        if isinstance(pred, dict) and 'target_date' not in pred:
            pred['target_date'] = _get_next_trading_date_str(market)
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

            # 從 DB 讀取時也做價格合理性驗證
            suggestion_dict = {
                "stock_id": existing_report.stock_id,
                "name": stock.name,
                "suggestion": existing_report.suggestion,
                "confidence": confidence,
                "bullish_probability": bullish_prob,
                "current_price": existing_report.current_price,
                "target_price": existing_report.target_price,
                "stop_loss_price": existing_report.stop_loss_price,
                "reasoning": existing_report.reasoning,
                "key_factors": key_factors,
                "report_date": existing_report.report_date,
            }
            cp = float(existing_report.current_price or 0)
            if cp > 0:
                suggestion_dict = _validate_prices(suggestion_dict, cp)
            results.append(AISuggestion(**suggestion_dict))
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
                        current_price=suggestion_data.get("current_price"),
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
                next_pred = {**next_pred, 'target_date': _get_next_trading_date_str(market)}

            # 從 DB 讀取時也做價格合理性驗證
            suggestion_dict = {
                "stock_id": existing_report.stock_id,
                "name": stock_name,
                "suggestion": existing_report.suggestion,
                "confidence": confidence,
                "bullish_probability": bullish_prob,
                "current_price": existing_report.current_price,
                "target_price": existing_report.target_price,
                "stop_loss_price": existing_report.stop_loss_price,
                "reasoning": existing_report.reasoning,
                "key_factors": key_factors,
                "report_date": existing_report.report_date,
                "entry_price_min": existing_report.entry_price_min,
                "entry_price_max": existing_report.entry_price_max,
                "take_profit_targets": existing_report.take_profit_targets,
                "risk_level": existing_report.risk_level,
                "time_horizon": existing_report.time_horizon,
                "predicted_change_percent": existing_report.predicted_change_percent,
                "next_day_prediction": next_pred,
            }
            cp = float(existing_report.current_price or 0)
            if cp > 0:
                suggestion_dict = _validate_prices(suggestion_dict, cp)
            return AISuggestion(**suggestion_dict)

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
                current_price=suggestion_data.get("current_price"),
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
            next_pred['target_date'] = _get_next_trading_date_str(market)

        return AISuggestion(**suggestion_data)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"AI Suggestion Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comprehensive-analysis/{stock_id}")
def get_comprehensive_analysis(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    綜合 AI 分析 — 6維度（技術/籌碼/基本面/新聞/社群/宏觀）
    回傳雷達圖數據 + 健康等級(A-F) + AI 摘要
    """
    try:
        suggestion_service = AISuggestionService.for_user(current_user)
        data = suggestion_service.collect_stock_data(stock_id, market=market)

        tech_score = data.get('technical', {}).get('technical_score', 0)
        chip_score = data.get('chip', {}).get('chip_score', 0)
        fund_score = data.get('fundamental', {}).get('fundamental_score', 0)
        news_score = data.get('news_sentiment', {}).get('sentiment_score', 0)
        social_score = data.get('social', {}).get('social_score', 0)
        macro_score = data.get('macro', {}).get('macro_score', 0)

        # 加權計算
        if market == "US":
            total_score = (tech_score * 0.35) + (fund_score * 0.25) + (news_score * 0.12) + (social_score * 0.08) + (macro_score * 0.20)
        else:
            total_score = (tech_score * 0.30) + (chip_score * 0.20) + (fund_score * 0.15) + (news_score * 0.10) + (social_score * 0.10) + (macro_score * 0.15)

        # 健康等級 A-F（total_score 範圍約 -100 ~ +100）
        # 多數正常股票加權後落在 -10 ~ +20，門檻需配合實際分佈
        if total_score >= 30:
            health_grade = 'A'
        elif total_score >= 15:
            health_grade = 'B'
        elif total_score >= 0:
            health_grade = 'C'
        elif total_score >= -15:
            health_grade = 'D'
        elif total_score >= -30:
            health_grade = 'E'
        else:
            health_grade = 'F'

        # 正規化分數到 0-100（雷達圖用）
        def normalize(score):
            return max(0, min(100, round((score + 100) / 2)))

        # 維度明細
        dimensions = {
            'technical': {
                'score': tech_score,
                'normalized': normalize(tech_score),
                'signal': data.get('technical', {}).get('technical_signal', 'N/A'),
                'weight': 0.30 if market == 'TW' else 0.35,
                'label': '技術面',
                'details': {
                    'rsi': data.get('technical', {}).get('rsi'),
                    'macd_status': data.get('technical', {}).get('macd_status'),
                    'ma_trend': data.get('technical', {}).get('ma_trend'),
                    'bb_position': data.get('technical', {}).get('bb_position'),
                },
            },
            'chip': {
                'score': chip_score if market == 'TW' else None,
                'normalized': normalize(chip_score) if market == 'TW' else None,
                'signal': data.get('chip', {}).get('chip_signal', 'N/A') if market == 'TW' else 'N/A',
                'weight': 0.20 if market == 'TW' else 0,
                'label': '籌碼面',
                'details': {
                    'foreign_trend': data.get('chip', {}).get('foreign_trend'),
                    'trust_trend': data.get('chip', {}).get('trust_trend'),
                    'margin_trend': data.get('chip', {}).get('margin_trend'),
                } if market == 'TW' else {},
            },
            'fundamental': {
                'score': fund_score,
                'normalized': normalize(fund_score),
                'signal': data.get('fundamental', {}).get('fundamental_signal', 'N/A'),
                'weight': 0.15 if market == 'TW' else 0.25,
                'label': '基本面',
                'details': {
                    'per': data.get('fundamental', {}).get('per'),
                    'eps': data.get('fundamental', {}).get('eps'),
                    'roe': data.get('fundamental', {}).get('roe'),
                    'dividend_yield': data.get('fundamental', {}).get('dividend_yield'),
                },
            },
            'news': {
                'score': news_score,
                'normalized': normalize(news_score),
                'signal': data.get('news_sentiment', {}).get('sentiment_signal', 'N/A'),
                'weight': 0.10 if market == 'TW' else 0.12,
                'label': '新聞面',
                'details': {
                    'news_count': data.get('news_sentiment', {}).get('news_count', 0),
                    'positive_news': data.get('news_sentiment', {}).get('positive_news', 0),
                    'negative_news': data.get('news_sentiment', {}).get('negative_news', 0),
                },
            },
            'social': {
                'score': social_score,
                'normalized': normalize(social_score),
                'signal': data.get('social', {}).get('social_signal', 'N/A'),
                'weight': 0.10 if market == 'TW' else 0.08,
                'label': '社群面',
                'details': {
                    'total_mentions': data.get('social', {}).get('total_mentions', 0),
                    'positive': data.get('social', {}).get('positive', 0),
                    'negative': data.get('social', {}).get('negative', 0),
                    'platforms': data.get('social', {}).get('platforms', []),
                },
            },
            'macro': {
                'score': macro_score,
                'normalized': normalize(macro_score),
                'signal': data.get('macro', {}).get('macro_signal', 'N/A'),
                'weight': 0.15 if market == 'TW' else 0.20,
                'label': '總經面',
                'details': data.get('macro', {}).get('details', {}),
            },
        }

        # 雷達圖數據（正規化 0-100）
        if market == 'TW':
            radar_labels = ['技術面', '籌碼面', '基本面', '新聞面', '社群面', '總經面']
            radar_values = [
                normalize(tech_score), normalize(chip_score), normalize(fund_score),
                normalize(news_score), normalize(social_score), normalize(macro_score),
            ]
        else:
            radar_labels = ['技術面', '基本面', '新聞面', '社群面', '總經面']
            radar_values = [
                normalize(tech_score), normalize(fund_score),
                normalize(news_score), normalize(social_score), normalize(macro_score),
            ]

        # AI 摘要（更詳細的文字描述）
        summary_parts = []

        # 技術面
        tech_detail = data.get('technical', {})
        rsi_val = tech_detail.get('rsi')
        macd_st = tech_detail.get('macd_status', '')
        if tech_score > 20:
            summary_parts.append(f'技術面偏多（RSI {round(rsi_val, 1) if rsi_val else "N/A"}，MACD {"翻多" if macd_st == "bullish" else "翻空" if macd_st == "bearish" else "中性"}）')
        elif tech_score < -20:
            summary_parts.append(f'技術面偏空（RSI {round(rsi_val, 1) if rsi_val else "N/A"}，MACD {"翻空" if macd_st == "bearish" else "中性"}）')
        else:
            summary_parts.append(f'技術面中性（RSI {round(rsi_val, 1) if rsi_val else "N/A"}）')

        # 籌碼面（台股）
        if market == 'TW':
            chip_detail = data.get('chip', {})
            foreign_5d = chip_detail.get('foreign_net_5d', 0)
            if chip_score > 20:
                summary_parts.append(f'法人買超（外資近5日淨買 {foreign_5d} 張）')
            elif chip_score < -20:
                summary_parts.append(f'法人賣超（外資近5日淨賣 {abs(foreign_5d)} 張）')

        # 基本面
        fund_detail = data.get('fundamental', {})
        per_val = fund_detail.get('per')
        if fund_score > 20:
            summary_parts.append(f'基本面良好' + (f'（PER {per_val}）' if per_val else ''))
        elif fund_score < -20:
            summary_parts.append(f'基本面疲弱' + (f'（PER {per_val}）' if per_val else ''))

        # 社群
        if social_score > 15:
            summary_parts.append('社群看好')
        elif social_score < -15:
            summary_parts.append('社群看空')

        # 宏觀面
        macro_detail = data.get('macro', {}).get('details', {})
        vix_val = macro_detail.get('vix', {}).get('value')
        if macro_score > 15:
            summary_parts.append(f'總經面利多' + (f'（VIX {vix_val}）' if vix_val else ''))
        elif macro_score < -15:
            summary_parts.append(f'總經面利空' + (f'（VIX {vix_val}）' if vix_val else ''))

        # 總結
        grade_desc = {'A': '體質強健', 'B': '表現不錯', 'C': '中性偏穩', 'D': '略顯疲弱', 'E': '警訊浮現', 'F': '風險偏高'}
        ai_summary = '；'.join(summary_parts) + f'。\n綜合評分 {round(total_score, 1)} 分，健康等級 {health_grade}（{grade_desc.get(health_grade, "")}）。'

        # 股票基本資訊
        stock_name = stock_id
        if market == 'TW':
            stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
            if stock:
                stock_name = stock.name
        else:
            stock_info = stock_service.get_stock(db, stock_id, market="US")
            if stock_info:
                stock_name = stock_info.get("name", stock_id)

        return {
            'stock_id': stock_id,
            'stock_name': stock_name,
            'market': market,
            'total_score': round(total_score, 1),
            'health_grade': health_grade,
            'dimensions': dimensions,
            'radar': {
                'labels': radar_labels,
                'values': radar_values,
            },
            'ai_summary': ai_summary,
            'latest_price': data.get('latest_price', 0),
            'price_change_5d': data.get('price_change_5d', 0),
            'price_change_20d': data.get('price_change_20d', 0),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"綜合分析失敗: {str(e)}")


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
