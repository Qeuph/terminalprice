from textual.screen import ModalScreen
from textual.widgets import Label, Static
from textual.containers import Vertical, Container
from textual.app import ComposeResult

class HelpScreen(ModalScreen):
    BINDINGS = [("escape,q,question_mark", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        help_text = """
[bold]TerminalPrice Keyboard Shortcuts[/]

[yellow]/[/]        Open Search
[yellow]Ctrl+P[/]   Command Palette
[yellow]?[/]        This Help Screen
[yellow]a[/]        Add current to Watchlist
[yellow]d[/]        Remove from Watchlist
[yellow]t[/]        Cycle Timeframe
[yellow]c[/]        Cycle Currency
[yellow]+ / -[/]    Zoom In/Out
[yellow]← / →[/]    Scroll Chart
[yellow]r[/]        Refresh Data
[yellow]q[/]        Quit

[dim]Press ESC or ? to close[/]
"""
        yield Container(
            Static(help_text, id="help_text"),
            id="help_container"
        )

    def action_dismiss(self) -> None:
        self.dismiss()
