from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, ListView, ListItem, Label, Button
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.reactive import reactive

from data_providers.crypto import CryptoProvider
from data_providers.traditional import TraditionalProvider
from utils.currency import CurrencyConverter
from utils.persistence import PersistenceManager
from models.instrument import Instrument, MarketType
from ui.chart_widget import ChartWidget

import asyncio

class SearchModal(ModalScreen):
    market_filter = "ALL"

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Exchange (for Crypto)"),
            Input(value="binance", placeholder="e.g. binance, coinbase...", id="exchange_input"),
            Label("Search Symbol (e.g. BTC, AAPL, EURUSD)"),
            Input(placeholder="Enter symbol...", id="search_input"),
            Horizontal(
                Button("All", id="filter_all", variant="primary"),
                Button("Stocks", id="filter_stock"),
                Button("Crypto", id="filter_crypto"),
                Button("Forex", id="filter_forex"),
                classes="filter_buttons"
            ),
            ListView(id="results_list"),
            id="search_container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        for btn in self.query(".filter_buttons Button"):
            btn.variant = "default"
        event.button.variant = "primary"

        if event.button.id == "filter_all": self.market_filter = "ALL"
        elif event.button.id == "filter_stock": self.market_filter = MarketType.STOCK
        elif event.button.id == "filter_crypto": self.market_filter = MarketType.CRYPTO
        elif event.button.id == "filter_forex": self.market_filter = MarketType.FOREX

        # Re-trigger search if input has value
        search_input = self.query_one("#search_input", Input)
        if search_input.value:
            asyncio.create_task(self.run_search(search_input.value))

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_input":
            if len(event.value) < 2:
                return
            await self.run_search(event.value)

    async def run_search(self, query: str) -> None:
        exchange = self.query_one("#exchange_input", Input).value or "binance"
        results = await self.app.search_instruments(query, exchange)

        # Apply filter
        if self.market_filter != "ALL":
            results = [r for r in results if r.market_type == self.market_filter]

        list_view = self.query_one("#results_list", ListView)
        await list_view.clear()
        for instrument in results:
            label = f"{instrument.symbol} - {instrument.name} ({instrument.market_type.value})"
            if instrument.exchange:
                label += f" [{instrument.exchange}]"
            list_view.append(ListItem(Label(label), name=instrument.symbol))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_name = event.item.name
        self.dismiss(selected_name)

class TerminalPriceApp(App):
    CSS = """
    #main_container {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 4fr;
    }
    #sidebar {
        background: $panel;
        border-right: tall $primary;
    }
    #search_container {
        padding: 1 2;
        background: $panel;
        border: thick $primary;
        width: 80;
        height: 30;
        align: center middle;
    }
    .filter_buttons {
        height: 3;
        margin: 1 0;
    }
    .filter_buttons Button {
        min-width: 10;
        margin-right: 1;
    }
    #results_list {
        height: 10;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "search", "Search"),
        Binding("t", "change_timeframe", "Timeframe"),
        Binding("c", "change_currency", "Currency"),
        Binding("a", "add_to_watchlist", "Add Watchlist"),
        Binding("plus", "zoom_in", "Zoom In"),
        Binding("minus", "zoom_out", "Zoom Out"),
        Binding("left", "scroll_left", "Scroll Left"),
        Binding("right", "scroll_right", "Scroll Right"),
        Binding("r", "refresh", "Refresh"),
    ]

    current_instrument = reactive(None)
    timeframe = reactive("1h")
    target_currency = reactive("USD")

    def __init__(self):
        super().__init__()
        self.crypto_provider = CryptoProvider()
        self.trad_provider = TraditionalProvider()
        self.currency_converter = CurrencyConverter()
        self.persistence = PersistenceManager()
        self.last_search_results = []
        self.watchlist = []
        self.recent = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_container"):
            with Vertical(id="sidebar"):
                yield Label("WATCHLIST")
                yield ListView(id="watchlist_list")
                yield Label("RECENT")
                yield ListView(id="recent_list")
            with Vertical():
                yield Static(id="instrument_header")
                yield ChartWidget(id="main_chart")
        yield Footer()

    async def on_mount(self) -> None:
        await self.currency_converter.update_rates()
        self.watchlist = self.persistence.load_watchlist()
        self.recent = self.persistence.load_recent()
        self.update_sidebars()

        # Default instrument
        await self.select_instrument(Instrument("BTC/USDT", "Bitcoin", MarketType.CRYPTO, "ccxt", "USDT", "binance"))
        self.set_interval(30, self.refresh_data)

    def update_sidebars(self):
        wl = self.query_one("#watchlist_list", ListView)
        wl.clear()
        for i in self.watchlist:
            wl.append(ListItem(Label(i.symbol), name=i.symbol))

        rl = self.query_one("#recent_list", ListView)
        rl.clear()
        for i in self.recent:
            rl.append(ListItem(Label(i.symbol), name=i.symbol))

    async def search_instruments(self, query: str, exchange: str = "binance"):
        # Search both providers
        crypto_task = self.crypto_provider.search_symbols(exchange, query)
        trad_task = self.trad_provider.search_symbols(query)

        results = await asyncio.gather(crypto_task, trad_task)
        self.last_search_results = results[0] + results[1]
        return self.last_search_results

    async def action_search(self) -> None:
        def check_search_result(symbol_name: str | None):
            if symbol_name:
                instrument = next((i for i in self.last_search_results if i.symbol == symbol_name), None)
                if instrument:
                    asyncio.create_task(self.select_instrument(instrument))

        self.push_screen(SearchModal(), check_search_result)

    async def select_instrument(self, instrument: Instrument):
        self.current_instrument = instrument
        # Add to recent
        if instrument not in self.recent:
            self.recent.insert(0, instrument)
            self.recent = self.recent[:10]
            self.persistence.save_recent(self.recent)
            self.update_sidebars()

        await self.refresh_data()

    async def refresh_data(self):
        if not self.current_instrument:
            return

        inst = self.current_instrument
        try:
            if inst.provider == 'ccxt':
                data = await self.crypto_provider.fetch_ohlcv(inst.exchange, inst.symbol, self.timeframe)
            else:
                data = await self.trad_provider.fetch_ohlcv(inst.symbol, self.timeframe)

            # Normalize to target currency
            if inst.currency != self.target_currency:
                for d in data:
                    d.open = self.currency_converter.convert(d.open, inst.currency, self.target_currency)
                    d.high = self.currency_converter.convert(d.high, inst.currency, self.target_currency)
                    d.low = self.currency_converter.convert(d.low, inst.currency, self.target_currency)
                    d.close = self.currency_converter.convert(d.close, inst.currency, self.target_currency)

            chart = self.query_one("#main_chart", ChartWidget)
            chart.data = data

            header = self.query_one("#instrument_header", Static)
            last_price = data[-1].close if data else 0
            header.update(f"[bold]{inst.symbol}[/] ({inst.name}) - {self.timeframe} - [green]{last_price:.2f} {self.target_currency}[/]")
        except Exception as e:
            self.notify(f"Error fetching data: {str(e)}", severity="error")

    def action_zoom_in(self):
        self.query_one("#main_chart", ChartWidget).zoom_in()

    def action_zoom_out(self):
        self.query_one("#main_chart", ChartWidget).zoom_out()

    def action_scroll_left(self):
        self.query_one("#main_chart", ChartWidget).scroll_left()

    def action_scroll_right(self):
        self.query_one("#main_chart", ChartWidget).scroll_right()

    async def action_refresh(self):
        await self.refresh_data()

    async def action_change_timeframe(self):
        # Simple cycle for now
        timeframes = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        idx = timeframes.index(self.timeframe)
        self.timeframe = timeframes[(idx + 1) % len(timeframes)]
        await self.refresh_data()

    async def action_add_to_watchlist(self):
        if self.current_instrument and self.current_instrument not in self.watchlist:
            self.watchlist.append(self.current_instrument)
            self.persistence.save_watchlist(self.watchlist)
            self.update_sidebars()
            self.notify(f"Added {self.current_instrument.symbol} to watchlist")

    async def action_change_currency(self):
        currencies = ["USD", "EUR", "GBP", "JPY", "BTC"]
        idx = currencies.index(self.target_currency) if self.target_currency in currencies else 0
        self.target_currency = currencies[(idx + 1) % len(currencies)]
        await self.refresh_data()

    async def on_shutdown(self):
        await self.crypto_provider.close()

if __name__ == "__main__":
    app = TerminalPriceApp()
    app.run()
