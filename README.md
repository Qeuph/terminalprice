# TerminalPrice

A fast, responsive terminal-based colored trading chart application supporting multiple financial markets.

## Features
- **Multi-market Support**: Stocks, Forex, Cryptocurrencies, Commodities, and Indices.
- **Unified Interface**: Search and select any instrument across different providers (Kraken, Yahoo Finance).
- **High-Resolution Candlestick Charts**: Custom renderer using block characters for improved volume and price visualization.
- **Minimalist TUI**: Modern, clean design with dedicated Sidebar, Header, and Status bar.
- **Command Palette**: Quick access to all features via `Ctrl+P`.
- **Price Alerts**: Set target price alerts and get notified when they are hit.
- **Watchlist & History**: Persist your favorite symbols and recently viewed ones.
- **Currency Normalization**: View prices in USD or other major currencies (EUR, GBP, JPY, BTC).

## Visuals
*(Note: Visuals are rendered in the terminal. Here is a representation of the UI)*

![Main Chart](https://raw.githubusercontent.com/Textualize/textual/main/docs/images/screenshots/screenshot.png) <!-- Placeholder until real screenshots are added to repo -->

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
- `Ctrl+P`: Open Command Palette
- `?`: Show Help screen
- `l`: Set price alert
- `a`: Add current instrument to watchlist
- `t`: Cycle timeframes (1m, 5m, 15m, 1h, 4h, 1d, 1w)
- `c`: Cycle target currency (USD, EUR, GBP, JPY, BTC)
- `+ / -`: Zoom in/out
- `Left / Right`: Scroll chart history
- `r`: Refresh data
- `q`: Quit
