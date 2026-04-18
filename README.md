# TerminalPrice

A fast, responsive terminal-based colored trading chart application supporting multiple financial markets.

## Features
- **Multi-market Support**: Stocks, Forex, Cryptocurrencies, Commodities, and Indices.
- **Unified Interface**: Search and select any instrument across different providers.
- **Terminal Candlestick Charts**: High-performance, colored rendering with zoom and scroll.
- **Watchlist & History**: Persist your favorite symbols and recently viewed ones.
- **Currency Normalization**: View prices in USD or other major currencies (EUR, GBP, JPY, BTC).
- **Responsive TUI**: Built with Textual for a modern terminal experience.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python3 app.py
```

## Keyboard Controls
- `/`: Open search modal
- `a`: Add current instrument to watchlist
- `t`: Cycle timeframes (1m, 5m, 15m, 1h, 4h, 1d, 1w)
- `c`: Cycle target currency (USD, EUR, GBP, JPY, BTC)
- `+ / -`: Zoom in/out
- `Left / Right`: Scroll chart history
- `r`: Refresh data
- `q`: Quit