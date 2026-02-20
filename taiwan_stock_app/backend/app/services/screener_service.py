"""
Stock Screener Service - 股票篩選服務
Filter stocks based on fundamental criteria
"""
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.models import Stock
from app.models.fundamental import StockFundamental, StockDividend

logger = logging.getLogger(__name__)


class ScreenerService:
    """股票篩選服務"""

    # Preset screen configurations
    PRESET_SCREENS = {
        "high_dividend": {
            "name": "高殖利率",
            "name_en": "High Dividend Yield",
            "description": "殖利率 > 5%",
            "criteria": {"dividend_yield_min": 5.0}
        },
        "low_pe": {
            "name": "低本益比",
            "name_en": "Low P/E Ratio",
            "description": "本益比 < 15",
            "criteria": {"pe_max": 15.0}
        },
        "high_roe": {
            "name": "高ROE",
            "name_en": "High ROE",
            "description": "ROE > 15%",
            "criteria": {"roe_min": 15.0}
        },
        "value_stocks": {
            "name": "價值股",
            "name_en": "Value Stocks",
            "description": "P/E < 12, P/B < 1.5, 殖利率 > 3%",
            "criteria": {"pe_max": 12.0, "pb_max": 1.5, "dividend_yield_min": 3.0}
        },
        "growth_stocks": {
            "name": "成長股",
            "name_en": "Growth Stocks",
            "description": "ROE > 20%, 營收成長 > 10%",
            "criteria": {"roe_min": 20.0, "revenue_growth_min": 10.0}
        },
        "blue_chip": {
            "name": "藍籌股",
            "name_en": "Blue Chip",
            "description": "市值 > 500億, ROE > 10%",
            "criteria": {"market_cap_min": 50000000000, "roe_min": 10.0}
        },
    }

    async def screen_stocks(
        self,
        db: Session,
        criteria: Dict,
        market: str = "TW",
        limit: int = 50
    ) -> List[Dict]:
        """
        依條件篩選股票

        Args:
            db: Database session
            criteria: Screening criteria dict with keys like:
                - pe_min, pe_max: P/E ratio range
                - pb_min, pb_max: P/B ratio range
                - dividend_yield_min: Minimum dividend yield (%)
                - roe_min: Minimum ROE (%)
                - roa_min: Minimum ROA (%)
                - revenue_growth_min: Minimum revenue growth (%)
                - gross_margin_min: Minimum gross margin (%)
                - market_cap_min, market_cap_max: Market cap range
                - industry: Industry filter
            market: 'TW' or 'US'
            limit: Maximum results

        Returns:
            List of matching stocks with fundamental data
        """
        try:
            # Build query
            query = db.query(Stock, StockFundamental).outerjoin(
                StockFundamental,
                Stock.stock_id == StockFundamental.stock_id
            ).filter(Stock.market_region == market)

            # Apply filters
            filters = []

            # P/E ratio filter
            if criteria.get("pe_min") is not None:
                filters.append(StockFundamental.pe_ratio >= criteria["pe_min"])
            if criteria.get("pe_max") is not None:
                filters.append(StockFundamental.pe_ratio <= criteria["pe_max"])
                filters.append(StockFundamental.pe_ratio > 0)  # Exclude negative/zero PE

            # P/B ratio filter
            if criteria.get("pb_min") is not None:
                filters.append(StockFundamental.pb_ratio >= criteria["pb_min"])
            if criteria.get("pb_max") is not None:
                filters.append(StockFundamental.pb_ratio <= criteria["pb_max"])

            # ROE filter
            if criteria.get("roe_min") is not None:
                filters.append(StockFundamental.roe >= criteria["roe_min"])

            # ROA filter
            if criteria.get("roa_min") is not None:
                filters.append(StockFundamental.roa >= criteria["roa_min"])

            # Gross margin filter
            if criteria.get("gross_margin_min") is not None:
                filters.append(StockFundamental.gross_margin >= criteria["gross_margin_min"])

            # Market cap filter
            if criteria.get("market_cap_min") is not None:
                filters.append(StockFundamental.market_cap >= criteria["market_cap_min"])
            if criteria.get("market_cap_max") is not None:
                filters.append(StockFundamental.market_cap <= criteria["market_cap_max"])

            # Industry filter
            if criteria.get("industry"):
                filters.append(Stock.industry == criteria["industry"])

            # Apply all filters
            if filters:
                query = query.filter(and_(*filters))

            # Execute query
            results = query.limit(limit).all()

            # Format results
            stocks = []
            for stock, fundamental in results:
                stock_data = {
                    "stock_id": stock.stock_id,
                    "name": stock.name,
                    "industry": stock.industry,
                    "market": stock.market,
                    "market_region": stock.market_region,
                }

                if fundamental:
                    stock_data.update({
                        "pe_ratio": float(fundamental.pe_ratio) if fundamental.pe_ratio else None,
                        "pb_ratio": float(fundamental.pb_ratio) if fundamental.pb_ratio else None,
                        "eps": float(fundamental.eps) if fundamental.eps else None,
                        "roe": float(fundamental.roe) if fundamental.roe else None,
                        "roa": float(fundamental.roa) if fundamental.roa else None,
                        "gross_margin": float(fundamental.gross_margin) if fundamental.gross_margin else None,
                        "market_cap": float(fundamental.market_cap) if fundamental.market_cap else None,
                        "report_date": fundamental.report_date.isoformat() if fundamental.report_date else None,
                    })

                stocks.append(stock_data)

            # Filter by dividend yield if specified (requires separate query)
            if criteria.get("dividend_yield_min") is not None:
                stocks = await self._filter_by_dividend_yield(
                    db, stocks, criteria["dividend_yield_min"]
                )

            return stocks[:limit]

        except Exception as e:
            logger.error("Error screening stocks: %s", e)
            return []

    async def _filter_by_dividend_yield(
        self,
        db: Session,
        stocks: List[Dict],
        min_yield: float
    ) -> List[Dict]:
        """Filter stocks by dividend yield"""
        if not stocks:
            return stocks

        stock_ids = [s["stock_id"] for s in stocks]

        # Get latest dividend data
        dividends = (
            db.query(StockDividend)
            .filter(StockDividend.stock_id.in_(stock_ids))
            .order_by(desc(StockDividend.year))
            .all()
        )

        # Build dividend yield map (use latest year)
        dividend_map = {}
        for d in dividends:
            if d.stock_id not in dividend_map:
                dividend_map[d.stock_id] = {
                    "dividend_yield": float(d.dividend_yield) if d.dividend_yield else None,
                    "total_dividend": float(d.total_dividend) if d.total_dividend else None,
                }

        # Filter and add dividend data
        filtered = []
        for stock in stocks:
            div_data = dividend_map.get(stock["stock_id"], {})
            dividend_yield = div_data.get("dividend_yield")

            if dividend_yield is not None and dividend_yield >= min_yield:
                stock["dividend_yield"] = dividend_yield
                stock["total_dividend"] = div_data.get("total_dividend")
                filtered.append(stock)

        return filtered

    async def get_preset_screens(self) -> List[Dict]:
        """
        取得預設篩選條件列表

        Returns:
            List of preset screen configurations
        """
        return [
            {
                "id": key,
                "name": value["name"],
                "name_en": value["name_en"],
                "description": value["description"],
                "criteria": value["criteria"],
            }
            for key, value in self.PRESET_SCREENS.items()
        ]

    async def get_preset_screen_results(
        self,
        db: Session,
        preset_id: str,
        market: str = "TW",
        limit: int = 50
    ) -> List[Dict]:
        """
        執行預設篩選

        Args:
            db: Database session
            preset_id: Preset screen ID (e.g., 'high_dividend')
            market: 'TW' or 'US'
            limit: Maximum results

        Returns:
            List of matching stocks
        """
        preset = self.PRESET_SCREENS.get(preset_id)
        if not preset:
            return []

        return await self.screen_stocks(
            db=db,
            criteria=preset["criteria"],
            market=market,
            limit=limit
        )

    async def get_industries(self, db: Session, market: str = "TW") -> List[str]:
        """
        取得產業列表

        Args:
            db: Database session
            market: 'TW' or 'US'

        Returns:
            List of unique industries
        """
        try:
            industries = (
                db.query(Stock.industry)
                .filter(
                    Stock.market_region == market,
                    Stock.industry.isnot(None),
                    Stock.industry != ""
                )
                .distinct()
                .all()
            )
            return sorted([i[0] for i in industries if i[0]])
        except Exception as e:
            logger.error("Error getting industries: %s", e)
            return []

    async def get_top_by_metric(
        self,
        db: Session,
        metric: str,
        market: str = "TW",
        ascending: bool = False,
        limit: int = 20
    ) -> List[Dict]:
        """
        依特定指標排名取得股票

        Args:
            db: Database session
            metric: Metric to sort by ('pe_ratio', 'roe', 'dividend_yield', etc.)
            market: 'TW' or 'US'
            ascending: Sort ascending if True, descending if False
            limit: Maximum results

        Returns:
            List of stocks sorted by metric
        """
        try:
            # Map metric names to model attributes
            metric_map = {
                "pe_ratio": StockFundamental.pe_ratio,
                "pb_ratio": StockFundamental.pb_ratio,
                "eps": StockFundamental.eps,
                "roe": StockFundamental.roe,
                "roa": StockFundamental.roa,
                "gross_margin": StockFundamental.gross_margin,
                "market_cap": StockFundamental.market_cap,
            }

            if metric not in metric_map:
                return []

            sort_col = metric_map[metric]
            order = sort_col.asc() if ascending else sort_col.desc()

            results = (
                db.query(Stock, StockFundamental)
                .join(StockFundamental, Stock.stock_id == StockFundamental.stock_id)
                .filter(
                    Stock.market_region == market,
                    sort_col.isnot(None),
                    sort_col > 0
                )
                .order_by(order)
                .limit(limit)
                .all()
            )

            return [
                {
                    "stock_id": stock.stock_id,
                    "name": stock.name,
                    "industry": stock.industry,
                    metric: float(getattr(fundamental, metric)) if getattr(fundamental, metric) else None,
                }
                for stock, fundamental in results
            ]

        except Exception as e:
            logger.error("Error getting top stocks by %s: %s", metric, e)
            return []


# Global service instance
screener_service = ScreenerService()
