import bdb

from rich.syntax import Syntax
from rich.text import Text

from textual.widgets import TextArea, Static, ListView, ListItem, Label
from textual.binding import _Bindings, Binding
from textual.containers import ScrollableContainer, VerticalScroll

from typing import Union

# class Navigation(ListView):
#     ...

class Navigation(VerticalScroll, can_focus=True, can_focus_children=False):
    def __init__(
        self,
        *children: ListItem,
        initial_index: Union[int, None] = 0,
        name: Union[str, None] = None,
        id: Union[str, None] = 'code',
        classes: Union[str, None] = None,
        disabled: bool = False,
    ):
        self._index = initial_index
        self._cursor = initial_index
        # self.scrollbars_enabled = (False, False)
        # self.scroll
        self.debugger = self.app.debugger
        
        current_bp: bdb.Breakpoint = self.debugger.current_bp
        
        children = []
        with open(current_bp.file) as f:
            self.lines = f.readlines()
            
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        self.update_lines()
        self.update_cursor()
        
    def get_renderable_lines(self):
        start = max(0, self._index - 100)
        end = min(len(self.lines), start + 100)
        lines = self.lines[start:end]
        return lines
    
    def update_lines(self):
        lines = self.get_renderable_lines()
        children = []
        for i, line in enumerate(lines):
            f_line = Syntax(
                code = line.strip(), 
                lexer = "python", 
                # line_numbers=True,
                # highlight_lines={current_bp.line},
                )
            children.append(Label(f_line))
        self.remove_children()
        self._add_children(*children)
            # self.children[i] = Label(f_line)
        self.refresh()
        
    def highlight_line(self, line_no: int) -> None:
        child = self.children[5]
        # child.add_class('highlight')
        child.renderable.background_color = 'red'
        child.refresh(layout=True)
        self.refresh(layout=True)
        
    def update_cursor(self):
        self.highlight_line(self._cursor)
            
            # for line in f.readlines():
            #     if not line.strip():
            #         f_line = Syntax(
            #         code = ' ', 
            #         lexer = "python", 
            #         )
            #     else:
            #         f_line = Syntax(
            #             code = line.strip(), 
            #             lexer = "python", 
            #             # line_numbers=True,
            #             # highlight_lines={current_bp.line},
            #             )
            #     children.append(Label(f_line))
        # self._id = id

class CodeWidget(Navigation):
    def __init__(
        self,
        *children: ListItem,
        initial_index: Union[int, None] = 0,
        name: Union[str, None] = None,
        id: Union[str, None] = 'code',
        classes: Union[str, None] = None,
        disabled: bool = False,
    ):
        # self._id = id
        self._index = initial_index
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        self.focus()
        
        # with open(current_bp.file) as f:
        #     code = Syntax(
        #         code = f.read(), 
        #         lexer = "python", 
        #         line_numbers=True,
        #         # highlight_lines={current_bp.line},
        #         )
        #     code.stylize_range('red on white', (1,0), (5,0))
        #     self.update(code)
        #     self.highlight_line(7)
            # self.insert(f.read())
            # self.cursor_location = (current_bp.line-1, 0)
        
        # self.update("hello")
        # self._id = "code"
        # self._closed = False
        # self._closing = False

# class CodeWidget():
    
#     BINDINGS = [
#         Binding("q", "quit", "Quit"),
#         Binding("d", "toggle_dark", "Toggle dark mode"),
#     ]
    
#     def __init__(self):
#         # self._bindings = _Bindings(*self.BINDINGS)
#         super().__init__()
#         self.debugger = self.app.debugger
        
#         self.language = "python"
#         self.cursor_blink = False
        
#         self.clear()
        
#         current_bp = self.debugger.current_bp
#         with open(current_bp.file) as f:
#             self.insert(f.read())
#             self.cursor_location = (current_bp.line-1, 0)
        
        # self.insert(str(self.app.debugger.current_bp))
        # self.insert(str(bdb.Breakpoint.bpbynumber))
        # self.insert(str(self.app.debugger.current_breakpoint))
        # self.insert(str(self._bindings))