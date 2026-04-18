import yfinance as yf
import pandas as pd
import asyncio
from typing import List
from models.ohlcv import OHLCV
from models.instrument import Instrument, MarketType
from datetime import datetime
import httpx

class TraditionalProvider:
    def __init__(self):
        pass

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[OHLCV]:
        # yfinance timeframe mapping
        # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        period = "1mo"
        if timeframe in ['1d', '1w']:
            period = "2y"
        elif timeframe in ['1h', '4h']:
            period = "1mo"
        elif timeframe in ['1m', '5m', '15m']:
            period = "7d"

        # Use asyncio.to_thread to avoid blocking the event loop
        ticker = yf.Ticker(symbol)
        df = await asyncio.to_thread(ticker.history, period=period, interval=timeframe)

        if df.empty:
            return []

        df = df.tail(limit)

        results = []
        for index, row in df.iterrows():
            results.append(OHLCV(
                timestamp=index.to_pydatetime(),
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume']
            ))
        return results

    async def search_symbols(self, query: str) -> List[Instrument]:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        async with httpx.AsyncClient() as client:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return []

            data = response.json()
            results = []
            for quote in data.get('quotes', []):
                symbol = quote.get('symbol')
                name = quote.get('longname') or quote.get('shortname') or symbol
                quote_type = quote.get('quoteType')

                market_type = MarketType.STOCK
                if quote_type == 'CURRENCY':
                    market_type = MarketType.FOREX
                elif quote_type == 'CRYPTOCURRENCY':
                    market_type = MarketType.CRYPTO
                elif quote_type == 'INDEX':
                    market_type = MarketType.INDEX
                elif quote_type == 'COMMODITY':
                    market_type = MarketType.COMMODITY

                results.append(Instrument(
                    symbol=symbol,
                    name=name,
                    market_type=market_type,
                    provider='yfinance',
                    currency=quote.get('currency', 'USD')
                ))
            return results
