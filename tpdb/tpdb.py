import sys

from weakref import proxy

from rich.syntax import Syntax

from textual.binding import Binding
from textual.app import App, AutopilotCallbackType
from textual.widgets import Footer, Header, Static, Label, Tree
from textual.containers import ScrollableContainer, VerticalScroll, Vertical, Horizontal

from typing import TYPE_CHECKING, Any, Coroutine

if TYPE_CHECKING:
    from tpdb.debugger import Debugger


from tpdb.widgets import CodeWidget
from tpdb.widgets.navigatable import CodeNavigatable, VarNavigatable, VariableView, StackView

class tPDBApp(App):
    
    def __init__(self, debugger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.debugger: Debugger = proxy(debugger)
        # self.debugger.set_step()
        # sys.settrace(self.debugger.trace_dispatch)
        
    
    # BINDINGS = [
    #     ("q", "quit", "Quit"),
    #     ("d", "toggle_dark", "Toggle dark mode"),
    #     ("right", "move_right", "Move Right")
    # ]

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("right", "move_right", "Move Right", show=True, priority=True),
        Binding("left", "move_left", "Move Left", show=False, priority=True),
    ]

    
    
    
    def compose(self):
        yield Header()
        yield Horizontal(
            Vertical(
                CodeNavigatable(
                    id='code', 
                    filepath=self.debugger.current_bp.file,
                    index=self.debugger.current_bp.line-1
                    ),
                id="left-pane"
            ),
            Vertical(
                Label('[u]V[/u]ariables', markup=True),
                VariableView(
                    'Variables', id="variables"),
                # Label('[u]S[/u]tack', markup=True),
                # StackView(
                #     id='stack'),
                # id="right-pane"
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
        # pane.cursor_line = 0
        pane.focus()

    def action_move_left(self):
        pane = self.query_one('#code')
        pane.focus()
    
        
    # def run(self, *args, **kwargs):
    #     super().run(*args, **kwargs)
    #     self.debugger.set_step()
    #     sys.settrace(self.debugger.trace_dispatch)
    
        
    # def on_mount(self):
    #     current_bp = self.debugger.current_bp
        # with open(current_bp.file) as f:
        #     code = Syntax(f.read(), "python", line_numbers=True)
        #     self.query_one("#code").update(code)
            # self.insert(f.read())
            # self.cursor_location = (current_bp.line-1, 0)
    
        
        
if __name__ == '__main__':
    app = tPDBApp()
    app.run()