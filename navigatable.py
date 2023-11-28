from typing import Any, Coroutine
from rich.syntax import Syntax, ANSISyntaxTheme, ANSI_DARK, SyntaxTheme

from textual.events import Resize, Event
from textual.widgets import Static
from textual.containers import VerticalScroll

class Line(Static):
    """A simple label widget for displaying text-oriented renderables."""

    DEFAULT_CSS = """
    Line {
        width: 100%;
        height: 1;
    }
    """


class Navigatable(VerticalScroll):
    
    DEFAULT_CSS = """    
    Navigatable .highlighted {
        background: rgb(0,128,255);
    }
    """
    
    def __init__(self, index: int = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lines = None
        self._index = index
        self._line_cursor = 0
        
    def set_lines(self, text: str, language: str = 'python', theme: SyntaxTheme = ANSISyntaxTheme, cursor_pos: int = 0):
        """Sets the lines

        Args:
            text (str): Text to split on newlines and set
            language (str, optional): Language to highlight. Defaults to 'python'.
            theme (SyntaxTheme, optional): Theme to use to highlight. Defaults to ANSISyntaxTheme.
            cursor_pos (int, optional): Cursor position to start at. Defaults to 0
        """
        syntax_highlighter = Syntax('', language, theme=theme(ANSI_DARK))
        highlighted_text = syntax_highlighter.highlight(text)
        self.lines = highlighted_text.split()
        
        # Remove children and update lines
        self.remove_children()
        self.update_line_range()
        for i in range(self.start, self.end):
            self.mount(Line(self.lines[i]))
            
        self._index = cursor_pos
        self.reload_lines()
        
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
        
        for cur_pos, i in enumerate(range(self.start, self.end)):
            if id(self.lines[i]) == id(current_line):
                self._line_cursor = cur_pos
            self.mount(Line(self.lines[i]))
            
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
            self.mount(Line(self.lines[self._index]))
            self.children[0].remove()
            self.end += direction
            self.start += direction
            return True
        # Move Up
        elif self._index < self.start:
            self.mount(Line(self.lines[self._index]), before=0)
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
        
    def action_scroll_down(self) -> None:
        """Scroll the text down"""
        if not self.lines:
            return
        if self._index + 1 < len(self.lines):
            self.update_cursor(1)
            self.refresh(layout=True)
        print(f'{self._index=}, {self._line_cursor=}, {self.start=}, {self.end=}, {self.height=}, {len(self.children)}')
            
    def action_scroll_up(self) -> None:
        """Scroll the text up"""
        if not self.lines:
            return
        if self._index - 1 >= 0:
            self.update_cursor(-1)
            self.refresh(layout=True)
        print(f'{self._index=}, {self._line_cursor=}, {self.start=}, {self.end=}, {self.height=}, {len(self.children)}')
        
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
        
class CodeNavigation(Navigatable):
    
    BINDINGS = [
        ('s', 'set_text', 'Set Text')
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def action_set_text(self):
        with open('navigatable.py') as fil:
            self.set_lines(fil.read(), cursor_pos=100)