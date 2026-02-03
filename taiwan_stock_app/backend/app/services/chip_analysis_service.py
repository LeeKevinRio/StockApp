"""
Chip Analysis Service
專業級高風險交易分析平台 - 籌碼深度分析服務

分析內容：
- 法人買賣超動向（外資、投信、自營商）
- 籌碼集中度變化
- 融資融券使用率
- 主力進出指標
- 籌碼動能評分
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date, timedelta
import pandas as pd
import numpy as np

from app.data_fetchers import FinMindFetcher
from app.config import settings


@dataclass
class InstitutionalFlow:
    """法人買賣超數據"""
    date: str
    foreign_buy: int  # 外資買超（張）
    foreign_sell: int  # 外資賣超（張）
    foreign_net: int  # 外資淨買賣
    trust_buy: int  # 投信買超
    trust_sell: int  # 投信賣超
    trust_net: int  # 投信淨買賣
    dealer_buy: int  # 自營商買超
    dealer_sell: int  # 自營商賣超
    dealer_net: int  # 自營商淨買賣
    total_net: int  # 三大法人合計淨買賣


@dataclass
class MarginData:
    """融資融券數據"""
    date: str
    margin_balance: int  # 融資餘額（張）
    margin_change: int  # 融資增減
    margin_utilization: float  # 融資使用率 (%)
    short_balance: int  # 融券餘額
    short_change: int  # 融券增減
    short_ratio: float  # 券資比 (%)


@dataclass
class ChipConcentration:
    """籌碼集中度"""
    top_holders_ratio: float  # 前十大持股比例
    foreign_ratio: float  # 外資持股比例
    trust_ratio: float  # 投信持股比例
    retail_ratio: float  # 散戶持股比例（估算）
    concentration_score: float  # 集中度分數 (0-100)
    concentration_trend: str  # 集中趨勢 (increasing/decreasing/stable)


class ChipAnalysisService:
    """籌碼深度分析服務"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)

    def get_institutional_flows(
        self,
        stock_id: str,
        days: int = 20
    ) -> List[InstitutionalFlow]:
        """
        取得法人買賣超資料

        Args:
            stock_id: 股票代碼
            days: 天數

        Returns:
            法人買賣超數據列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 10)  # 多取幾天確保有足夠交易日

        data = self.finmind.get_institutional_investors(
            stock_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        if len(data) == 0:
            return []

        flows = []
        grouped = data.groupby('date')

        for date_str, group in grouped:
            flow = InstitutionalFlow(
                date=str(date_str),
                foreign_buy=0,
                foreign_sell=0,
                foreign_net=0,
                trust_buy=0,
                trust_sell=0,
                trust_net=0,
                dealer_buy=0,
                dealer_sell=0,
                dealer_net=0,
                total_net=0,
            )

            for _, row in group.iterrows():
                name = str(row.get('name', ''))
                buy = int(row.get('buy', 0))
                sell = int(row.get('sell', 0))
                net = buy - sell

                if 'Foreign' in name or '外資' in name:
                    flow.foreign_buy += buy
                    flow.foreign_sell += sell
                    flow.foreign_net += net
                elif 'Investment' in name or '投信' in name:
                    flow.trust_buy += buy
                    flow.trust_sell += sell
                    flow.trust_net += net
                elif 'Dealer' in name or '自營' in name:
                    flow.dealer_buy += buy
                    flow.dealer_sell += sell
                    flow.dealer_net += net

            # 轉為張數（原數據通常是股數）
            flow.foreign_buy //= 1000
            flow.foreign_sell //= 1000
            flow.foreign_net //= 1000
            flow.trust_buy //= 1000
            flow.trust_sell //= 1000
            flow.trust_net //= 1000
            flow.dealer_buy //= 1000
            flow.dealer_sell //= 1000
            flow.dealer_net //= 1000
            flow.total_net = flow.foreign_net + flow.trust_net + flow.dealer_net

            flows.append(flow)

        # 排序並限制數量
        flows.sort(key=lambda x: x.date, reverse=True)
        return flows[:days]

    def get_margin_data(
        self,
        stock_id: str,
        days: int = 20
    ) -> List[MarginData]:
        """
        取得融資融券資料

        Args:
            stock_id: 股票代碼
            days: 天數

        Returns:
            融資融券數據列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days + 10)

        data = self.finmind.get_margin_trading(
            stock_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        if len(data) == 0:
            return []

        margins = []
        prev_margin = None
        prev_short = None

        for _, row in data.iterrows():
            margin_balance = int(row.get('MarginPurchaseBalance', 0))
            short_balance = int(row.get('ShortSaleBalance', 0))
            margin_limit = int(row.get('MarginPurchaseLimit', 0))

            margin_change = margin_balance - prev_margin if prev_margin else 0
            short_change = short_balance - prev_short if prev_short else 0

            # 計算使用率
            utilization = (margin_balance / margin_limit * 100) if margin_limit > 0 else 0
            short_ratio = (short_balance / margin_balance * 100) if margin_balance > 0 else 0

            margins.append(MarginData(
                date=str(row.get('date', '')),
                margin_balance=margin_balance,
                margin_change=margin_change,
                margin_utilization=round(utilization, 2),
                short_balance=short_balance,
                short_change=short_change,
                short_ratio=round(short_ratio, 2),
            ))

            prev_margin = margin_balance
            prev_short = short_balance

        margins.sort(key=lambda x: x.date, reverse=True)
        return margins[:days]

    def calculate_chip_momentum(
        self,
        institutional_flows: List[InstitutionalFlow],
        margin_data: List[MarginData]
    ) -> Dict:
        """
        計算籌碼動能指標

        Returns:
            籌碼動能分析結果
        """
        result = {
            "momentum_score": 50,
            "momentum_direction": "neutral",
            "foreign_momentum": 0,
            "trust_momentum": 0,
            "margin_momentum": 0,
            "signals": [],
            "recommendation": "觀望",
        }

        if not institutional_flows:
            return result

        # 外資動能分析
        foreign_5d = sum(f.foreign_net for f in institutional_flows[:5])
        foreign_10d = sum(f.foreign_net for f in institutional_flows[:10])
        foreign_20d = sum(f.foreign_net for f in institutional_flows[:20]) if len(institutional_flows) >= 20 else foreign_10d

        # 投信動能分析
        trust_5d = sum(f.trust_net for f in institutional_flows[:5])
        trust_10d = sum(f.trust_net for f in institutional_flows[:10])

        # 計算連續買超/賣超天數
        foreign_streak = self._calculate_streak([f.foreign_net for f in institutional_flows])
        trust_streak = self._calculate_streak([f.trust_net for f in institutional_flows])

        # 外資動能分數 (-50 到 +50)
        foreign_momentum = 0
        if foreign_5d > 0 and foreign_10d > 0:
            foreign_momentum = min(30, foreign_5d / 100)  # 買超量轉換為分數
        elif foreign_5d < 0 and foreign_10d < 0:
            foreign_momentum = max(-30, foreign_5d / 100)

        # 連續天數加分
        if foreign_streak > 0:
            foreign_momentum += min(20, foreign_streak * 3)
        else:
            foreign_momentum -= min(20, abs(foreign_streak) * 3)

        result["foreign_momentum"] = round(foreign_momentum)

        # 投信動能分數 (-30 到 +30)
        trust_momentum = 0
        if trust_5d > 0:
            trust_momentum = min(20, trust_5d / 50)
        elif trust_5d < 0:
            trust_momentum = max(-20, trust_5d / 50)

        if trust_streak > 0:
            trust_momentum += min(10, trust_streak * 2)
        else:
            trust_momentum -= min(10, abs(trust_streak) * 2)

        result["trust_momentum"] = round(trust_momentum)

        # 融資動能分析
        margin_momentum = 0
        if margin_data:
            margin_5d_change = sum(m.margin_change for m in margin_data[:5])
            latest_utilization = margin_data[0].margin_utilization if margin_data else 0

            # 融資增加過多是負面信號（散戶追高）
            if margin_5d_change > 1000:
                margin_momentum = -15
                result["signals"].append("融資大增，散戶追高")
            elif margin_5d_change < -1000:
                margin_momentum = 10
                result["signals"].append("融資減少，籌碼沉澱")

            # 使用率過高是負面信號
            if latest_utilization > 70:
                margin_momentum -= 10
                result["signals"].append(f"融資使用率偏高 ({latest_utilization:.1f}%)")

        result["margin_momentum"] = round(margin_momentum)

        # 計算總動能分數 (0-100)
        total_momentum = 50 + foreign_momentum + trust_momentum + margin_momentum
        total_momentum = max(0, min(100, total_momentum))
        result["momentum_score"] = round(total_momentum)

        # 判斷方向
        if total_momentum >= 65:
            result["momentum_direction"] = "bullish"
            result["recommendation"] = "籌碼面偏多，可考慮順勢操作"
        elif total_momentum <= 35:
            result["momentum_direction"] = "bearish"
            result["recommendation"] = "籌碼面偏空，建議保守觀望"
        else:
            result["momentum_direction"] = "neutral"
            result["recommendation"] = "籌碼面中性，等待明確信號"

        # 添加具體信號
        if foreign_streak >= 3:
            result["signals"].append(f"外資連續買超 {foreign_streak} 天")
        elif foreign_streak <= -3:
            result["signals"].append(f"外資連續賣超 {abs(foreign_streak)} 天")

        if trust_streak >= 3:
            result["signals"].append(f"投信連續買超 {trust_streak} 天")
        elif trust_streak <= -3:
            result["signals"].append(f"投信連續賣超 {abs(trust_streak)} 天")

        if foreign_5d > 0 and trust_5d > 0:
            result["signals"].append("外資投信同步買超")
        elif foreign_5d < 0 and trust_5d < 0:
            result["signals"].append("外資投信同步賣超")

        return result

    def _calculate_streak(self, values: List[int]) -> int:
        """計算連續正負天數"""
        if not values:
            return 0

        streak = 0
        first_sign = 1 if values[0] > 0 else (-1 if values[0] < 0 else 0)

        if first_sign == 0:
            return 0

        for v in values:
            current_sign = 1 if v > 0 else (-1 if v < 0 else 0)
            if current_sign == first_sign:
                streak += 1
            else:
                break

        return streak if first_sign > 0 else -streak

    def get_comprehensive_chip_analysis(
        self,
        stock_id: str,
        days: int = 20
    ) -> Dict:
        """
        取得完整籌碼分析

        Args:
            stock_id: 股票代碼
            days: 分析天數

        Returns:
            完整籌碼分析結果
        """
        # 取得各類數據
        flows = self.get_institutional_flows(stock_id, days)
        margins = self.get_margin_data(stock_id, days)
        momentum = self.calculate_chip_momentum(flows, margins)

        # 彙總統計
        summary = {
            "stock_id": stock_id,
            "analysis_days": days,
        }

        # 法人統計
        if flows:
            summary["institutional"] = {
                "foreign_5d_net": sum(f.foreign_net for f in flows[:5]),
                "foreign_10d_net": sum(f.foreign_net for f in flows[:10]),
                "foreign_20d_net": sum(f.foreign_net for f in flows[:min(20, len(flows))]),
                "trust_5d_net": sum(f.trust_net for f in flows[:5]),
                "trust_10d_net": sum(f.trust_net for f in flows[:10]),
                "dealer_5d_net": sum(f.dealer_net for f in flows[:5]),
                "total_5d_net": sum(f.total_net for f in flows[:5]),
                "total_10d_net": sum(f.total_net for f in flows[:10]),
            }

            # 轉換為 dict 列表以便 JSON 序列化
            summary["daily_flows"] = [
                {
                    "date": f.date,
                    "foreign_net": f.foreign_net,
                    "trust_net": f.trust_net,
                    "dealer_net": f.dealer_net,
                    "total_net": f.total_net,
                }
                for f in flows[:10]
            ]

        # 融資融券統計
        if margins:
            latest = margins[0]
            summary["margin"] = {
                "current_balance": latest.margin_balance,
                "current_utilization": latest.margin_utilization,
                "short_balance": latest.short_balance,
                "short_ratio": latest.short_ratio,
                "margin_5d_change": sum(m.margin_change for m in margins[:5]),
                "margin_trend": "increasing" if sum(m.margin_change for m in margins[:5]) > 0 else "decreasing",
            }

            summary["daily_margin"] = [
                {
                    "date": m.date,
                    "margin_balance": m.margin_balance,
                    "margin_change": m.margin_change,
                    "short_balance": m.short_balance,
                }
                for m in margins[:10]
            ]

        # 動能分析
        summary["momentum"] = momentum

        # 綜合建議
        summary["overall"] = self._generate_overall_recommendation(summary)

        return summary

    def _generate_overall_recommendation(self, analysis: Dict) -> Dict:
        """生成綜合籌碼建議"""
        momentum = analysis.get("momentum", {})
        institutional = analysis.get("institutional", {})
        margin = analysis.get("margin", {})

        score = momentum.get("momentum_score", 50)
        direction = momentum.get("momentum_direction", "neutral")

        strengths = []
        weaknesses = []
        warnings = []

        # 分析優勢
        if institutional:
            foreign_5d = institutional.get("foreign_5d_net", 0)
            trust_5d = institutional.get("trust_5d_net", 0)

            if foreign_5d > 500:
                strengths.append(f"外資近5日大幅買超 {foreign_5d} 張")
            if trust_5d > 200:
                strengths.append(f"投信近5日買超 {trust_5d} 張")
            if foreign_5d > 0 and trust_5d > 0:
                strengths.append("外資投信同步看多")

            if foreign_5d < -500:
                weaknesses.append(f"外資近5日大幅賣超 {abs(foreign_5d)} 張")
            if trust_5d < -200:
                weaknesses.append(f"投信近5日賣超 {abs(trust_5d)} 張")

        # 融資融券警示
        if margin:
            utilization = margin.get("current_utilization", 0)
            margin_change = margin.get("margin_5d_change", 0)

            if utilization > 70:
                warnings.append(f"融資使用率偏高 ({utilization:.1f}%)，籌碼較為鬆散")
            if margin_change > 2000:
                warnings.append("近期融資大幅增加，散戶追價明顯")

        # 生成建議文字
        if direction == "bullish":
            suggestion = "籌碼面呈現多頭格局"
            if strengths:
                suggestion += f"，主要優勢：{', '.join(strengths[:2])}"
        elif direction == "bearish":
            suggestion = "籌碼面呈現空頭格局"
            if weaknesses:
                suggestion += f"，主要弱勢：{', '.join(weaknesses[:2])}"
        else:
            suggestion = "籌碼面呈現觀望格局，等待法人明確表態"

        return {
            "score": score,
            "direction": direction,
            "direction_cn": "多頭" if direction == "bullish" else "空頭" if direction == "bearish" else "觀望",
            "suggestion": suggestion,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "warnings": warnings,
        }
