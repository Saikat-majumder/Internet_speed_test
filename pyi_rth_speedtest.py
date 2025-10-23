# PyInstaller Runtime Hook for speedtest-cli compatibility + Windows Taskbar Icon Fix
# Save this file as: pyi_rth_speedtest.py

import sys
import os

# Fix 1: Windows Taskbar Icon - Set App User Model ID
try:
    import ctypes
    myappid = 'saikatmajumder.internetspeedtest.1.0'  # Unique app ID
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

# Fix 2: Add builtins as __builtin__ for Python 3
if sys.version_info[0] >= 3:
    import builtins
    sys.modules['__builtin__'] = builtins

# Fix 3: Ensure stdout/stderr have fileno() method
class FileDescriptorWrapper:
    """Wrapper to add fileno() method to file-like objects"""
    def __init__(self, wrapped):
        self._wrapped = wrapped
    
    def fileno(self):
        try:
            return self._wrapped.fileno()
        except (AttributeError, OSError, IOError):
            return -1
    
    def __getattr__(self, name):
        return getattr(self._wrapped, name)

# Only wrap if needed
if sys.stdout is not None and not hasattr(sys.stdout, 'fileno'):
    sys.stdout = FileDescriptorWrapper(sys.stdout)

if sys.stderr is not None and not hasattr(sys.stderr, 'fileno'):
    sys.stderr = FileDescriptorWrapper(sys.stderr)

# Fix 4: Handle cases where stdout/stderr are None
if sys.stdout is None:
    class DummyOutput:
        def write(self, s): pass
        def flush(self): pass
        def fileno(self): return 1
        def isatty(self): return False
    sys.stdout = DummyOutput()

if sys.stderr is None:
    class DummyOutput:
        def write(self, s): pass
        def flush(self): pass
        def fileno(self): return 2
        def isatty(self): return False
    sys.stderr = DummyOutput()