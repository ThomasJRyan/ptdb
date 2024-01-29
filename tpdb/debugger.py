import os
import bdb
import sys
import time
import inspect

import asyncio

from types import FrameType, TracebackType
from typing import Union

from tpdb.tpdb import tPDBApp

class Debugger(bdb.Bdb):
    """The debugger that runs tPDB"""
    def __init__(self):
        """Initializes the tPDB class"""
        bdb.Bdb.__init__(self)
        
        # Store our breakpoints in a dict for easy toggling
        self.breakpoints = {}
        
        # Keep a reference to our Textual app for create/teardown purposes
        self.app_cls = tPDBApp
        # Create an instance of the app
        self.app = self.app_cls(self)
        
        # Set some variables for use
        self.current_frame = None
        self.current_index = None
        self.stack = None
        self._quit = False
        
    #------------------------------------------------
    #                Properties
    #------------------------------------------------
        
    @property
    def app(self) -> tPDBApp:
        """Returns the tPDB app. Creates a new instance if we've exited it

        Returns:
            tPDBApp: The tPDB app
        """
        if self._app.exit:
            self.app = self.app_cls(self)
            return self._app
        return self._app
    
    @app.setter
    def app(self, app):
        """Set the app"""
        self._app = app
        
    @property
    def filepath(self) -> str:
        """The canonical filepath of the current frame

        Returns:
            str: The canonical filepath of the current frame
        """
        frame_ins = inspect.getframeinfo(self.current_frame)
        return os.path.realpath(frame_ins.filename)
    
    @property
    def lineno(self) -> int:
        """The current frame's line number

        Returns:
            int: The current frame's line number
        """
        frame_ins = inspect.getframeinfo(self.current_frame)
        return frame_ins.lineno
        
    #------------------------------------------------
    #                bdb functions
    #------------------------------------------------    
    
    def interaction(self, frame: FrameType, traceback: TracebackType = None):
        """Called after each line. Defines what we're going to do next
        Usually this is just re-running the app

        Args:
            frame (FrameType): Next frame to execute
            traceback (TracebackType, optional): Traceback information. Defaults to None.
        """
        self.current_frame = frame
        if not self._quit:
            self.app.run()
        
    def user_call(self, frame: FrameType, argument_list: None) -> None:
        return super().user_call(frame, argument_list)
    
    def user_line(self, frame: FrameType) -> None:
        """This function is called when we stop or break at this line."""
        self.set_break(frame.f_code.co_filename, frame.f_lineno)
        self.interaction(frame)
        
    def user_return(self, frame: FrameType) -> None:
        self.set_break(frame.f_code.co_filename, frame.f_lineno)
        self.interaction(frame)
        
    def set_step(self):
        self.current_frame = self.stack[self.current_index][0]
        return super().set_step()
    
    def set_next(self):
        self.current_frame = self.stack[self.current_index][0]
        return super().set_next(self.current_frame)
    
    def set_return(self) -> None:
        self.current_frame = self.stack[self.current_index][0]
        return super().set_return(self.current_frame)
        
    #------------------------------------------------
    #                Custom functions
    #------------------------------------------------
        
    def set_breakpoint(self, filename: str, lineno: int) -> None:
        self.set_break(filename, lineno)
        self.breakpoints[(filename, lineno)] = True
        
    def clear_breakpoint(self, filename: str, lineno: int) -> None:
        self.clear_break(filename, lineno)
        if (filename, lineno) in self.breakpoints:
            del self.breakpoints[(filename, lineno)]
        
    def toggle_breakpoint(self, filename: str, lineno: int) -> None:
        if (filename, lineno) in self.breakpoints or lineno in self.breaks.get(filename, []):
            self.clear_breakpoint(filename, lineno)
        else:
            self.set_breakpoint(filename, lineno)
            
    def user_return(self, frame: FrameType, return_value: None) -> None:
        return super().user_return(frame, return_value)
    
    def user_exception(self, frame: FrameType, exception: Exception) -> None:
        return super().user_exception(frame, exception)
    
    def set_trace(self, frame=None, as_breakpoint=None, paused=True):
        """Start debugging from frame.

        If frame is not specified, debugging starts from caller's frame.
        """
        
        if as_breakpoint is None:
            as_breakpoint = paused
        
        if frame is None:
            frame = sys._getframe().f_back
        self.reset()
        
        self.current_frame = frame
        self.stack, self.current_index = self.get_stack(frame, None)
        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
        
        if as_breakpoint:
            self.set_break(self.current_frame.f_code.co_filename, self.current_frame.f_lineno)
            self.current_bp = bdb.Breakpoint.bpbynumber[-1]
            self.app.run()
            
        self.set_step()
        sys.settrace(self.trace_dispatch)