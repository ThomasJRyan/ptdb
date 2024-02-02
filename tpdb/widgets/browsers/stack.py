
from __future__ import annotations

import inspect

from pathlib import Path
from inspect import FrameInfo

from rich.text import Text
from rich.syntax import Syntax, ANSISyntaxTheme, ANSI_DARK, SyntaxTheme
from textual.strip import Strip

from textual.widgets import OptionList
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets.option_list import Option, Separator


class StackBrowser(OptionList):
    stack = reactive([])
    
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.stack = inspect.stack()
        
    def watch_stack(self, stack):
        self.clear_options()
        for frame_info in stack:
            self.add_option(self._format_frame(frame_info))
            
    def _format_frame(self, frame_info: FrameInfo):
        name = frame_info.frame.f_code.co_name or None
        
        try:
            class_name = frame_info.frame.f_locals["self"].__class__.__name__
        except Exception:
            class_name = None
        
        filename = Path(frame_info.filename).name or None
        lineno = frame_info.lineno or None
        
        ret_str = ""
        
        if name: 
            ret_str += f"{name} "
        if class_name: 
            ret_str += f"{class_name} "
        if filename: 
            ret_str += f"{filename}:"
        if lineno: 
            ret_str += f"{lineno}"
            
        return ret_str
        
    