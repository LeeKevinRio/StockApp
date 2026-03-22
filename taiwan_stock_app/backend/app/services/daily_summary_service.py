"""
Daily Summary Service — 每日盤前摘要郵件服務
每天早上 8:00 台灣時間自動發送盤前總結郵件

功能：
1. 美股收盤回顧 (S&P 500, Nasdaq, Dow, VIX)
2. 國際新聞重點 (Top 5)
3. 台灣市場相關新聞 (Top 5)
4. 宏觀指標變化 (Fed利率、公債殖利率、美元/台幣)
5. 社群情緒概況 (PTT/Threads 看多看空比例)
6. 今日重點事件 (財報、經濟數據公布)
7. AI 監控清單預警 (強信號股票)
8. HTML 郵件模板 (行動裝置友善、色彩分類情緒)
"""

import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from html import escape

logger = logging.getLogger(__name__)


class DailySummaryService:
    """每日盤前摘要服務"""

    def __init__(self):
        """初始化服務，讀取 SMTP 配置"""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        # 保留環境變數作為備用，但主要從用戶 DB 取得 email
        self.to_emails = self._parse_to_emails(os.getenv("TO_EMAIL", ""))

        # 延遲導入以避免循環依賴
        self._enhanced_news_fetcher = None
        self._fred_fetcher = None
        self._us_stock_fetcher = None
        self._enhanced_analyzer = None

    def _parse_to_emails(self, to_email_str: str) -> List[str]:
        """解析逗號分隔的郵件地址"""
        if not to_email_str:
            return []
        return [email.strip() for email in to_email_str.split(",") if email.strip()]

    def _get_subscribed_emails(self) -> List[str]:
        """
        從資料庫取得所有已訂閱盤前摘要的用戶 Email（Google 登入帳號）
        如果 DB 不可用，退回使用環境變數設定
        """
        try:
            from app.database import SessionLocal
            from app.models.user import User
            db = SessionLocal()
            try:
                # 取得所有啟用盤前摘要的用戶 email
                users = db.query(User).filter(
                    User.email.isnot(None),
                    User.daily_summary_enabled == True
                ).all()
                emails = [u.email for u in users if u.email]
                if emails:
                    return emails
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"無法從 DB 取得訂閱用戶，退回環境變數: {e}")

        # 退回使用環境變數
        return self.to_emails

    async def _get_us_market_summary(self) -> Dict:
        """
        取得美股收盤回顧
        包括：S&P 500, Nasdaq, Dow, VIX
        """
        try:
            from app.data_fetchers.us_stock_fetcher import USStockFetcher

            if not self._us_stock_fetcher:
                self._us_stock_fetcher = USStockFetcher()

            fetcher = self._us_stock_fetcher

            # 抓取主要指數
            indices = {
                "^GSPC": "S&P 500",
                "^IXIC": "Nasdaq",
                "^DJI": "道瓊指數 (Dow)",
                "^VIX": "波動率指數 (VIX)"
            }

            summary = {
                "timestamp": datetime.now().isoformat(),
                "indices": []
            }

            for symbol, name in indices.items():
                try:
                    data = fetcher.get_quote(symbol)
                    if data:
                        summary["indices"].append({
                            "symbol": symbol,
                            "name": name,
                            "price": data.get("price"),
                            "change": data.get("change"),
                            "change_percent": data.get("change_percent"),
                            "previous_close": data.get("previous_close")
                        })
                except Exception as e:
                    logger.warning(f"無法取得 {name} 數據: {e}")
                    continue

            return summary

        except Exception as e:
            logger.error(f"取得美股摘要失敗: {e}")
            return {"error": str(e), "indices": []}

    async def _get_international_news(self, limit: int = 5) -> List[Dict]:
        """取得國際新聞 Top N"""
        try:
            from app.data_fetchers.enhanced_news_fetcher import EnhancedNewsFetcher

            if not self._enhanced_news_fetcher:
                self._enhanced_news_fetcher = EnhancedNewsFetcher()

            fetcher = self._enhanced_news_fetcher
            news_list = await fetcher.fetch_international_news(limit=limit * 2)

            # 排序並取前 N 筆
            sorted_news = sorted(
                news_list,
                key=lambda x: x.get("published_at", ""),
                reverse=True
            )[:limit]

            return sorted_news

        except Exception as e:
            logger.error(f"取得國際新聞失敗: {e}")
            return []

    async def _get_taiwan_news(self, limit: int = 5) -> List[Dict]:
        """取得台灣市場相關新聞 Top N"""
        try:
            from app.data_fetchers.enhanced_news_fetcher import EnhancedNewsFetcher

            if not self._enhanced_news_fetcher:
                self._enhanced_news_fetcher = EnhancedNewsFetcher()

            fetcher = self._enhanced_news_fetcher
            news_list = await fetcher.fetch_market_overview_news(market="TW", limit=limit * 2)

            # 排序並取前 N 筆
            sorted_news = sorted(
                news_list,
                key=lambda x: x.get("published_at", ""),
                reverse=True
            )[:limit]

            return sorted_news

        except Exception as e:
            logger.error(f"取得台灣新聞失敗: {e}")
            return []

    async def _get_macro_indicators(self) -> Dict:
        """取得宏觀指標變化"""
        try:
            from app.data_fetchers.fred_fetcher import FREDFetcher
            from app.data_fetchers.us_stock_fetcher import USStockFetcher

            if not self._fred_fetcher:
                self._fred_fetcher = FREDFetcher(
                    api_key=os.getenv("FRED_API_KEY", "")
                )

            if not self._us_stock_fetcher:
                self._us_stock_fetcher = USStockFetcher()

            indicators = {}

            # 從 FRED 取得利率與殖利率
            try:
                fed_rate = self._fred_fetcher.get_latest_value("fed_rate")
                if fed_rate:
                    indicators["fed_rate"] = {
                        "name": "聯邦基金利率",
                        "value": fed_rate.get("value"),
                        "date": fed_rate.get("date"),
                        "previous_value": fed_rate.get("previous_value")
                    }
            except Exception as e:
                logger.warning(f"無法取得 Fed 利率: {e}")

            try:
                us10y = self._fred_fetcher.get_latest_value("us10y_yield")
                if us10y:
                    indicators["us10y_yield"] = {
                        "name": "10年期公債殖利率",
                        "value": us10y.get("value"),
                        "date": us10y.get("date"),
                        "previous_value": us10y.get("previous_value")
                    }
            except Exception as e:
                logger.warning(f"無法取得 10年殖利率: {e}")

            # 從 yfinance 取得美元/台幣匯率
            try:
                usd_twd = self._us_stock_fetcher.get_quote("USDTWD=X")
                if usd_twd:
                    indicators["usd_twd"] = {
                        "name": "美元/台幣匯率",
                        "price": usd_twd.get("price"),
                        "change": usd_twd.get("change"),
                        "change_percent": usd_twd.get("change_percent")
                    }
            except Exception as e:
                logger.warning(f"無法取得美元/台幣匯率: {e}")

            return indicators

        except Exception as e:
            logger.error(f"取得宏觀指標失敗: {e}")
            return {}

    async def _get_social_sentiment(self) -> Dict:
        """
        取得社群情緒概況
        來自 PTT、Threads 等平台的看多/看空比例
        """
        try:
            from app.services.enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer

            if not self._enhanced_analyzer:
                self._enhanced_analyzer = EnhancedSentimentAnalyzer()

            # 簡化版：返回統計數據
            # 實際應該從 PTT/Threads fetcher 獲取文章並分析
            sentiment_data = {
                "bullish_count": 0,
                "bearish_count": 0,
                "bullish_ratio": 0.0,
                "bearish_ratio": 0.0,
                "avg_sentiment": 0.0,
                "data_sources": ["PTT", "Threads"]
            }

            try:
                # 嘗試從社群平台抓取數據
                from app.data_fetchers.taiwan_social_fetcher import TaiwanSocialFetcher
                from app.data_fetchers.threads_fetcher import ThreadsFetcher

                tw_fetcher = TaiwanSocialFetcher()

                # 抓取 PTT 文章
                ptt_posts = tw_fetcher.get_posts_by_keyword("股票", limit=20)

                bullish = 0
                bearish = 0
                total_score = 0.0

                for post in ptt_posts:
                    score, _ = self._enhanced_analyzer.analyze(post.get("content", ""))
                    total_score += score
                    if score > 0.3:
                        bullish += 1
                    elif score < -0.3:
                        bearish += 1

                total = bullish + bearish
                if total > 0:
                    sentiment_data["bullish_count"] = bullish
                    sentiment_data["bearish_count"] = bearish
                    sentiment_data["bullish_ratio"] = bullish / total
                    sentiment_data["bearish_ratio"] = bearish / total
                    sentiment_data["avg_sentiment"] = total_score / len(ptt_posts)

            except Exception as e:
                logger.warning(f"社群數據收集失敗: {e}")

            return sentiment_data

        except Exception as e:
            logger.error(f"取得社群情緒失敗: {e}")
            return {
                "bullish_count": 0,
                "bearish_count": 0,
                "bullish_ratio": 0.0,
                "bearish_ratio": 0.0,
                "avg_sentiment": 0.0
            }

    async def _get_key_events(self) -> List[Dict]:
        """
        取得今日重點事件
        包括：財報發布、經濟數據公布、央行會議等
        """
        try:
            from app.services.calendar_service import CalendarService

            calendar_service = CalendarService()
            today = datetime.now().date()

            events = calendar_service.get_events_by_date(today)

            # 篩選重要事件（高影響力）
            important_events = [
                e for e in events
                if e.get("importance", "low") in ["medium", "high"]
            ][:5]

            return important_events

        except Exception as e:
            logger.warning(f"取得日曆事件失敗: {e}")
            return []

    async def _get_ai_watchlist_alerts(self) -> List[Dict]:
        """
        取得 AI 監控清單中的強信號股票
        """
        try:
            # 簡化版：返回空列表或模擬數據
            # 實際應該從 AI 建議服務或預測追蹤器獲取
            alerts = []

            try:
                from app.services.prediction_tracker import PredictionTracker

                tracker = PredictionTracker()
                today = datetime.now().date()

                # 取得今日高信心預測
                predictions = tracker.get_predictions_for_date(today)

                strong_signals = [
                    p for p in predictions
                    if p.get("confidence", 0) > 0.75
                ][:5]

                alerts = strong_signals

            except Exception as e:
                logger.warning(f"無法取得預測信號: {e}")

            return alerts

        except Exception as e:
            logger.warning(f"取得 AI 監控警報失敗: {e}")
            return []

    def _build_html_email(self, summary_data: Dict) -> str:
        """
        構建 HTML 郵件模板
        專業、行動裝置友善的設計
        """

        # 顏色定義
        color_positive = "#10b981"  # 綠色 (看多)
        color_negative = "#ef4444"  # 紅色 (看空)
        color_neutral = "#6b7280"   # 灰色 (中立)
        color_header = "#1f2937"    # 深灰 (標題)
        color_bg = "#f9fafb"        # 淺灰背景

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日盤前摘要 - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft JhengHei', 'PingFang TC', sans-serif;
            background-color: {color_bg};
            margin: 0;
            padding: 0;
            color: #374151;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .header p {{
            margin: 8px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .section {{
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section h2 {{
            margin: 0 0 16px 0;
            font-size: 18px;
            font-weight: 600;
            color: {color_header};
            padding-bottom: 8px;
            border-bottom: 2px solid #667eea;
        }}
        .market-card {{
            background: {color_bg};
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 4px solid #667eea;
        }}
        .market-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            font-size: 14px;
        }}
        .market-name {{
            font-weight: 500;
            color: {color_header};
            flex: 1;
        }}
        .market-value {{
            font-weight: 600;
            margin: 0 12px;
            min-width: 80px;
            text-align: right;
        }}
        .market-change {{
            font-weight: 600;
            min-width: 70px;
            text-align: right;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .positive {{
            color: {color_positive};
            background-color: rgba(16, 185, 129, 0.1);
        }}
        .negative {{
            color: {color_negative};
            background-color: rgba(239, 68, 68, 0.1);
        }}
        .neutral {{
            color: {color_neutral};
            background-color: rgba(107, 114, 128, 0.1);
        }}
        .news-item {{
            background: {color_bg};
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 3px solid #e5e7eb;
        }}
        .news-title {{
            font-weight: 600;
            color: {color_header};
            margin: 0 0 4px 0;
            font-size: 14px;
        }}
        .news-time {{
            font-size: 12px;
            color: {color_neutral};
            margin: 0;
        }}
        .sentiment-gauge {{
            display: flex;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            background: {color_bg};
            margin: 12px 0;
        }}
        .sentiment-bullish {{
            background: {color_positive};
            height: 100%;
            flex: 0;
        }}
        .sentiment-bearish {{
            background: {color_negative};
            height: 100%;
            flex: 0;
        }}
        .footer {{
            padding: 20px;
            background: {color_header};
            color: white;
            text-align: center;
            font-size: 12px;
            line-height: 1.6;
        }}
        .footer p {{
            margin: 4px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            margin: 12px 0;
        }}
        th {{
            background: {color_bg};
            padding: 8px;
            text-align: left;
            font-weight: 600;
            color: {color_header};
            border-bottom: 2px solid #e5e7eb;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .event-item {{
            background: {color_bg};
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 10px;
            font-size: 13px;
        }}
        .event-time {{
            color: {color_neutral};
            font-weight: 500;
            margin-bottom: 4px;
        }}
        .event-title {{
            color: {color_header};
            font-weight: 600;
        }}
        .event-importance {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-top: 4px;
        }}
        .importance-high {{
            background: rgba(239, 68, 68, 0.2);
            color: {color_negative};
        }}
        .importance-medium {{
            background: rgba(251, 191, 36, 0.2);
            color: #b45309;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📈 每日盤前摘要</h1>
            <p>{datetime.now().strftime('%Y 年 %m 月 %d 日')}</p>
        </div>

        <!-- US Market Summary -->
        <div class="section">
            <h2>🇺🇸 美股收盤回顧</h2>
"""

        # 美股指數
        if summary_data.get("us_market"):
            market_data = summary_data["us_market"]
            if not market_data.get("error"):
                for index in market_data.get("indices", []):
                    price = index.get("price", "N/A")
                    change = index.get("change", 0)
                    change_pct = index.get("change_percent", 0)
                    change_class = "positive" if change >= 0 else "negative"
                    change_sign = "+" if change >= 0 else ""

                    html += f"""
            <div class="market-card">
                <div class="market-row">
                    <div class="market-name">{escape(index.get('name', 'N/A'))}</div>
                    <div class="market-value">{price}</div>
                    <div class="market-change {change_class}">
                        {change_sign}{change:.2f} ({change_sign}{change_pct:.2f}%)
                    </div>
                </div>
            </div>
"""

        # International News
        html += f"""
        </div>
        <div class="section">
            <h2>🌍 國際新聞重點 (Top 5)</h2>
"""

        if summary_data.get("international_news"):
            for i, news in enumerate(summary_data["international_news"][:5], 1):
                title = escape(news.get("title", "無標題"))
                time_str = news.get("published_at", "")
                if time_str:
                    try:
                        time_obj = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                        time_display = time_obj.strftime("%m/%d %H:%M")
                    except:
                        time_display = time_str[:10]
                else:
                    time_display = "時間未知"

                html += f"""
            <div class="news-item">
                <div class="news-title">{i}. {title}</div>
                <div class="news-time">📅 {time_display}</div>
            </div>
"""

        # Taiwan News
        html += f"""
        </div>
        <div class="section">
            <h2>🇹🇼 台灣市場新聞 (Top 5)</h2>
"""

        if summary_data.get("taiwan_news"):
            for i, news in enumerate(summary_data["taiwan_news"][:5], 1):
                title = escape(news.get("title", "無標題"))
                time_str = news.get("published_at", "")
                if time_str:
                    try:
                        time_obj = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                        time_display = time_obj.strftime("%m/%d %H:%M")
                    except:
                        time_display = time_str[:10]
                else:
                    time_display = "時間未知"

                html += f"""
            <div class="news-item">
                <div class="news-title">{i}. {title}</div>
                <div class="news-time">📅 {time_display}</div>
            </div>
"""

        # Macro Indicators
        html += f"""
        </div>
        <div class="section">
            <h2>📊 宏觀指標變化</h2>
            <table>
                <tr>
                    <th>指標</th>
                    <th>最新數值</th>
                    <th>變化</th>
                </tr>
"""

        if summary_data.get("macro_indicators"):
            indicators = summary_data["macro_indicators"]
            for key, indicator in indicators.items():
                if not indicator:
                    continue
                name = indicator.get("name", key)
                value = indicator.get("value") or indicator.get("price", "N/A")
                prev = indicator.get("previous_value")
                change = indicator.get("change", 0)
                change_class = "positive" if change >= 0 else "negative"
                change_sign = "+" if change >= 0 else ""

                change_text = "N/A"
                if change:
                    change_text = f"{change_sign}{change:.4f}"

                html += f"""
                <tr>
                    <td><strong>{escape(name)}</strong></td>
                    <td>{value}</td>
                    <td class="{change_class}">{change_text}</td>
                </tr>
"""

        html += """
            </table>
        </div>
"""

        # Social Sentiment
        sentiment_data = summary_data.get("social_sentiment", {})
        bullish_ratio = sentiment_data.get("bullish_ratio", 0)
        bearish_ratio = sentiment_data.get("bearish_ratio", 0)

        html += f"""
        <div class="section">
            <h2>💬 社群情緒概況</h2>
            <div style="margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: {color_positive}; font-weight: 600;">看多 {sentiment_data.get('bullish_count', 0)} 篇</span>
                    <span style="color: {color_negative}; font-weight: 600;">看空 {sentiment_data.get('bearish_count', 0)} 篇</span>
                </div>
                <div class="sentiment-gauge">
                    <div class="sentiment-bullish" style="flex: {bullish_ratio or 0}"></div>
                    <div class="sentiment-bearish" style="flex: {bearish_ratio or 0}"></div>
                </div>
                <div style="font-size: 12px; color: {color_neutral}; margin-top: 8px;">
                    平均情緒值: <span style="font-weight: 600;">{sentiment_data.get('avg_sentiment', 0):.2f}</span>
                    (範圍: -1.0 ~ +1.0)
                </div>
            </div>
        </div>
"""

        # Key Events
        html += f"""
        <div class="section">
            <h2>📅 今日重點事件</h2>
"""

        if summary_data.get("key_events"):
            for event in summary_data["key_events"][:5]:
                title = escape(event.get("title", "無標題"))
                time_str = event.get("time", "")
                importance = event.get("importance", "low").lower()
                importance_class = f"importance-{importance}"
                importance_text = {"high": "高", "medium": "中", "low": "低"}.get(importance, "低")

                html += f"""
            <div class="event-item">
                <div class="event-time">🕐 {time_str}</div>
                <div class="event-title">{title}</div>
                <div class="event-importance {importance_class}">影響力: {importance_text}</div>
            </div>
"""

        # AI Watchlist Alerts
        html += f"""
        </div>
        <div class="section">
            <h2>🤖 AI 監控清單預警</h2>
"""

        if summary_data.get("ai_alerts"):
            for i, alert in enumerate(summary_data["ai_alerts"][:5], 1):
                stock = escape(alert.get("stock_id", "N/A"))
                signal = escape(alert.get("signal", "未知"))
                confidence = alert.get("confidence", 0)
                confidence_class = "positive" if confidence > 0.75 else "neutral"

                html += f"""
            <div class="news-item" style="border-left-color: #667eea;">
                <div class="news-title">{i}. {stock} - {signal}</div>
                <div class="news-time">信心度: <span style="font-weight: 600; color: {color_positive};">{confidence:.1%}</span></div>
            </div>
"""
        else:
            html += """
            <div class="news-item">
                <p style="margin: 0; color: #6b7280; font-size: 13px;">暫無強信號預警</p>
            </div>
"""

        # Footer
        html += f"""
        </div>
        <div class="footer">
            <p><strong>📌 重要免責聲明</strong></p>
            <p>投資有風險，本內容僅供參考，不構成投資建議。</p>
            <p>過去表現不代表未來結果。請在投資前進行充分調查與評估。</p>
            <p style="margin-top: 12px; font-size: 11px;">
                此郵件由自動化服務生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)
            </p>
        </div>
    </div>
</body>
</html>
"""

        return html

    async def send_email(self, summary_data: Dict) -> bool:
        """
        發送郵件

        Args:
            summary_data: 摘要數據字典

        Returns:
            是否發送成功
        """

        if not self.smtp_user or not self.smtp_password or not self.from_email or not self.to_emails:
            logger.error("SMTP 配置不完整，無法發送郵件")
            return False

        try:
            # 構建 HTML 郵件
            html_content = self._build_html_email(summary_data)

            # 建立郵件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📈 每日盤前摘要 - {datetime.now().strftime('%Y-%m-%d')}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)

            # 附加 HTML 部分
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # 發送郵件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, self.to_emails, msg.as_string())

            logger.info(f"每日摘要郵件已發送至 {', '.join(self.to_emails)}")
            return True

        except Exception as e:
            logger.error(f"發送郵件失敗: {e}")
            return False

    async def generate_summary(self) -> Dict:
        """
        生成完整的日常摘要數據

        Returns:
            摘要數據字典
        """

        logger.info("開始生成每日摘要...")

        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "us_market": {},
            "international_news": [],
            "taiwan_news": [],
            "macro_indicators": {},
            "social_sentiment": {},
            "key_events": [],
            "ai_alerts": []
        }

        # 並發抓取所有數據
        try:
            results = await asyncio.gather(
                self._get_us_market_summary(),
                self._get_international_news(),
                self._get_taiwan_news(),
                self._get_macro_indicators(),
                self._get_social_sentiment(),
                self._get_key_events(),
                self._get_ai_watchlist_alerts(),
                return_exceptions=True
            )

            summary_data["us_market"] = results[0] if not isinstance(results[0], Exception) else {}
            summary_data["international_news"] = results[1] if not isinstance(results[1], Exception) else []
            summary_data["taiwan_news"] = results[2] if not isinstance(results[2], Exception) else []
            summary_data["macro_indicators"] = results[3] if not isinstance(results[3], Exception) else {}
            summary_data["social_sentiment"] = results[4] if not isinstance(results[4], Exception) else {}
            summary_data["key_events"] = results[5] if not isinstance(results[5], Exception) else []
            summary_data["ai_alerts"] = results[6] if not isinstance(results[6], Exception) else []

            logger.info("每日摘要數據生成完成")

        except Exception as e:
            logger.error(f"生成摘要時發生錯誤: {e}")

        return summary_data

    async def send_to_user(self, user_email: str, summary_data: Optional[Dict] = None) -> bool:
        """
        發送盤前摘要到指定用戶的 Google 登入 Email

        Args:
            user_email: 用戶的 Google 登入 email
            summary_data: 摘要數據，若為 None 則自動生成

        Returns:
            是否發送成功
        """
        if not summary_data:
            summary_data = await self.generate_summary()

        # 暫時替換收件人
        original = self.to_emails
        self.to_emails = [user_email]
        try:
            return await self.send_email(summary_data)
        finally:
            self.to_emails = original

    async def schedule_daily_summary(self) -> bool:
        """
        每日摘要定時任務
        應由 APScheduler 在每天 8:00 AM 台灣時間調用
        自動從 DB 取得所有訂閱用戶的 Google Email 並逐一發送

        Returns:
            是否執行成功
        """

        logger.info("執行每日盤前摘要任務...")

        try:
            # 生成摘要數據（只需生成一次）
            summary_data = await self.generate_summary()

            # 從 DB 取得訂閱用戶 email（即 Google 登入帳號）
            subscribed_emails = self._get_subscribed_emails()

            if not subscribed_emails:
                logger.warning("沒有訂閱盤前摘要的用戶")
                return False

            # 逐一發送（未來可改為批次）
            success_count = 0
            for email in subscribed_emails:
                try:
                    sent = await self.send_to_user(email, summary_data)
                    if sent:
                        success_count += 1
                except Exception as e:
                    logger.error(f"發送至 {email} 失敗: {e}")

            logger.info(f"每日摘要完成：{success_count}/{len(subscribed_emails)} 封發送成功")
            return success_count > 0

        except Exception as e:
            logger.error(f"每日摘要任務執行失敗: {e}")
            return False

    async def send_test_email(self, to_email: Optional[str] = None) -> bool:
        """
        發送測試郵件

        Args:
            to_email: 接收者郵件，如未提供則使用配置的默認值

        Returns:
            是否發送成功
        """

        test_data = {
            "timestamp": datetime.now().isoformat(),
            "us_market": {
                "indices": [
                    {
                        "symbol": "^GSPC",
                        "name": "S&P 500",
                        "price": 5341.20,
                        "change": 35.80,
                        "change_percent": 0.68
                    },
                    {
                        "symbol": "^IXIC",
                        "name": "Nasdaq",
                        "price": 16875.35,
                        "change": 125.45,
                        "change_percent": 0.75
                    }
                ]
            },
            "international_news": [
                {
                    "title": "美聯儲議息結果：維持利率不變",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "title": "Apple 發布新款 iPhone 15 Pro",
                    "published_at": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ],
            "taiwan_news": [
                {
                    "title": "台積電第三季度營收創新高",
                    "published_at": datetime.now().isoformat()
                }
            ],
            "macro_indicators": {
                "fed_rate": {
                    "name": "聯邦基金利率",
                    "value": 5.50,
                    "change": 0.0
                },
                "us10y_yield": {
                    "name": "10年期公債殖利率",
                    "value": 4.15,
                    "change": 0.02
                }
            },
            "social_sentiment": {
                "bullish_count": 12,
                "bearish_count": 8,
                "bullish_ratio": 0.6,
                "bearish_ratio": 0.4,
                "avg_sentiment": 0.15
            },
            "key_events": [
                {
                    "title": "美國首次申請失業救濟數據",
                    "time": "20:30",
                    "importance": "high"
                }
            ],
            "ai_alerts": [
                {
                    "stock_id": "AAPL",
                    "signal": "黃金交叉突破",
                    "confidence": 0.85
                }
            ]
        }

        # 臨時修改 to_email
        original_to_emails = self.to_emails
        if to_email:
            self.to_emails = [to_email]

        try:
            success = await self.send_email(test_data)
            return success
        finally:
            self.to_emails = original_to_emails


# 全局實例
daily_summary_service = DailySummaryService()
