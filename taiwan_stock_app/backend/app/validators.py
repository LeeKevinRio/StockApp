"""
輸入驗證工具 — stock_id / pagination / market
"""
import re
from fastapi import HTTPException, Query
from enum import Enum


class MarketEnum(str, Enum):
    TW = "TW"
    US = "US"


# 台股: 1-6 位數字；美股: 1-5 位英文字母（可含 . 如 BRK.B）
_STOCK_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{1,6}(\.[A-Za-z])?$")


def validate_stock_id(stock_id: str) -> str:
    """驗證 stock_id 格式，防止注入"""
    if not _STOCK_ID_PATTERN.match(stock_id):
        raise HTTPException(status_code=400, detail=f"無效的股票代碼: {stock_id}")
    return stock_id


def PaginationLimit(default: int = 50, le: int = 200) -> int:
    """分頁上限參數"""
    return Query(default, ge=1, le=le, description=f"每頁筆數（上限 {le}）")


def PaginationOffset() -> int:
    """分頁偏移參數"""
    return Query(0, ge=0, description="偏移量")
