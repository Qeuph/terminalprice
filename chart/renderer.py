from typing import List, Tuple
from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style
from models.ohlcv import OHLCV
import math

class CandlestickChart:
    def __init__(self, data: List[OHLCV], width: int, height: int):
        self.data = data
        self.width = width
        self.height = height
        self.zoom_level = 1.0
        self.scroll_offset = 0  # Number of candles to skip from the end

    def render(self) -> List[str]:
        if not self.data:
            return ["No data to display"]

        # UI configuration
        price_axis_width = 12
        time_axis_height = 1
        volume_height = int(self.height * 0.2)
        chart_height = self.height - time_axis_height - volume_height
        chart_width = self.width - price_axis_width

        # Calculate visible range
        candle_width = max(1, int(self.zoom_level))
        spacing = 1
        visible_candles_count = int(chart_width / (candle_width + spacing))
        if visible_candles_count < 2: visible_candles_count = 2

        end_idx = len(self.data) - self.scroll_offset
        start_idx = max(0, end_idx - visible_candles_count)
        visible_data = self.data[start_idx:end_idx]

        if not visible_data:
            return ["No data in visible range"]

        # Scale Price
        min_price = min(d.low for d in visible_data)
        max_price = max(d.high for d in visible_data)
        price_range = max_price - min_price
        if price_range == 0: price_range = 1

        # Scale Volume
        max_volume = max(d.volume for d in visible_data) if any(d.volume for d in visible_data) else 1
        if max_volume == 0: max_volume = 1

        canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]

        for i, d in enumerate(visible_data):
            x = i * (candle_width + spacing)
            if x + candle_width > chart_width:
                break

            # --- Render Candlestick ---
            def to_y_price(price):
                return int((chart_height - 1) * (1 - (price - min_price) / price_range))

            y_open = to_y_price(d.open)
            y_close = to_y_price(d.close)
            y_high = to_y_price(d.high)
            y_low = to_y_price(d.low)

            is_bullish = d.close >= d.open
            color = "green" if is_bullish else "red"

            # Draw wick
            for y in range(min(y_high, y_low), max(y_high, y_low) + 1):
                if 0 <= y < chart_height:
                    canvas[y][x + candle_width // 2] = '│'

            # Draw body
            body_top = min(y_open, y_close)
            body_bottom = max(y_open, y_close)
            for y in range(body_top, body_bottom + 1):
                if 0 <= y < chart_height:
                    for dx in range(candle_width):
                        canvas[y][x + dx] = f"[{color}]█[/]"

            # --- Render Volume ---
            vol_y_size = int((d.volume / max_volume) * (volume_height - 1))
            for v_off in range(vol_y_size + 1):
                y = self.height - time_axis_height - 1 - v_off
                if y >= chart_height:
                    for dx in range(candle_width):
                        canvas[y][x + dx] = f"[{color}]┃[/]"

            # --- Render Time Axis (Partial) ---
            if i % 5 == 0:
                time_str = d.timestamp.strftime("%H:%M" if self.zoom_level > 1 else "%d/%m")
                for j, char in enumerate(time_str):
                    if x + j < chart_width:
                        canvas[self.height - 1][x + j] = char

        # --- Render Price Axis (Right) ---
        for y in range(chart_height):
            price = max_price - (y / (chart_height - 1)) * price_range
            price_str = f" {price:10.2f}"
            for j, char in enumerate(price_str):
                if chart_width + j < self.width:
                    canvas[y][chart_width + j] = f"[dim]{char}[/]"

        # Add vertical separator for price axis
        for y in range(self.height - time_axis_height):
            canvas[y][chart_width] = '│'

        return ["".join(row) for row in canvas]

# For Textual integration, we'll likely wrap this in a Widget
