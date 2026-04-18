from dataclasses import dataclass
from enum import Enum
from typing import Optional

class MarketType(Enum):
    STOCK = "stock"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    INDEX = "index"

@dataclass
class Instrument:
    symbol: str
    name: str
    market_type: MarketType
    provider: str  # 'ccxt' or 'yfinance'
    currency: str = "USD"
    exchange: Optional[str] = None
