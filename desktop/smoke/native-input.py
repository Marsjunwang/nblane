"""Send real X11 events to disposable desktop smoke windows, never DOM/CDP events."""

import ctypes
import sys
import time

x11 = ctypes.CDLL('libX11.so.6')
xtest = ctypes.CDLL('libXtst.so.6')
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XFlush.argtypes = [ctypes.c_void_p]
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
x11.XKeysymToKeycode.restype = ctypes.c_uint
xtest.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
xtest.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
xtest.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
display = x11.XOpenDisplay(None)
if not display:
    raise RuntimeError('Native input requires a working X11 DISPLAY; CDP fallback is not allowed')

def flush():
    x11.XFlush(display)
    time.sleep(0.08)

try:
    if sys.argv[1:] == ['escape']:
        key = x11.XKeysymToKeycode(display, 0xFF1B)
        if not key:
            raise RuntimeError('X11 Escape key is unavailable')
        xtest.XTestFakeKeyEvent(display, key, True, 0)
        flush()
        xtest.XTestFakeKeyEvent(display, key, False, 0)
        flush()
    elif len(sys.argv) == 4 and sys.argv[1] == 'click':
        xtest.XTestFakeMotionEvent(display, -1, int(sys.argv[2]), int(sys.argv[3]), 0)
        flush()
        xtest.XTestFakeButtonEvent(display, 1, True, 0)
        flush()
        xtest.XTestFakeButtonEvent(display, 1, False, 0)
        flush()
    else:
        raise ValueError('Usage: native-input.py click <x> <y> | escape')
finally:
    x11.XCloseDisplay(display)
