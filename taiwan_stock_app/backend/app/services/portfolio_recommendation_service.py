"""
Portfolio Recommendation Service
投資組合推薦服務 - AI 驅動的投資組合建議和分析

功能：
- 風險偏好自動檢測
- AI 驅動的股票推薦
- 投資組合再平衡提醒
- 預設模型投資組合
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import json
from sqlalchemy.orm import Session

from app.models import Portfolio, Position, Stock
from app.services.stock_data_service import StockDataService
from app.services.ai_client_factory import AIClientFactory

logger = logging.getLogger(__name__)


# ==================== 風險偏好配置 ====================
RISK_PROFILES = {
    "保守型": {
        "label": "Conservative",
        "allocation": {
            "bonds_etf": 0.60,      # 債券/ETF 60%
            "blue_chip": 0.30,      # 藍籌股 30%
            "growth": 0.10,         # 成長股 10%
        },
        "expected_return": "3-6%",
        "max_drawdown": "-10%",
    },
    "穩健型": {
        "label": "Moderate",
        "allocation": {
            "blue_chip": 0.40,      # 藍籌股 40%
            "growth": 0.30,         # 成長股 30%
            "etf": 0.20,            # ETF 20%
            "high_risk": 0.10,      # 高風險 10%
        },
        "expected_return": "7-12%",
        "max_drawdown": "-20%",
    },
    "積極型": {
        "label": "Aggressive",
        "allocation": {
            "growth_momentum": 0.50, # 成長/動量股 50%
            "high_risk_small_cap": 0.30,  # 高風險/小型股 30%
            "speculative": 0.20,    # 投機股 20%
        },
        "expected_return": "15-30%",
        "max_drawdown": "-40%",
    },
}


# ==================== 模型投資組合 ====================
MODEL_PORTFOLIOS = {
    "台灣市場": {
        "高股息組合": {
            "description": "專注於高股息發放的藍籌股和金融股",
            "stocks": [
                {"symbol": "1101", "name": "台泥", "allocation": 0.15},
                {"symbol": "2882", "name": "國泰金", "allocation": 0.15},
                {"symbol": "3008", "name": "大立光", "allocation": 0.10},
                {"symbol": "0056", "name": "元大高息", "allocation": 0.20},
                {"symbol": "00878", "name": "國泰永續高股息", "allocation": 0.20},
                {"symbol": "1304", "name": "寶齡富錦", "allocation": 0.10},
                {"symbol": "2409", "name": "友達", "allocation": 0.10},
            ],
            "risk_level": "保守型",
        },
        "AI概念股組合": {
            "description": "聚焦於人工智慧、晶片和電子相關產業的成長機會",
            "stocks": [
                {"symbol": "2330", "name": "台積電", "allocation": 0.20},
                {"symbol": "2454", "name": "聯發科", "allocation": 0.15},
                {"symbol": "3034", "name": "聯詠", "allocation": 0.12},
                {"symbol": "3231", "name": "緯創", "allocation": 0.10},
                {"symbol": "2388", "name": "威盛", "allocation": 0.08},
                {"symbol": "6239", "name": "力特", "allocation": 0.10},
                {"symbol": "6415", "name": "矽力-KY", "allocation": 0.10},
                {"symbol": "3008", "name": "大立光", "allocation": 0.15},
            ],
            "risk_level": "積極型",
        },
        "金融龍頭組合": {
            "description": "投資於台灣主要金融機構的穩定配息組合",
            "stocks": [
                {"symbol": "2882", "name": "國泰金", "allocation": 0.25},
                {"symbol": "2884", "name": "玉山金", "allocation": 0.20},
                {"symbol": "2890", "name": "永豐金", "allocation": 0.15},
                {"symbol": "2891", "name": "中信金", "allocation": 0.15},
                {"symbol": "1102", "name": "亞泥", "allocation": 0.10},
                {"symbol": "5880", "name": "華南金", "allocation": 0.15},
            ],
            "risk_level": "穩健型",
        },
        "ETF懶人組合": {
            "description": "簡單易懂的 ETF 組合，適合長期投資",
            "stocks": [
                {"symbol": "0050", "name": "元大台灣50", "allocation": 0.40},
                {"symbol": "0056", "name": "元大高息", "allocation": 0.30},
                {"symbol": "00878", "name": "國泰永續高股息", "allocation": 0.15},
                {"symbol": "0055", "name": "元大MSCI台灣", "allocation": 0.15},
            ],
            "risk_level": "保守型",
        },
    },
    "美國市場": {
        "FAANG+組合": {
            "description": "科技巨頭和成長股組合",
            "stocks": [
                {"symbol": "AAPL", "name": "Apple", "allocation": 0.15},
                {"symbol": "MSFT", "name": "Microsoft", "allocation": 0.15},
                {"symbol": "GOOGL", "name": "Google", "allocation": 0.12},
                {"symbol": "AMZN", "name": "Amazon", "allocation": 0.12},
                {"symbol": "META", "name": "Meta", "allocation": 0.10},
                {"symbol": "NVDA", "name": "Nvidia", "allocation": 0.15},
                {"symbol": "TSLA", "name": "Tesla", "allocation": 0.10},
                {"symbol": "SPY", "name": "SPY ETF", "allocation": 0.11},
            ],
            "risk_level": "積極型",
        },
        "半導體組合": {
            "description": "聚焦於半導體和晶片製造產業",
            "stocks": [
                {"symbol": "NVDA", "name": "Nvidia", "allocation": 0.20},
                {"symbol": "AMD", "name": "AMD", "allocation": 0.15},
                {"symbol": "QCOM", "name": "Qualcomm", "allocation": 0.12},
                {"symbol": "INTC", "name": "Intel", "allocation": 0.12},
                {"symbol": "TSM", "name": "TSMC ADR", "allocation": 0.15},
                {"symbol": "ASML", "name": "ASML", "allocation": 0.12},
                {"symbol": "SMH", "name": "Semiconductor ETF", "allocation": 0.14},
            ],
            "risk_level": "積極型",
        },
        "價值型組合": {
            "description": "低本益比的價值投資組合",
            "stocks": [
                {"symbol": "JPM", "name": "JPMorgan", "allocation": 0.12},
                {"symbol": "XOM", "name": "Exxon", "allocation": 0.10},
                {"symbol": "KO", "name": "Coca-Cola", "allocation": 0.10},
                {"symbol": "JNJ", "name": "Johnson & Johnson", "allocation": 0.12},
                {"symbol": "PG", "name": "Procter & Gamble", "allocation": 0.10},
                {"symbol": "WMT", "name": "Walmart", "allocation": 0.10},
                {"symbol": "VTV", "name": "Value ETF", "allocation": 0.18},
                {"symbol": "GE", "name": "General Electric", "allocation": 0.08},
            ],
            "risk_level": "保守型",
        },
        "成長型組合": {
            "description": "高成長潛力的科技和創新企業",
            "stocks": [
                {"symbol": "NVDA", "name": "Nvidia", "allocation": 0.12},
                {"symbol": "GOOGL", "name": "Google", "allocation": 0.11},
                {"symbol": "MSFT", "name": "Microsoft", "allocation": 0.11},
                {"symbol": "CRM", "name": "Salesforce", "allocation": 0.08},
                {"symbol": "SHOP", "name": "Shopify", "allocation": 0.08},
                {"symbol": "SNPS", "name": "Synopsys", "allocation": 0.08},
                {"symbol": "ARKK", "name": "Innovation ETF", "allocation": 0.20},
                {"symbol": "QQQ", "name": "QQQ Nasdaq", "allocation": 0.12},
            ],
            "risk_level": "積極型",
        },
    },
}


class PortfolioRecommendationService:
    """投資組合推薦服務"""

    def __init__(self):
        """初始化服務"""
        self.stock_service = StockDataService()
        logger.info("PortfolioRecommendationService 已初始化")

    # ==================== 風險偏好檢測 ====================

    def detect_risk_profile(self, positions: List[Position], db: Optional[Session] = None) -> str:
        """
        根據現有持倉自動檢測用戶的風險偏好

        分析指標：
        - 股票波動率（Beta，僅美股可取得；台股 fallback 為 1.0）
        - 產業集中度
        - 平均市值（僅美股能精準取得）

        Args:
            positions: 持倉列表
            db: Optional DB session（取得台股 industry 用）

        Returns:
            風險偏好級別: 保守型, 穩健型, 積極型
        """
        if not positions:
            return "穩健型"  # 預設值

        try:
            # 計算各項指標
            total_volatility = 0
            industry_concentration = {}
            total_market_cap = 0
            position_count = len(positions)

            for position in positions:
                try:
                    # 推測市場：純英文 → 美股，否則 → 台股（與專案其他處同樣的 heuristic）
                    sid = position.stock_id or ""
                    market = "US" if sid.isalpha() else "TW"
                    base = self.stock_service.get_stock(db, sid, market=market) if db else None
                    fundamentals = None
                    if market == "US":
                        try:
                            fundamentals = self.stock_service.us_fetcher.get_fundamentals(sid)
                        except Exception as fe:
                            logger.debug("get_fundamentals 失敗 %s: %s", sid, fe)

                    # Beta：美股 fundamentals 提供，台股暫無公開來源 → 1.0
                    beta_val = (fundamentals or {}).get("beta")
                    beta = float(beta_val) if beta_val is not None else 1.0
                    total_volatility += beta

                    # 產業集中度
                    industry = ((base or {}).get("industry")
                                or (fundamentals or {}).get("industry")
                                or "其他")
                    industry_concentration[industry] = industry_concentration.get(industry, 0) + 1

                    # 市值統計（僅美股有）
                    market_cap_val = (fundamentals or {}).get("market_cap") or 0
                    total_market_cap += float(market_cap_val or 0)
                except Exception as e:
                    logger.warning(f"無法取得股票 {position.stock_id} 的資料: {e}")
                    continue

            # 計算平均指標
            avg_beta = total_volatility / position_count if position_count > 0 else 1.0
            avg_market_cap = total_market_cap / position_count if position_count > 0 else 0

            # 計算產業集中度（最大產業的比例）
            max_industry_concentration = (
                max(industry_concentration.values()) / position_count
                if industry_concentration else 0
            )

            # 根據指標判斷風險偏好
            # Beta > 1.2 且集中度高 -> 積極型
            # Beta < 0.8 或集中度低 -> 保守型
            # 其他 -> 穩健型

            if avg_beta > 1.2 or max_industry_concentration > 0.4:
                return "積極型"
            elif avg_beta < 0.8 or max_industry_concentration < 0.2:
                return "保守型"
            else:
                return "穩健型"

        except Exception as e:
            logger.error(f"風險偏好檢測失敗: {e}")
            return "穩健型"

    # ==================== 投資組合推薦 ====================

    def generate_recommendation(
        self,
        risk_level: str,
        market: str = "台灣市場",
        budget: float = 100000,
        db: Optional[Session] = None
    ) -> Dict:
        """
        使用 AI 生成投資組合推薦

        Args:
            risk_level: 風險級別 (保守型/穩健型/積極型)
            market: 市場 (台灣市場/美國市場)
            budget: 預算金額
            db: 資料庫 Session

        Returns:
            推薦數據包含：
            - suggested_stocks: 推薦股票及配置比例
            - expected_return: 預期報酬率
            - risk_metrics: 風險指標
            - rebalancing_suggestions: 再平衡建議
        """
        try:
            # 驗證風險級別
            if risk_level not in RISK_PROFILES:
                return {
                    "success": False,
                    "error": f"無效的風險級別: {risk_level}"
                }

            profile = RISK_PROFILES[risk_level]

            # 使用 AI 生成推薦
            ai_config = AIClientFactory.get_system_config()
            ai_client = AIClientFactory.create_client(ai_config)

            if not ai_client:
                return {
                    "success": False,
                    "error": "無法初始化 AI 客戶端"
                }

            # 構建 AI 提示詞
            prompt = f"""
你是一位專業的投資組合經理。根據以下條件生成投資組合推薦。

風險偏好: {risk_level} ({profile['label']})
目標配置: {json.dumps(profile['allocation'], ensure_ascii=False, indent=2)}
預算: {budget} 元
市場: {market}
預期報酬率: {profile['expected_return']}
最大回撤: {profile['max_drawdown']}

請以 JSON 格式回覆，包含以下結構：
{{
    "recommended_stocks": [
        {{
            "symbol": "股票代碼",
            "name": "股票名稱",
            "allocation_percentage": 配置比例(0-100),
            "entry_price": 建議進場價,
            "stop_loss": 停損價,
            "rationale": "推薦理由"
        }}
    ],
    "portfolio_summary": {{
        "total_allocation": 100,
        "diversification_score": 評分(1-10),
        "risk_score": 風險評分(1-10),
        "expected_annual_return": "預期年報酬率"
    }},
    "rebalancing_tips": ["再平衡建議1", "再平衡建議2"]
}}
"""

            result = ai_client.generate_json(prompt, temperature=0.5)

            if not result:
                return {
                    "success": False,
                    "error": "AI 生成推薦失敗"
                }

            return {
                "success": True,
                "risk_level": risk_level,
                "market": market,
                "budget": budget,
                "allocation_targets": profile["allocation"],
                "expected_return": profile["expected_return"],
                "max_drawdown": profile["max_drawdown"],
                "recommendation": result,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"生成推薦失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== 再平衡提醒 ====================

    def check_rebalance_needed(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int,
        tolerance: float = 0.05
    ) -> Dict:
        """
        檢查投資組合是否需要再平衡

        超過目標配置 ±5% 時發出警告

        Args:
            db: 資料庫 Session
            portfolio_id: 投資組合 ID
            user_id: 用戶 ID
            tolerance: 容許偏差比例 (預設 5%)

        Returns:
            再平衡檢查報告
        """
        try:
            from app.services.portfolio_service import PortfolioService

            portfolio_service = PortfolioService()
            portfolio = portfolio_service.get_portfolio(db, portfolio_id, user_id)

            if not portfolio:
                return {
                    "success": False,
                    "error": "投資組合不存在"
                }

            # 獲取持倉和配置
            positions = portfolio_service.get_positions(db, portfolio_id, user_id)
            allocations = portfolio_service.get_position_allocation(db, portfolio_id, user_id)

            if not allocations:
                return {
                    "success": True,
                    "rebalance_needed": False,
                    "message": "投資組合為空"
                }

            # 檢測當前風險偏好
            risk_level = self.detect_risk_profile(positions, db=db)
            profile = RISK_PROFILES.get(risk_level, RISK_PROFILES["穩健型"])
            target_allocation = profile["allocation"]

            # 分析偏差
            deviations = []
            rebalancing_trades = []

            for allocation in allocations:
                stock_id = allocation["stock_id"]
                current_weight = allocation["weight"] / 100  # 轉換為比例

                # 嘗試匹配目標配置
                target_weight = None
                for alloc_type, weight in target_allocation.items():
                    # 簡單的類型匹配（實務應更複雜）
                    if self._match_stock_type(stock_id, alloc_type):
                        target_weight = weight
                        break

                if target_weight is None:
                    target_weight = sum(target_allocation.values()) / len(target_allocation)

                # 計算偏差
                deviation = abs(current_weight - target_weight)

                if deviation > tolerance:
                    deviations.append({
                        "stock_id": stock_id,
                        "stock_name": allocation["stock_name"],
                        "current_weight": round(current_weight * 100, 2),
                        "target_weight": round(target_weight * 100, 2),
                        "deviation": round(deviation * 100, 2),
                        "action": "增加持有" if current_weight < target_weight else "減少持有"
                    })

                    # 生成交易建議
                    market_value = allocation["market_value"]
                    target_value = market_value * (target_weight / current_weight)
                    trade_amount = target_value - market_value

                    rebalancing_trades.append({
                        "stock_id": stock_id,
                        "stock_name": allocation["stock_name"],
                        "trade_amount": round(trade_amount, 2),
                        "trade_direction": "買入" if trade_amount > 0 else "賣出"
                    })

            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "current_risk_level": risk_level,
                "rebalance_needed": len(deviations) > 0,
                "deviation_count": len(deviations),
                "deviations": deviations,
                "rebalancing_trades": rebalancing_trades,
                "tolerance": tolerance * 100,
                "checked_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"檢查再平衡失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _match_stock_type(self, stock_id: str, alloc_type: str) -> bool:
        """
        簡單的股票類型匹配邏輯

        Args:
            stock_id: 股票代碼
            alloc_type: 配置類型

        Returns:
            是否匹配
        """
        # 這是簡化版本，實務應從股票基本資料查詢
        etf_symbols = ["0050", "0056", "00878", "0055", "SMH", "VTV", "ARKK", "QQQ", "SPY"]

        if alloc_type in ["etf", "bonds_etf"] and stock_id in etf_symbols:
            return True

        return False

    # ==================== 預設模型投資組合 ====================

    def get_model_portfolios(self, market: str = "台灣市場") -> Dict:
        """
        取得預設的模型投資組合

        Args:
            market: 市場 (台灣市場/美國市場)

        Returns:
            模型投資組合列表
        """
        try:
            if market not in MODEL_PORTFOLIOS:
                return {
                    "success": False,
                    "error": f"不支援的市場: {market}"
                }

            portfolios = MODEL_PORTFOLIOS[market]

            return {
                "success": True,
                "market": market,
                "model_portfolios": {
                    name: {
                        "name": name,
                        "description": portfolio["description"],
                        "risk_level": portfolio["risk_level"],
                        "stocks": portfolio["stocks"],
                        "stock_count": len(portfolio["stocks"]),
                        "total_allocation": sum(s["allocation"] for s in portfolio["stocks"]),
                    }
                    for name, portfolio in portfolios.items()
                }
            }

        except Exception as e:
            logger.error(f"取得模型投資組合失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_portfolio_detail(
        self,
        market: str = "台灣市場",
        portfolio_name: str = ""
    ) -> Dict:
        """
        取得特定模型投資組合的詳細資訊

        Args:
            market: 市場
            portfolio_name: 投資組合名稱

        Returns:
            詳細資訊
        """
        try:
            if market not in MODEL_PORTFOLIOS:
                return {
                    "success": False,
                    "error": f"不支援的市場: {market}"
                }

            if portfolio_name not in MODEL_PORTFOLIOS[market]:
                return {
                    "success": False,
                    "error": f"找不到投資組合: {portfolio_name}"
                }

            portfolio = MODEL_PORTFOLIOS[market][portfolio_name]

            return {
                "success": True,
                "market": market,
                "portfolio_name": portfolio_name,
                "description": portfolio["description"],
                "risk_level": portfolio["risk_level"],
                "stocks": portfolio["stocks"],
                "total_allocation": sum(s["allocation"] for s in portfolio["stocks"]),
            }

        except Exception as e:
            logger.error(f"取得模型投資組合詳細資訊失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== 輔助方法 ====================

    def get_risk_profiles(self) -> Dict:
        """
        取得所有可用的風險偏好配置

        Returns:
            風險偏好配置列表
        """
        return {
            "success": True,
            "risk_profiles": {
                name: {
                    "name": name,
                    "label": profile["label"],
                    "allocation": profile["allocation"],
                    "expected_return": profile["expected_return"],
                    "max_drawdown": profile["max_drawdown"],
                }
                for name, profile in RISK_PROFILES.items()
            }
        }

    def calculate_portfolio_metrics(
        self,
        positions: List[Position]
    ) -> Dict:
        """
        計算投資組合的風險指標

        Args:
            positions: 持倉列表

        Returns:
            風險指標
        """
        try:
            if not positions:
                return {
                    "success": True,
                    "error": "投資組合為空",
                }

            # 計算基本指標
            total_value = sum(p.current_price * p.quantity for p in positions)

            # 波動率（簡化版本）
            volatilities = []
            for position in positions:
                # 這裡應該使用歷史數據計算
                beta = 1.0  # 預設值
                volatilities.append(beta)

            avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 1.0

            return {
                "success": True,
                "position_count": len(positions),
                "total_value": round(total_value, 2),
                "average_volatility": round(avg_volatility, 2),
                "diversification_score": min(10, len(positions)),  # 簡化計算
            }

        except Exception as e:
            logger.error(f"計算投資組合指標失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局實例
portfolio_recommendation_service = PortfolioRecommendationService()
