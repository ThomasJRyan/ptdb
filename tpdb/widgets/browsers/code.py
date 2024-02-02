
from __future__ import annotations

from rich.text import Text
from rich.syntax import Syntax, ANSISyntaxTheme, ANSI_DARK, SyntaxTheme
from textual.strip import Strip

from textual.widgets import OptionList
from textual.binding import Binding
from textual.widgets.option_list import Option, Separator


class CodeLine(Option):
    def __init__(self, content: Text, length: int, id: str | None = None, disabled: bool = False):
        self.__line_no = Text(" {index:>{width}} ".format(index=content[0], width=length))
        self.__line = content[1]
        
        self.can_break = True
        if self.__line.plain.strip().startswith('#') or not self.__line.plain.strip():
            self.can_break = False
            
        self.__id = id
        self.disabled = disabled
        
        self.is_breakpoint = False
        self.__break_text = Text(' ')
        
        self.is_next_to_execute = False
        self.__execute_text = Text(' ')
    
    @property
    def prompt(self):
        text = self.__execute_text + self.__break_text + self.__line_no + self.__line
        return text
    
    @property
    def id(self) -> str | None:
        """The optional ID for the option."""
        return self.__id
    
    def set_break(self) -> None:
        if not self.can_break:
            return
        self.is_breakpoint = True
        self.__break_text = Text('*')
        
    def unset_break(self) -> None:
        self.is_breakpoint = False
        self.__break_text = Text(' ')
        
    def toggle_break(self) -> bool:
        if self.is_breakpoint:
            self.unset_break()
        else:
            self.set_break()
        return self.is_breakpoint
            
    def set_execute_next(self) -> None:
        if not self.can_break:
            return
        self.is_next_to_execute = True
        self.__execute_text = Text('>')
        
    def unset_execute_next(self) -> None:
        self.is_next_to_execute = False
        self.__execute_text = Text(' ')
        
    def toggle_execute_next(self) -> bool:
        if self.is_next_to_execute:
            self.unset_execute_next()
        else:
            self.set_execute_next()
        return self.is_next_to_execute
    

class CodeBrowser(OptionList):
    
    DEFAULT_CSS = """
    $breakpoint-highlight: red;
    $execute-highlight: limegreen;
    
    CodeBrowser {
        height: 100%;
    }
    
    CodeBrowser > .code-browser--breakpoint-highlighted {
        background: $breakpoint-highlight;
    }
    
    CodeBrowser > .code-browser--execute-highlighted {
        background: $execute-highlight;
    }
    
    """
    
    BINDINGS = [
        Binding("b", "set_break", "Set Breakpoint"),
        Binding("n", "do_next", "Next"),
        Binding("s", "do_step", "Step"),
        Binding("c", "do_continue", "Continue"),
    ]
    
    COMPONENT_CLASSES = [
        "code-browser--breakpoint-highlighted",
        "code-browser--execute-highlighted",
    ]
    
    class OptionBreak(OptionList.OptionMessage):
        ...
    
    def __init__(self, filepath: str, index: int = 0, language: str = 'python', theme: SyntaxTheme = ANSISyntaxTheme, *args, **kwargs):
        self.debugger = self.app.debugger
        
        lines = []
        self.filepath = filepath
        with open(filepath) as fil:
            text = fil.read()
            syntax_highlighter = Syntax('', language, theme=theme(ANSI_DARK))
            highlighted_text = syntax_highlighter.highlight(text)
            self.__lines = highlighted_text.split()
            lines = [(line_no, line) for line_no, line in enumerate(self.__lines, start=1)]
            
        super().__init__(*lines, *args, **kwargs)
        
        self.highlighted = index
        self._options[index].set_execute_next()
        
        for _filename, lineno in self.debugger.breakpoints:
            self._options[lineno - 1].set_break()
        
    
    def action_set_break(self) -> None:
        """Set breakpoint in the code"""
        highlighted = self.highlighted
        if highlighted is not None and not self._options[highlighted].disabled:
            self.post_message(self.OptionBreak(self, highlighted))
            
    def on_code_browser_option_break(self, option_break: OptionBreak, *args, **kwargs):
        option: CodeLine = option_break.option
        option.toggle_break()
        self.debugger.set_breakpoint(self.filepath, self.highlighted+1)
        self._refresh_content_tracking(force=True)
        self.refresh()
        
    def render_line(self, y: int) -> Strip:
        """Render a single line in the option list.

        Args:
            y: The Y offset of the line to render.

        Returns:
            A `Strip` instance for the caller to render.
        """

        scroll_x, scroll_y = self.scroll_offset

        # First off, work out which line we're working on, based off the
        # current scroll offset plus the line we're being asked to render.
        line_number = scroll_y + y
        try:
            line = self._lines[line_number]
        except IndexError:
            # An IndexError means we're drawing in an option list where
            # there's more list than there are options.
            return Strip([])

        # Now that we know which line we're on, pull out the option index so
        # we have a "local" copy to refer to rather than needing to do a
        # property access multiple times.
        option_index = line.option_index

        # Knowing which line we're going to be drawing, we can now go pull
        # the relevant segments for the line of that particular prompt.
        strip = line.segments

        # If the line we're looking at isn't associated with an option, it
        # will be a separator, so let's exit early with that.
        if option_index is None:
            return strip.apply_style(
                self.get_component_rich_style("option-list--separator")
            )

        # At this point we know we're drawing actual content. To allow for
        # horizontal scrolling, let's crop the strip at the right locations.
        strip = strip.crop(scroll_x, scroll_x + self.scrollable_content_region.width)

        highlighted = self.highlighted
        mouse_over = self._mouse_hovering_over
        spans = self._spans      

        # Handle drawing a highlighted option.
        if highlighted is not None and line_number in spans[highlighted]:
            # Highlighted with the mouse over it?
            if option_index == mouse_over:
                return strip.apply_style(
                    self.get_component_rich_style(
                        "option-list--option-hover-highlighted"
                    )
                )
            # Just a normal highlight.
            return strip.apply_style(
                self.get_component_rich_style("option-list--option-highlighted")
            )

            
        if self._options[option_index].is_breakpoint:
            return strip.apply_style(
                self.get_component_rich_style(
                    "code-browser--breakpoint-highlighted"
                )
            )
            
        if self._options[option_index].is_next_to_execute:
            return strip.apply_style(
                self.get_component_rich_style(
                    "code-browser--execute-highlighted"
                )
            )
            
        # Perhaps the line is within an otherwise-uninteresting option that
        # has the mouse hovering over it?
        if mouse_over is not None and line_number in spans[mouse_over]:
            return strip.apply_style(
                self.get_component_rich_style("option-list--option-hover")
            )

        # It's a normal option line.
        return strip.apply_style(self.rich_style)
        
        
    def _make_content(self, content):
        """Convert a single item of content for the list into a content type.

        Args:
            content: The content to turn into a full option list type.

        Returns:
            The content, usable in the option list.
        """
        if isinstance(content, (Option, Separator)):
            return content
        if content is None:
            return Separator()
        return CodeLine(content, len(str(len(self.__lines)))-1)
    
    def action_do_next(self):
        """Execute the next line"""
        self.debugger.do_next()
        self.app.exit()
        
    def action_do_step(self):
        """Step into the next line"""
        self.debugger.do_step()
        self.app.exit()
        
    def action_do_continue(self):
        self.debugger.do_continue()
        self.app.exit()