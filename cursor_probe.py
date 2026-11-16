# -*- coding: utf-8 -*-
"""
光标 / 插入符定位

优先拿到文本插入符（caret）的屏幕坐标，这样大 C 会正好出现在
正在被复制的文字光标处；拿不到时退回鼠标指针位置。
"""

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
user32.GetGUIThreadInfo.restype = wintypes.BOOL
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.ClientToScreen.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL


def get_caret_pos():
    """返回文本插入符屏幕坐标 (x, y)（物理像素），失败返回 None。"""
    try:
        hwnd_fg = user32.GetForegroundWindow()
        if not hwnd_fg:
            return None
        tid = user32.GetWindowThreadProcessId(hwnd_fg, None)
        if not tid:
            return None

        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if not user32.GetGUIThreadInfo(tid, ctypes.byref(info)):
            return None

        rc = info.rcCaret
        if not info.hwndCaret or (rc.left == 0 and rc.top == 0 and rc.right == 0 and rc.bottom == 0):
            return None

        pt = wintypes.POINT(rc.left, rc.bottom)
        if not user32.ClientToScreen(info.hwndCaret, ctypes.byref(pt)):
            return None

        # 明显离屏的坐标视为无效
        if pt.x <= -30000 or pt.y <= -30000:
            return None
        return int(pt.x), int(pt.y)
    except Exception:
        return None


def get_mouse_pos():
    """鼠标指针屏幕坐标（物理像素）。"""
    pt = wintypes.POINT()
    if user32.GetCursorPos(ctypes.byref(pt)):
        return int(pt.x), int(pt.y)
    return None


def get_anchor_pos(prefer_caret=True):
    """综合定位：优先插入符，退化到鼠标位置。"""
    if prefer_caret:
        pos = get_caret_pos()
        if pos:
            return pos, "caret"
    pos = get_mouse_pos()
    if pos:
        return pos, "mouse"
    return (0, 0), "none"
