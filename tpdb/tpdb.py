from weakref import proxy

from textual.binding import Binding
from textual.app import App
from textual.widgets import Footer, Header, Label, Tree
from textual.containers import Vertical, Horizontal

from typing import TYPE_CHECKING, Any, Coroutine

if TYPE_CHECKING:
    from tpdb.debugger import Debugger


from tpdb.widgets.browsers import CodeBrowser, VariableBrowser

class tPDBApp(App):
    
    def __init__(self, debugger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.debugger: Debugger = proxy(debugger)

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("right", "move_right", "Move Right", show=True, priority=True),
        Binding("left", "move_left", "Move Left", show=False, priority=True),
    ]
    
    def compose(self):
        yield Header()
        yield Horizontal(
            Vertical(
                CodeBrowser(
                    filepath=self.debugger.filepath,
                    index=self.debugger.lineno-1,
                    id="code-browser"),
            ),
            Vertical(
                Label('[u]V[/u]ariables', markup=True),
                VariableBrowser(
                    'Variables', id="variables"),
                ),
            )
        yield Footer()
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
        
    def action_quit(self) -> Coroutine[Any, Any, None]:
        self.debugger._quit = True
        return super().action_quit()

    def action_move_right(self):
        pane: Tree = self.query_one('#variables')
        pane.focus()

    def action_move_left(self):
        pane = self.query_one('#code-browser')
        pane.focus()
        
        
if __name__ == '__main__':
    app = tPDBApp()
    app.run()