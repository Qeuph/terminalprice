from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult

class AlertModal(ModalScreen):
    def __init__(self, current_price: float, symbol: str):
        super().__init__()
        self.current_price = current_price
        self.symbol = symbol

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(f"Set Price Alert for {self.symbol}"),
            Label(f"Current Price: {self.current_price:.2f}"),
            Input(placeholder="Enter target price...", id="price_input", type="number"),
            Horizontal(
                Button("Set Alert", variant="primary", id="set_btn"),
                Button("Cancel", id="cancel_btn"),
                classes="modal_buttons"
            ),
            id="alert_container"
        )

    def on_mount(self) -> None:
        self.query_one("#price_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "set_btn":
            try:
                price = float(self.query_one("#price_input", Input).value)
                self.dismiss(price)
            except ValueError:
                pass
        else:
            self.dismiss(None)
