import ccxt.async_support as ccxt
from typing import List, Optional
from models.ohlcv import OHLCV
from models.instrument import Instrument, MarketType
from datetime import datetime

class CryptoProvider:
    def __init__(self):
        self.exchanges = {}

    async def get_exchange(self, exchange_id: str):
        if exchange_id not in self.exchanges:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchanges[exchange_id] = exchange_class()
        return self.exchanges[exchange_id]

    async def fetch_ohlcv(self, exchange_id: str, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[OHLCV]:
        exchange = await self.get_exchange(exchange_id)
        # ccxt uses 1h, 1d, etc. but 4h is standard too. 1w might need conversion
        tf = timeframe
        if tf == '1w': tf = '1w' # ccxt usually supports 1w

        data = await exchange.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
        return [
            OHLCV(
                timestamp=datetime.fromtimestamp(d[0] / 1000),
                open=d[1],
                high=d[2],
                low=d[3],
                close=d[4],
                volume=d[5]
            ) for d in data
        ]

    async def search_symbols(self, exchange_id: str, query: str) -> List[Instrument]:
        exchange = await self.get_exchange(exchange_id)
        try:
            markets = await exchange.load_markets()
            results = []
            query = query.upper()
            for symbol, market in markets.items():
                if query in symbol.upper():
                    results.append(Instrument(
                        symbol=symbol,
                        name=symbol,
                        market_type=MarketType.CRYPTO,
                        provider='ccxt',
                        exchange=exchange_id,
                        currency=market.get('quote', 'USD')
                    ))
            return results[:50] # Limit results
        except Exception:
            return []

    async def close(self):
        for exchange in self.exchanges.values():
            await exchange.close()
