from textual.widget import Widget
from textual.reactive import reactive
from rich.panel import Panel
from rich.text import Text
from chart.renderer import CandlestickChart as Renderer
from models.ohlcv import OHLCV
from typing import List

class ChartWidget(Widget):
    data: reactive[List[OHLCV]] = reactive([])
    zoom_level: reactive[float] = reactive(1.0)
    scroll_offset: reactive[int] = reactive(0)

    def render(self):
        if not self.data:
            return Text("No data available", justify="center")

        # Use full available size
        renderer = Renderer(self.data, self.size.width, self.size.height)
        renderer.zoom_level = self.zoom_level
        renderer.scroll_offset = self.scroll_offset

        chart_lines = renderer.render()
        chart_text = Text.from_markup("\n".join(chart_lines))

        return chart_text

    def zoom_in(self):
        self.zoom_level = min(20.0, self.zoom_level * 1.2)

    def zoom_out(self):
        self.zoom_level = max(0.5, self.zoom_level / 1.2)

    def scroll_left(self):
        self.scroll_offset = min(len(self.data) - 2, self.scroll_offset + max(1, int(5 / self.zoom_level)))

    def scroll_right(self):
        self.scroll_offset = max(0, self.scroll_offset - max(1, int(5 / self.zoom_level)))
