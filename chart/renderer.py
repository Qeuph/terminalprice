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

        # Calculate visible range
        visible_candles_count = int(self.width / (2 * self.zoom_level))
        if visible_candles_count < 2: visible_candles_count = 2

        end_idx = len(self.data) - self.scroll_offset
        start_idx = max(0, end_idx - visible_candles_count)
        visible_data = self.data[start_idx:end_idx]

        if not visible_data:
            return ["No data in visible range"]

        min_price = min(d.low for d in visible_data)
        max_price = max(d.high for d in visible_data)
        price_range = max_price - min_price
        if price_range == 0: price_range = 1

        canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]

        candle_width = max(1, int(self.zoom_level))
        spacing = 1

        for i, d in enumerate(visible_data):
            x = i * (candle_width + spacing)
            if x + candle_width > self.width:
                break

            # Map prices to Y coordinates
            def to_y(price):
                return int((self.height - 1) * (1 - (price - min_price) / price_range))

            y_open = to_y(d.open)
            y_close = to_y(d.close)
            y_high = to_y(d.high)
            y_low = to_y(d.low)

            is_bullish = d.close >= d.open
            color = "green" if is_bullish else "red"

            # Draw wick
            for y in range(min(y_high, y_low), max(y_high, y_low) + 1):
                if 0 <= y < self.height:
                    canvas[y][x + candle_width // 2] = '│'

            # Draw body
            body_top = min(y_open, y_close)
            body_bottom = max(y_open, y_close)
            for y in range(body_top, body_bottom + 1):
                if 0 <= y < self.height:
                    for dx in range(candle_width):
                        char = '█'
                        canvas[y][x + dx] = f"[{color}]{char}[/]"

        return ["".join(row) for row in canvas]

# For Textual integration, we'll likely wrap this in a Widget
