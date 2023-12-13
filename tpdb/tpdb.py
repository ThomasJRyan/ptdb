import sys

from weakref import proxy

from rich.syntax import Syntax

from textual.app import App, AutopilotCallbackType
from textual.widgets import Footer, Header, Static
from textual.containers import ScrollableContainer, VerticalScroll, Vertical, Horizontal

from typing import TYPE_CHECKING, Any, Coroutine

if TYPE_CHECKING:
    from tpdb.debugger import Debugger


from tpdb.widgets import CodeWidget
from tpdb.widgets.navigatable import CodeNavigatable, VarNavigatable

class tPDBApp(App):
    
    def __init__(self, debugger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.debugger: Debugger = proxy(debugger)
        # self.debugger.set_step()
        # sys.settrace(self.debugger.trace_dispatch)
        
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]
    
    
    def compose(self):
        yield Header()
        yield Horizontal(
            CodeNavigatable(
                id='code', 
                filepath=self.debugger.current_bp.file,
                index=self.debugger.current_bp.line-1
                ),
            Vertical(
                VarNavigatable(id='var1'),
                VarNavigatable(id='var2'),
                VarNavigatable(id='var3'),
                )
            )
        yield Footer()
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
        
    def action_quit(self) -> Coroutine[Any, Any, None]:
        self.debugger._quit = True
        return super().action_quit()
        
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