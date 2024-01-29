from __future__ import annotations

import re
import inspect

from types import ModuleType
from typing import TYPE_CHECKING

from textual.widgets import Tree
from textual.widgets.tree import TreeNode, TreeDataType
from textual.geometry import clamp


if TYPE_CHECKING:
    from tpdb.debugger import Debugger

class VariableBrowser(Tree):
    
    DEFAULT_CSS = """
        VariableBrowser {
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
            if PRIVATE_VAR_PATTERN.match(key):
                continue
            if isinstance(val, ModuleType):
                continue
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
            
    def _toggle_node(self, node: TreeNode[TreeDataType]) -> None:
        if not node.allow_expand:
            return
        
        print(self._updates)
        
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