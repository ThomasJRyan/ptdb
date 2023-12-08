import sys

from weakref import proxy

from rich.syntax import Syntax

from textual.app import App
from textual.widgets import Footer, Header, Static
from textual.containers import ScrollableContainer, VerticalScroll

from navigatable import Navigatable, CodeNavigatable

from typing import TYPE_CHECKING


class MyApp(App):
    
    CSS_PATH = 'main.tcss'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]
    
    def compose(self):
        yield Header()
        yield CodeNavigatable(id='code', filepath='navigatable.py', index=5)
        # yield CodeNavigation(id='code2')
        yield Footer()
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark   
        
    # def on_mount(self):
    #     self.query_one('#code').set_text('a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\n' * 100000)
        
        
if __name__ == '__main__':
    app = MyApp()
    app.run()