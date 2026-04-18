import json
import os
from typing import List, Dict
from models.instrument import Instrument, MarketType

class PersistenceManager:
    def __init__(self, filepath: str = "settings.json"):
        self.filepath = filepath

    def save_watchlist(self, watchlist: List[Instrument]):
        data = self._load_data()
        data['watchlist'] = [self._instrument_to_dict(i) for i in watchlist]
        self._save_data(data)

    def load_watchlist(self) -> List[Instrument]:
        data = self._load_data()
        return [self._dict_to_instrument(i) for i in data.get('watchlist', [])]

    def save_recent(self, recent: List[Instrument]):
        data = self._load_data()
        data['recent'] = [self._instrument_to_dict(i) for i in recent]
        self._save_data(data)

    def load_recent(self) -> List[Instrument]:
        data = self._load_data()
        return [self._dict_to_instrument(i) for i in data.get('recent', [])]

    def _instrument_to_dict(self, instrument: Instrument) -> dict:
        return {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "market_type": instrument.market_type.value,
            "provider": instrument.provider,
            "currency": instrument.currency,
            "exchange": instrument.exchange
        }

    def _dict_to_instrument(self, d: dict) -> Instrument:
        return Instrument(
            symbol=d["symbol"],
            name=d["name"],
            market_type=MarketType(d["market_type"]),
            provider=d["provider"],
            currency=d.get("currency", "USD"),
            exchange=d.get("exchange")
        )

    def _load_data(self) -> dict:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_data(self, data: dict):
        with open(self.filepath, 'w') as f:
            json.dump(data, f)
