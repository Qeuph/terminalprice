import httpx
import asyncio

class CurrencyConverter:
    def __init__(self):
        self.rates = {"USD": 1.0}
        self.last_updated = None

    async def update_rates(self):
        # Using a free API for demonstration.
        # In a real app, might use a more reliable source.
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://open.er-api.com/v6/latest/USD")
                if response.status_code == 200:
                    data = response.json()
                    self.rates = data.get("rates", {"USD": 1.0})
                    self.last_updated = asyncio.get_event_loop().time()
        except Exception as e:
            print(f"Error updating rates: {e}")

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return amount

        # Convert to USD first
        usd_amount = amount
        if from_currency != "USD":
            rate_to_usd = self.rates.get(from_currency)
            if rate_to_usd:
                usd_amount = amount / rate_to_usd
            else:
                return amount # Fallback

        # Convert from USD to target
        if to_currency == "USD":
            return usd_amount

        rate_from_usd = self.rates.get(to_currency)
        if rate_from_usd:
            return usd_amount * rate_from_usd

        return usd_amount # Fallback
