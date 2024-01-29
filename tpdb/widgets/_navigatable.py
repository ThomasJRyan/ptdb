from __future__ import annotations

import re
import inspect

from types import ModuleType
from typing import Any, Coroutine, ClassVar, TYPE_CHECKING

from rich.syntax import Syntax, ANSISyntaxTheme, ANSI_DARK, SyntaxTheme, Lines
from rich.text import Text


from textual.reactive import reactive, var
from textual.events import Resize, Event
from textual.binding import Binding, BindingType
from textual.widgets import Static, Tree
from textual.containers import VerticalScroll, Vertical
from textual.widgets.tree import TreeNode, TreeDataType
from textual.geometry import clamp

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

    .highlighted {
        background: rgb(0,128,255) !important;
    }
    """

    highlighted = reactive(False)

    def watch_highlighted(self, value):
        if self.highlighted:
            self.add_class("highlighted")
        else:
            self.remove_class("highlighted")
    
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
        Binding("up", "cursor_up", "Scroll Up", show=False),
        Binding("down", "cursor_down", "Scroll Down", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    cursor_line = reactive(0)

    slice = reactive((0, 0))
    height = var(0)

    index = var(0)

    lines = reactive([])
    
    def __init__(self, *children: list[Lines], **kwargs):
        self.last_slice = self.slice
        
        self.debugger: Debugger = self.app.debugger
        self._children = children
        self.last_child = self._children[self.cursor_line]
        
        self._start = self._end = 0
        
        super().__init__(**kwargs)
        
    def get_formatted_line(self, index):
        return Line(self.lines[index])
    
    def reload_lines(self):
        self._ready = True
        self.remove_children()
        self.height = self.size.height
        start = max(0, self.cursor_line + 1 - self.height)
        end = min(len(self._children), start + self.height)
        self.mount_all(self._children[start:end])
        self.slice = (start, end)
        self.children[self.cursor_line].highlighted = True

        

    #------------------------------------------------
    #                Validators
    #------------------------------------------------
    
    def validate_index(self, value):
        return clamp(value, 0, len(self._children))

    def validate_cursor_line(self, value):
        maximum = min(len(self.children), self.height)
        return clamp(value, 0, maximum-1)
    
    def validate_slice(self, value):
        curr_start, curr_end = self.slice
        
        maximum = len(self._children)
        validate_start = clamp(value[0], 0, maximum - self.height)
        validate_end = clamp(value[1], 0, maximum)
        
        print(f"{curr_start=}, {curr_end=}")
        print(f"{validate_start=}, {validate_end=}")
        
        if not self.slice == (0,0):
            if curr_start == validate_start or curr_end == validate_end:
                return (curr_start, curr_end)
            # elif curr_start != validate_start and curr_end == validate_end:
            #     return (curr_start, curr_end)
        
        # if self.slice[0] == validate_start or self.slice[1] == validate_end:
        #     return value
        return (validate_start, validate_end)


    #------------------------------------------------
    #                Watchers
    #------------------------------------------------

    def watch_cursor_line(self, value: int) -> None:
        try:
            self.last_child.highlighted = False
            self.children[self.cursor_line].highlighted = True
            self.last_child = self.children[self.cursor_line]
        except Exception as e:
            print(f"EXCEPTION: {e}")

    # async def watch_lines(self, value):
    #     await self.remove_children()
    #     try:
    #         self.lines[self.cursor_line].highlighted = True
    #         self.mount_all(self.lines)
    #     except Exception as e:
    #         print(f"EXCEPTION: {e}")
            
    def watch_slice(self, value):
        try:
            start, end = self.slice
            last_start, last_end = self.last_slice
            
            diff_start = start - last_start
            diff_end = end - last_end
            
            sliced_children = self._children[start:end]
            diff_children = [c for c in sliced_children if c not in self.children]
            
            print(diff_start)
            print(diff_children)
            
            if diff_start > 0:
                for pos, child in enumerate(reversed(diff_children)):
                    if pos == diff_start:
                        break
                    self.children[0].remove()
                    self.last_child.highlighted = False
                    child.highlighted = True
                    self.mount(child)
                    self.last_child = child
            elif diff_start < 0:
                
                for pos, child in enumerate(diff_children):
                    print(pos,child)
                    if -pos == diff_start:
                        break
                    self.children[-1].remove()
                    self.last_child.highlighted = False
                    child.highlighted = True
                    self.mount(child, before=0)
                    self.last_child = child
            else:
                self.mount_all(self._children[start:end])
        except Exception as e:
            print(f"EXCEPTION: {e}")
            
        self.last_slice = self.slice
        
    #------------------------------------------------
    #                Actions
    #------------------------------------------------

    def action_cursor_down(self):
        old_cursor = self.cursor_line
        self.cursor_line += 1
        self.index += 1
        
        if self.cursor_line == old_cursor and not self.index == len(self.children):
            start, end = self.slice
            self.slice = (start+1, end+1)
        print(self.slice)
            
    def action_cursor_up(self):
        old_cursor = self.cursor_line
        self.cursor_line -= 1
        self.index -= 1
        
        if self.cursor_line == old_cursor and not self.index == 0:
            start, end = self.slice
            self.slice = (start-1, end-1)
        print(self.slice)
        
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
        if isinstance(event, Resize):
            self.reload_lines()
        return super().on_event(event)
        
class CodeNavigatable(Navigatable, can_focus=True):
    
    DEFAULT_CSS = """    
    CodeNavigatable .cursor_line {
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
        self.filepath = filepath
        
        with open(filepath) as fil:
            text = fil.read()
            syntax_highlighter = Syntax('', language, theme=theme(ANSI_DARK))
            highlighted_text = syntax_highlighter.highlight(text)
            self._lines = highlighted_text.split()
            children = [self.format_line(i) for i in range(len(self._lines))]
        
        super().__init__(*children, **kwargs)
        self.index = index
        self.cursor_line = self.debugger.current_frame.f_lineno - 1
        
        
                    
    def format_line(self, index: int = None):
        if index is None:
            index = self._index
        line_count = len(str(len(self._lines)))
        line_no = Text(" {index:>{width}} ".format(index=index+1, width=line_count))
        return Line(line_no + self._lines[index], id=f'code_line_{index}')
    
    # def action_toggle_breakpoint(self):
    #     self.debugger.toggle_breakpoint(
    #         filename=self.filepath, 
    #         lineno=self._index+1)
        
    # def update_cursor_line(self, index):
    #     try:
    #         line = self.query_one(f'#code_line_{self.cursor_line}')
    #         line.remove_class('cursor_line')
    #         line = self.query_one(f'#code_line_{index}')
    #         line.add_class('cursor_line')
    #     except Exception:
    #         pass
        
    # def reload_lines(self):
    #     super().reload_lines()
    #     line = self.query_one(f'#code_line_{self.cursor_line}')
    #     line.add_class('cursor_line')
        
    # def action_do_step(self):
    #     print(self.debugger.current_bp.file, self.debugger.current_bp.line)
    #     self.debugger.set_step()
    #     print(self.debugger.current_bp.file, self.debugger.current_bp.line)
    #     self.update_current_line(self.debugger.current_bp.line)
        
    # def action_do_step(self):
    #     self.debugger.set_step()
    #     # self.update_current_line(self.debugger.current_frame.f_lineno)
    #     self.app.exit()
        
    # def action_do_next(self):
    #     # print(self.debugger.current_frame)
    #     # print(self.debugger.current_bp.file, self.debugger.current_frame.f_lineno)
    #     # print(self.debugger.set_next())
    #     # print(self.debugger.current_bp.file, self.debugger.current_frame.f_lineno)
    #     # print(self.app._driver)
    #     self.debugger.set_next()
    #     # self.update_current_line(self.debugger.current_frame.f_lineno)
    #     self.app.exit()

    

    # def watch_has_focus(self, has_focus):
    #     if has_focus:
    #         self.lines[self.cursor_line].add_class('cursor_line')
    #     else:
    #         self.lines[self.cursor_line].remove_class('cursor_line')
        
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
        VariableView {
            overflow-x: hidden;
        }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debugger: Debugger = self.app.debugger
        self.show_root = False
        self.guide_depth = 2
        
        self.show_level = 0
        self.old_cursor_line = 0
        
        PRIVATE_VAR_PATTERN = re.compile(r'^__.*__$')
        for key, val in self.debugger.current_frame.f_locals.items():
            if not PRIVATE_VAR_PATTERN.match(key):
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

    def watch_has_focus(self, has_focus):
        if has_focus:
            self.cursor_line = self.old_cursor_line
        else:
            self.old_cursor_line = self.cursor_line
            self.cursor_line = -1

    def validate_cursor_line(self, value: int) -> int:
        """Prevent cursor line from going outside of range.

        Args:
            value: The value to test.

        Return:
            A valid version of the given value.
        """
        return clamp(value, -1, len(self._tree_lines) - 1)

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
        
class StackView(Navigatable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lines = []
        stack, _ = self.debugger.get_stack(self.debugger.current_frame, None)
        for frame, line in stack:
            self.lines.append(f"{frame.f_code.co_filename}: {frame.f_lineno}")