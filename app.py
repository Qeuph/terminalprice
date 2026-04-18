from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, ListView, ListItem, Label, Button
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.reactive import reactive
from textual.command import CommandPalette, Hit, Hits, Provider

from data_providers.crypto import CryptoProvider
from data_providers.traditional import TraditionalProvider
from utils.currency import CurrencyConverter
from utils.persistence import PersistenceManager
from models.instrument import Instrument, MarketType
from ui.chart_widget import ChartWidget
from ui.help_screen import HelpScreen
from ui.alert_modal import AlertModal

import asyncio
from functools import partial
from datetime import datetime

class SearchModal(ModalScreen):
    market_filter = "ALL"

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Exchange (for Crypto)"),
            Input(value="kraken", placeholder="e.g. binance, coinbase...", id="exchange_input"),
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

    def on_mount(self) -> None:
        self.query_one("#search_input", Input).focus()

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
        exchange = self.query_one("#exchange_input", Input).value or "kraken"
        results = await self.app.search_instruments(query, exchange)

        # Apply filter
        if self.market_filter != "ALL":
            results = [r for r in results if r.market_type == self.market_filter]

        list_view = self.query_one("#results_list", ListView)
        await list_view.clear()
        for instrument in results:
            market_icon = {
                MarketType.STOCK: "📈",
                MarketType.CRYPTO: "₿",
                MarketType.FOREX: "💱",
                MarketType.COMMODITY: "📦",
                MarketType.INDEX: "📊"
            }.get(instrument.market_type, "❓")

            label = f"{market_icon} [bold]{instrument.symbol}[/] - {instrument.name} ({instrument.currency})"
            if instrument.exchange:
                label += f" [[dim]{instrument.exchange}[/]]"

            list_view.append(ListItem(Label(label), name=instrument.symbol))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_name = event.item.name
        self.dismiss(selected_name)

class AppCommandProvider(Provider):
    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)

        # Timeframe commands
        timeframes = ["1m", "5m", "15m", "1h", "4h", "12h", "1d", "1w", "1mo"]
        for tf in timeframes:
            score = matcher.match(f"Timeframe: {tf}")
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(f"Timeframe: {tf}"),
                    partial(self.app.action_change_timeframe, tf),
                    help=f"Switch chart timeframe to {tf}"
                )

        # Currency commands
        currencies = ["USD", "EUR", "GBP", "JPY", "BTC"]
        for cur in currencies:
            score = matcher.match(f"Currency: {cur}")
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(f"Currency: {cur}"),
                    partial(self.app.action_change_currency, cur),
                    help=f"Switch display currency to {cur}"
                )

        # Other actions
        actions = [
            ("Refresh Data", self.app.action_refresh, "Refresh market data"),
            ("Set Price Alert", self.app.action_set_alert, "Set a price alert for current instrument"),
            ("Add to Watchlist", self.app.action_add_to_watchlist, "Add current symbol to watchlist"),
            ("Toggle Help", self.app.action_help, "Show help screen"),
            ("Quit", self.app.action_quit, "Exit application"),
        ]
        for name, action, help_text in actions:
            score = matcher.match(name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(name),
                    action,
                    help=help_text
                )

class TerminalPriceApp(App):
    COMMANDS = App.COMMANDS | {AppCommandProvider}
    CSS = """
    #main_container {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 5fr;
    }
    #instrument_header {
        height: 3;
        background: $boost;
        color: $text;
        content-align: center middle;
        text-style: bold;
        border-bottom: solid $primary;
    }
    #status_bar {
        height: 1;
        background: $boost;
        color: $text-muted;
        padding: 0 1;
    }
    #sidebar {
        background: $boost;
        border-right: solid $primary;
        padding: 1;
    }
    #sidebar Label {
        text-style: bold;
        background: $primary;
        width: 100%;
        padding: 0 1;
        margin-top: 1;
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
    #alert_container {
        padding: 1 2;
        background: $panel;
        border: thick $primary;
        width: 40;
        height: 15;
        align: center middle;
    }
    #help_container {
        padding: 1 2;
        background: $panel;
        border: thick $primary;
        width: 50;
        height: 25;
        align: center middle;
    }
    .modal_buttons {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "search", "Search"),
        Binding("ctrl+p", "command_palette", "Commands"),
        Binding("question_mark", "help", "Help"),
        Binding("t", "change_timeframe", "Timeframe"),
        Binding("c", "change_currency", "Currency"),
        Binding("a", "add_to_watchlist", "Add Watchlist"),
        Binding("d", "remove_from_watchlist", "Remove Watchlist"),
        Binding("l", "set_alert", "Alert"),
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
        self.alerts = []
        self._data_cache = {}

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
                yield Static(id="status_bar")
        yield Footer()

    async def on_mount(self) -> None:
        await self.currency_converter.update_rates()
        self.watchlist = self.persistence.load_watchlist()
        self.recent = self.persistence.load_recent()
        self.update_sidebars()

        # Default instrument
        await self.select_instrument(Instrument("BTC/USDT", "Bitcoin", MarketType.CRYPTO, "ccxt", "USDT", "kraken"))
        self.set_interval(30, self.refresh_data)

    def update_sidebars(self):
        wl = self.query_one("#watchlist_list", ListView)
        wl.clear()
        for i in self.watchlist:
            wl.append(ListItem(Label(f"⭐ {i.symbol}"), name=i.symbol))

        rl = self.query_one("#recent_list", ListView)
        rl.clear()
        for i in self.recent:
            rl.append(ListItem(Label(f"🕒 {i.symbol}"), name=i.symbol))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id in ["watchlist_list", "recent_list"]:
            symbol = event.item.name
            # Try to find in watchlist first, then recent
            instrument = next((i for i in self.watchlist if i.symbol == symbol), None)
            if not instrument:
                instrument = next((i for i in self.recent if i.symbol == symbol), None)

            if instrument:
                await self.select_instrument(instrument)

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
        # Add to recent, remove existing if present to move to top
        self.recent = [i for i in self.recent if i.symbol != instrument.symbol]
        self.recent.insert(0, instrument)
        self.recent = self.recent[:10]
        self.persistence.save_recent(self.recent)
        self.update_sidebars()

        await self.refresh_data()

    async def refresh_data(self):
        if not self.current_instrument:
            return

        inst = self.current_instrument
        cache_key = f"{inst.provider}_{inst.exchange}_{inst.symbol}_{self.timeframe}"

        status_bar = self.query_one("#status_bar", Static)
        status_bar.update(f"Fetching {inst.symbol} ({self.timeframe})...")

        try:
            # Check cache
            if cache_key in self._data_cache:
                data = self._data_cache[cache_key]
            else:
                if inst.provider == 'ccxt':
                    data = await self.crypto_provider.fetch_ohlcv(inst.exchange, inst.symbol, self.timeframe)
                else:
                    data = await self.trad_provider.fetch_ohlcv(inst.symbol, self.timeframe)

                # Cache the original data
                self._data_cache[cache_key] = data

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
            change = 0
            if len(data) >= 2:
                change = ((data[-1].close - data[-2].close) / data[-2].close) * 100

            change_color = "green" if change >= 0 else "red"
            header.update(
                f"{inst.symbol} | {inst.name} | [bold]{last_price:.2f} {self.target_currency}[/] "
                f"([{change_color}]{change:+.2f}%[/])"
            )

            # Check Alerts
            triggered = []
            for alert in self.alerts:
                if alert['symbol'] == inst.symbol:
                    if (alert['type'] == 'above' and last_price >= alert['price']) or \
                       (alert['type'] == 'below' and last_price <= alert['price']):
                        self.notify(f"ALERT: {inst.symbol} hit {alert['price']:.2f}!", severity="warning")
                        triggered.append(alert)

            self.alerts = [a for a in self.alerts if a not in triggered]

            status_bar.update(
                f"Market: {inst.market_type.value.upper()} | Provider: {inst.provider} | "
                f"Currency: {self.target_currency} | Timeframe: {self.timeframe} | "
                f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            self.notify(f"Error fetching data: {str(e)}", severity="error")
            status_bar.update(f"[red]Error: {str(e)}[/]")

    def action_zoom_in(self):
        self.query_one("#main_chart", ChartWidget).zoom_in()

    def action_zoom_out(self):
        self.query_one("#main_chart", ChartWidget).zoom_out()

    def action_scroll_left(self):
        self.query_one("#main_chart", ChartWidget).scroll_left()

    def action_scroll_right(self):
        self.query_one("#main_chart", ChartWidget).scroll_right()

    async def action_help(self):
        self.push_screen(HelpScreen())

    async def action_refresh(self):
        # Clear cache for current instrument/timeframe and refresh
        if self.current_instrument:
            inst = self.current_instrument
            cache_key = f"{inst.provider}_{inst.exchange}_{inst.symbol}_{self.timeframe}"
            if cache_key in self._data_cache:
                del self._data_cache[cache_key]
        await self.refresh_data()

    async def action_change_timeframe(self, tf: str = None):
        timeframes = ["1m", "5m", "15m", "1h", "4h", "12h", "1d", "1w", "1mo"]
        if tf and tf in timeframes:
            self.timeframe = tf
        else:
            idx = timeframes.index(self.timeframe) if self.timeframe in timeframes else 3
            self.timeframe = timeframes[(idx + 1) % len(timeframes)]
        await self.refresh_data()

    async def action_set_alert(self):
        if not self.current_instrument or not self.current_instrument.symbol:
            return

        inst = self.current_instrument
        cache_key = f"{inst.provider}_{inst.exchange}_{inst.symbol}_{self.timeframe}"
        if cache_key not in self._data_cache or not self._data_cache[cache_key]:
            return

        last_price = self._data_cache[cache_key][-1].close

        def on_alert_set(price: float | None):
            if price:
                alert_type = 'above' if price > last_price else 'below'
                self.alerts.append({
                    'symbol': inst.symbol,
                    'price': price,
                    'type': alert_type
                })
                self.notify(f"Alert set for {inst.symbol} at {price:.2f}")

        self.push_screen(AlertModal(last_price, inst.symbol), on_alert_set)

    async def action_add_to_watchlist(self):
        if not self.current_instrument:
            return

        if any(i.symbol == self.current_instrument.symbol for i in self.watchlist):
            self.notify(f"{self.current_instrument.symbol} is already in watchlist", severity="warning")
            return

        self.watchlist.append(self.current_instrument)
        self.persistence.save_watchlist(self.watchlist)
        self.update_sidebars()
        self.notify(f"Added {self.current_instrument.symbol} to watchlist")

    async def action_remove_from_watchlist(self):
        wl = self.query_one("#watchlist_list", ListView)
        if wl.index is not None and 0 <= wl.index < len(self.watchlist):
            removed = self.watchlist.pop(wl.index)
            self.persistence.save_watchlist(self.watchlist)
            self.update_sidebars()
            self.notify(f"Removed {removed.symbol} from watchlist")
        else:
            self.notify("Select an item in the watchlist to remove", severity="warning")

    async def action_change_currency(self, cur: str = None):
        currencies = ["USD", "EUR", "GBP", "JPY", "BTC"]
        if cur and cur in currencies:
            self.target_currency = cur
        else:
            idx = currencies.index(self.target_currency) if self.target_currency in currencies else 0
            self.target_currency = currencies[(idx + 1) % len(currencies)]
        await self.refresh_data()

    async def on_shutdown(self):
        await self.crypto_provider.close()

if __name__ == "__main__":
    app = TerminalPriceApp()
    app.run()
