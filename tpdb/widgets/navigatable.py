from __future__ import annotations

import inspect

from types import ModuleType
from typing import Any, Coroutine, ClassVar, TYPE_CHECKING

from rich.syntax import Syntax, ANSISyntaxTheme, ANSI_DARK, SyntaxTheme, Lines
from rich.text import Text


from textual.reactive import reactive
from textual.events import Resize, Event
from textual.binding import Binding, BindingType
from textual.widgets import Static, Tree
from textual.containers import VerticalScroll, Vertical
from textual.widgets.tree import TreeNode, TreeDataType

if TYPE_CHECKING:
    from tpdb.debugger import Debugger

# print(f'{self._index=}, {self._line_cursor=}, {self.start=}, {self.end=}, {self.height=}, {len(self.children)}')


class Line(Static, can_focus=True):
    """A simple label widget for displaying text-oriented renderables."""

    DEFAULT_CSS = """
    Line {
        width: 100%;
        height: 1;
    }
    """
    
def ensure_lines(func):
    def wrapper(self, *args, **kwargs):
        if not self.lines:
            return
        return func(self, *args, **kwargs)
    return wrapper

class Navigatable(Vertical, can_focus=True):
    
    DEFAULT_CSS = """    
    Navigatable .highlighted {
        background: rgb(0,128,255) !important;
    }
    """
    
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("left", "scroll_left", "Scroll Up", show=False),
        Binding("right", "scroll_right", "Scroll Right", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]
    
    def __init__(self, *args, index: int = 0, **kwargs):
        self.lines: Lines = None
        self._index = index
        self._line_cursor = 0
        
        self.debugger: Debugger = self.app.debugger
            
        super().__init__(*args, **kwargs)
        
        
        
    # def set_lines(self, text: str, language: str = 'python', theme: SyntaxTheme = ANSISyntaxTheme, cursor_pos: int = 0):
    #     """Sets the lines

    #     Args:
    #         text (str): Text to split on newlines and set
    #         language (str, optional): Language to highlight. Defaults to 'python'.
    #         theme (SyntaxTheme, optional): Theme to use to highlight. Defaults to ANSISyntaxTheme.
    #         cursor_pos (int, optional): Cursor position to start at. Defaults to 0
    #     """
    #     syntax_highlighter = Syntax('', language, theme=theme(ANSI_DARK))
    #     highlighted_text = syntax_highlighter.highlight(text)
    #     self.lines = highlighted_text.split()
        
    #     # Remove children and update lines
    #     self.remove_children()
    #     self.update_line_range()
    #     for i in range(self.start, self.end):
    #         self.mount(Line(self.lines[i]))
            
    #     self._index = cursor_pos
    #     self.reload_lines()
        
    def reload_lines(self):
        """Reload the lines. Primarly used for terminal size change"""
        current_line = self.lines[self._index]
        
        # Remove all children and update the line range
        self.remove_children()
        self.update_line_range()
        
        # Get the midpoint of the new height so we can center our cursor
        half_height = self.height // 2
        if self._index > half_height:
            for _ in range(half_height):
                if self.end + 1 >= len(self.lines):
                    break
                self.end += 1
                self.start += 1
        
        # Mount the lines to the container
        for cur_pos, i in enumerate(range(self.start, self.end)):
            if id(self.lines[i]) == id(current_line):
                self._line_cursor = cur_pos
            self.mount(self.get_formatted_line(i))
            
        # Add our cursor highlight
        self.children[self._line_cursor].add_class('highlighted')
                    
    def update_line_range(self):
        """Updates the current line range"""
        self.height = self.size.height
        self.start = max(0, self._index + 1 - self.height)
        self.end = min(len(self.lines), self.start + self.height)
        
    def paginate(self, direction: int) -> bool:
        """Paginate the given lines

        Args:
            direction (int): Direction to paginate

        Returns:
            bool: True if successfully paginated, False otherwise
        """
        # Move Down
        if self._index >= self.end:
            self.mount(self.get_formatted_line(self._index))
            self.children[0].remove()
            self.end += direction
            self.start += direction
            return True
        # Move Up
        elif self._index < self.start:
            self.mount(self.get_formatted_line(self._index), before=0)
            self.children[-1].remove()
            self.end += direction
            self.start += direction
            return True
        return False
        
    def update_cursor(self, direction: int) -> None:
        """Updates the cursor in the given direction

        Args:
            direction (int): Direction to update the cursor to
                             Positive numbers bring the cursor down
                             Negative numbers bring the cursor up 
        """
        self._index += direction
        self.children[self._line_cursor].remove_class('highlighted')
        if not self.paginate(direction):
            self._line_cursor += direction
        self.children[self._line_cursor].add_class('highlighted')
        
    def get_formatted_line(self, index):
        return Line(self.lines[index])
    
    #------------------------------------------------
    #                Actions
    #------------------------------------------------
    
    @ensure_lines
    def action_scroll_down(self) -> None:
        """Scroll the text down"""
        if self._index + 1 < len(self.lines):
            self.update_cursor(1)
            
    @ensure_lines
    def action_scroll_up(self) -> None:
        """Scroll the text up"""
        if self._index - 1 >= 0:
            self.update_cursor(-1)
        
    #------------------------------------------------
    #                Events
    #------------------------------------------------
        
    def on_event(self, event: Event) -> Coroutine[Any, Any, None]:
        """Reload the text on terminal resize

        Args:
            event (Event): Textual Event

        Returns:
            Coroutine[Any, Any, None]: Event details
        """
        if isinstance(event, Resize) and self.lines:
            self.reload_lines()
        return super().on_event(event)
        
class CodeNavigatable(Navigatable, can_focus=True):
    
    DEFAULT_CSS = """    
    CodeNavigatable .current_line {
        background: rgb(0,128,0);
    }
    """
    
    BINDINGS = [
        ('b', 'toggle_breakpoint', 'Toggle Breakpoint'),
        ('s', 'do_step', 'Step'),
        ('n', 'do_next', 'Next'),
    ]
    
    # current_line = reactive(0)
    
    def __init__(self, *args, filepath: str, index: int = 0, language: str = 'python', theme: SyntaxTheme = ANSISyntaxTheme, **kwargs):
        super().__init__(*args, index=index, **kwargs)
        
        self.filepath = filepath
        self.current_line = self.debugger.current_frame.f_lineno - 1
        
        with open(filepath) as fil:
            text = fil.read()
            syntax_highlighter = Syntax('', language, theme=theme(ANSI_DARK))
            highlighted_text = syntax_highlighter.highlight(text)
            self.lines = highlighted_text.split()
                    
    def get_formatted_line(self, index: int = None):
        if index is None:
            index = self._index
        line_count = len(str(len(self.lines)))
        line_no = Text(" {index:>{width}} ".format(index=index+1, width=line_count))
        return Line(line_no + self.lines[index], id=f'code_line_{index}')
    
    def action_toggle_breakpoint(self):
        self.debugger.toggle_breakpoint(
            filename=self.filepath, 
            lineno=self._index+1)
        
    def update_current_line(self, index):
        try:
            line = self.query_one(f'#code_line_{self.current_line}')
            line.remove_class('current_line')
            line = self.query_one(f'#code_line_{index}')
            line.add_class('current_line')
        except Exception:
            pass
        
    def reload_lines(self):
        super().reload_lines()
        line = self.query_one(f'#code_line_{self.current_line}')
        line.add_class('current_line')
        
    # def action_do_step(self):
    #     print(self.debugger.current_bp.file, self.debugger.current_bp.line)
    #     self.debugger.set_step()
    #     print(self.debugger.current_bp.file, self.debugger.current_bp.line)
    #     self.update_current_line(self.debugger.current_bp.line)
        
    def action_do_step(self):
        self.debugger.set_step()
        # self.update_current_line(self.debugger.current_frame.f_lineno)
        self.app.exit()
        
    def action_do_next(self):
        # print(self.debugger.current_frame)
        # print(self.debugger.current_bp.file, self.debugger.current_frame.f_lineno)
        # print(self.debugger.set_next())
        # print(self.debugger.current_bp.file, self.debugger.current_frame.f_lineno)
        # print(self.app._driver)
        self.debugger.set_next()
        # self.update_current_line(self.debugger.current_frame.f_lineno)
        self.app.exit()
        
    # def watch_current_line(self, *args, **kwargs):
    #     try:
    #         line = self.query_one(f'#code_line_{self.current_line}')
    #         line.add_class('.current_line')
    #     except Exception:
    #         pass
        
    # def on_event(self, event: Event) -> Coroutine[Any, Any, None]:
    #     """Reload the text on terminal resize

    #     Args:
    #         event (Event): Textual Event

    #     Returns:
    #         Coroutine[Any, Any, None]: Event details
    #     """
    #     if isinstance(event, Resize) and self.lines:
    #         self.current_line = self.debugger.current_bp.line
    #     return super().on_event(event)
        
        # if self.filepath in self.debugger.breaks:
        #     self.debugger.clear_break(
        #         filename = self.filepath,
        #         lineno = self._index + 1
        #     )
        # else:
        #     self.debugger.set_breakpoint(
        #         filename = self.filepath,
        #         lineno = self._index + 1
        #     )
        # print(self.debugger.breaks)
        # print(self.debugger.breakpoints)
    
    # def action_set_text(self):
    #     with open('navigatable.py') as fil:
    #         self.set_lines(fil.read(), cursor_pos=100)
    
class ObjectTree(Tree):
    DEFAULT_CSS = """
    ObjectTree {
        height: 1;
    }
    """
    
    def __init__(self, label: str, obj: object, *args, **kwargs):
        super().__init__(label, *args, **kwargs)
        self.obj = obj
        
    def action_toggle_node(self) -> None:
        if not self._nodes:
            for key, val in self.obj.__dict__.items():
                self.root.add(key, val)
        return super().action_toggle_node()
        
class VarNavigatable(VerticalScroll):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debugger = self.app.debugger
        # print(self.debugger.current_frame.f_locals)
        # self.lines = []
        # for key, value in self.debugger.current_frame.f_locals.items():
        #     if key.startswith('_'):
        #         continue
        #     if isinstance(value, ModuleType):
        #         continue
        #     # self.lines.append(f"{key}: {value}")
        #     self.mount(ObjectTree(key, value))

class VariableView(Tree):
    
    DEFAULT_CSS = """
        ObjectTree {
            height: 1;
        }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debugger: Debugger = self.app.debugger
        self.show_root = False
        self.guide_depth = 2
        
        self.show_level = 0
        
        for key, val in self.debugger.current_frame.f_locals.items():
            self.root.add(f"{key}: {val.__repr__()}", data=val)
            
    def _check_value(self, val):
        literals = (int, str, list, dict, tuple, set, float, bool)
        if self.show_level == 0:
            return isinstance(val, literals)
        elif self.show_level == 1:
            return isinstance(val, literals)
        if self.show_level == 2:
            return True
        
            
        
        if isinstance(val, ):
            return False
        return True
            
    # def add_nodes(self, )
    def _toggle_node(self, node: TreeNode[TreeDataType]) -> None:
        if not node.allow_expand:
            return
        
        print(self._updates)
        
        # if not node.tree.children:
        # if not node.tree._tree_nodes:
        if not node._children:
            for key, val in inspect.getmembers(node.data, self._check_value):
                if self.show_level == 0 and key.startswith('_'):
                    continue
                elif self.show_level == 1 and key.startswith('__'):
                    continue
                try:
                    node.add(f"{key}: {val.__repr__()}", data=val)
                except Exception:
                    node.add_leaf(f"{key}: Error", data=val)
                
        if node.is_expanded:
            node.collapse()
        else:
            node.expand() 
    # def action_toggle_node(self) -> None:
    #     """Toggle the expanded state of the target node."""
    #     try:
    #         line = self._tree_lines[self.cursor_line]
    #     except IndexError:
    #         pass
    #     else:
    #         node = line.path[-1]
    #         # if not node._tree_nodes:
    #         #     for key, val, in node.data.__dir__():
    #         #         print(key, val)
    #         #         node.add(f"{key}: {val.__repr__()}", data=val)
    #         self._toggle_node(node)

# class VarNavigatable(Navigatable):
    
#     BINDINGS = [
#         ('enter', 'toggle_attrs', 'Toggle Attributes')
#     ]
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.lines = []
#         for key, value in self.debugger.current_frame.f_locals.items():
#             if key.startswith('_'):
#                 continue
#             if isinstance(value, ModuleType):
#                 continue
#             self.lines.append(f"{key}: {value.__repr__()}")
            
#     def action_toggle_attrs(self):
        