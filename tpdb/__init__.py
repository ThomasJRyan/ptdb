import sys
from tpdb.debugger import Debugger

def set_trace():
    debugger = Debugger()
    # debugger.app.run()
    # debugger.set_break(sys._getframe().f_back.f_code.co_filename, sys._getframe().f_back.f_lineno)
    debugger.set_trace(sys._getframe().f_back)