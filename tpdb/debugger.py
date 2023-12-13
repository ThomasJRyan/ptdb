import bdb
import sys
import time
import inspect

import asyncio

from types import FrameType
from typing import Union

from tpdb.tpdb import tPDBApp

class Debugger(bdb.Bdb):
    def __init__(self):
        bdb.Bdb.__init__(self)
        self.breakpoints = {}
        self.app_cls = tPDBApp
        self.app = self.app_cls(self)
        # self._wait_for_mainpyfile = False
        # bdb.Breakpoint.__init__(self)
        # self.stack, self.curindex = self.get_stack(f, tb)
        self.current_frame = None
        self.stack = None
        self.current_index = None
        self._quit = False
        
    @property
    def app(self):
        if self._app.exit:
            self.app = self.app_cls(self)
            return self._app
        return self._app
    
    @app.setter
    def app(self, app):
        self._app = app
        
    def interaction(self, frame: FrameType, traceback = None):
        # self.app._exit = False
        self.current_frame = frame
        if not self._quit:
            self.app.run()
        
    def user_call(self, frame: FrameType, argument_list: None) -> None:
        return super().user_call(frame, argument_list)
    
    def user_line(self, frame: FrameType) -> None:
        """This function is called when we stop or break at this line."""
        ...
        if frame.f_lineno > 20:
            return
        if (frame.f_code.co_filename, frame.f_lineno) in self.breakpoints:
            print('breakpoint', frame)
            # self.interaction(frame, None)
        # if self.stop_here(frame):
        #     print('stop_here', frame)
            # self.interaction(frame, None)
        # if self._wait_for_mainpyfile:
        # print(self.break_here(frame))
        # if (self.mainpyfile != self.canonic(frame.f_code.co_filename)
        #     or frame.f_lineno <= 0):
        #     return
        # self._wait_for_mainpyfile = False
        # if self.bp_commands(frame):
        #     self.interaction(frame, None)
        # print(self.break_here(frame))
        self.set_break(frame.f_code.co_filename, frame.f_lineno)
        print(frame)
        print(self.break_here(frame))
        
        self.interaction(frame)
        
        # app = tPDBApp()
        # app.run()
        # import multiprocessing
        # t = multiprocessing.Process(target=self.app.run)
        # t.start()
        
        # self.app.run()
        
        # self.app.run()
        
        # sys.exit(0)
        # raise bdb.BdbQuit
        # bdb.Bdb.reset(self)
        # return super().user_line(frame)
        # (filename, lineno, _, _, _) = inspect.getframeinfo(frame)
        # print(filename, lineno)
        # print(self.break_here(frame))
        
    def set_step(self):
        self.current_frame = self.stack[self.current_index][0]
        return super().set_step()
    
    def set_next(self):
        self.current_frame = self.stack[self.current_index][0]
        return super().set_next(self.current_frame)
    
    def set_return(self) -> None:
        self.current_frame = self.stack[self.current_index][0]
        return super().set_return(self.current_frame)
        
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
        
    # def dispatch_line(self, frame):
    #     if self.stop_here(frame) or self.break_here(frame):
    #         self.user_line(frame)
    #         if self.quitting:
    #             raise bdb.BdbQuit
    #         # Do not re-install the local trace when we are finished debugging,
    #         # see issues 16482 and 7238.
    #         if not sys.gettrace():
    #             return None
    #     return self.trace_dispatch
    
    def user_return(self, frame: FrameType, return_value: None) -> None:
        return super().user_return(frame, return_value)
    
    def user_exception(self, frame: FrameType, exception: Exception) -> None:
        return super().user_exception(frame, exception)
    
    def set_trace(self, frame=None, as_breakpoint=None, paused=True):
        """Start debugging from frame.

        If frame is not specified, debugging starts from caller's frame.
        """
        # filename = self.canonic(frame.f_code.co_filename)
        # line_no = frame.f_lineno
        # self.set_breakpoint(filename, line_no)
        
        if as_breakpoint is None:
            as_breakpoint = paused
        
        if frame is None:
            frame = sys._getframe().f_back
        self.reset()
        
        self.current_frame = frame
        self.stack, self.current_index = self.get_stack(frame, None)
        while frame:
            print('set_trace', frame)
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
            
        
        if as_breakpoint:
            self.set_break(self.current_frame.f_code.co_filename, self.current_frame.f_lineno)
            # self.current_bp = self.get_break(current_frame.f_code.co_filename, current_frame.f_lineno)
            self.current_bp = bdb.Breakpoint.bpbynumber[-1]
            self.app.run()
            # self.app.action_quit()
            
        self.set_step()
        sys.settrace(self.trace_dispatch)
            
    
    # def set_trace(self, frame: Union[FrameType, None] = None) -> None:
    #     print(frame.f_code.co_filename, frame.f_lineno)
    #     # bdb.Breakpoint(frame.f_code.co_filename, frame.f_lineno)
    #     print(self.break_here(frame))
        
    #     self.set_break(frame.f_code.co_filename, frame.f_lineno)
        
    #     print(self.break_here(frame))
        
    #     super().set_trace(frame)
        
    #     app = tPDBApp()
    #     app.run()
        
    
    #     self.breakpoints = {}
    #     self.set_trace()
        
    # def set_breakpont(self, filename, lineno, method):
    #     self.set_break(filename, lineno)
    #     try:
    #         self.breakpoints[(filename, lineno)].add(method)
    #     except KeyError:
    #         self.breakpoints[(filename, lineno)] = {method}
        
    # def user_line(self, frame: FrameType) -> None:
    #     if not self.break_here(frame):
    #         return
        
    #     (filename, lineno, _, _, _) = inspect.getframeinfo(frame)
        
    #     methods = self.breakpoints.get((filename, lineno), set())
    #     for method in methods:
    #         method(frame)
        
    # def set_trace(self, frame = None):
    #     if frame:
    #         current_frame = frame
    #     else:
    #         current_frame = frame = sys._getframe().f_back
        
    #     while frame:
    #         frame.f_trace = self.trace_dispatch
    #         self.botframe = frame
    #         frame = frame.f_back
            
    #     frame_info = (
    #             self.canonic(
    #                 current_frame.f_code.co_filename), 
    #                 current_frame.f_lineno)    
        
    #     self.breakpoints[frame_info] = True
        
    #     # self.reset()
    #     self.set_step()
        
    #     sys.settrace(self.trace_dispatch)