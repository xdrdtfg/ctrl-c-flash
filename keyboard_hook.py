# -*- coding: utf-8 -*-
"""
全局低级键盘钩子（WH_KEYBOARD_LL）

在钩子回调里只做「判断 + 记录坐标 + 塞进队列」这三件极轻的事，
绝不做任何 UI 操作，避免超过系统的 LowLevelHooksTimeout 被静默摘钩。
真正的动画播放交给主线程的定时器去消费队列。
"""

import ctypes
import time
import threading
from collections import deque
from ctypes import wintypes

from cursor_probe import get_anchor_pos

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

VK_C = 0x43
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p, wintypes.DWORD]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = ctypes.c_void_p


class CopyKeyWatcher:
    """监听 Ctrl+C，把触发事件放进线程安全队列。"""

    def __init__(self, on_trigger=None, debounce=0.25):
        self.on_trigger = on_trigger
        self.debounce = debounce
        self.events = deque()
        self._lock = threading.Lock()
        self._hook = None
        self._proc = None
        self.running = False
        self._last_fire = 0.0
        self.trigger_count = 0
        # 触发时的原始信息，可在主线程取用
        self.last_trigger = None

    # ---------- 钩子 ----------
    def _callback(self, n_code, w_param, l_param):
        try:
            if n_code == 0 and w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if kb.vkCode == VK_C:
                    ctrl = user32.GetAsyncKeyState(VK_CONTROL) & 0x8000
                    alt = user32.GetAsyncKeyState(VK_MENU) & 0x8000
                    if ctrl and not alt:
                        now = time.monotonic()
                        if now - self._last_fire >= self.debounce:
                            self._last_fire = now
                            # 坐标在按键瞬间取，避免之后鼠标移开
                            pos, source = get_anchor_pos(True)
                            self.trigger_count += 1
                            self.last_trigger = (pos, source, now)
                            with self._lock:
                                self.events.append((pos, source, now))
        except Exception:
            pass
        return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

    def start(self):
        if self.running:
            return True
        self._proc = HOOKPROC(self._callback)
        hmod = kernel32.GetModuleHandleW(None)
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, hmod, 0)
        self.running = bool(self._hook)
        return self.running

    def stop(self):
        if self._hook:
            try:
                user32.UnhookWindowsHookEx(self._hook)
            except Exception:
                pass
        self._hook = None
        self._proc = None
        self.running = False

    # ---------- 队列 ----------
    def pop_events(self):
        with self._lock:
            if not self.events:
                return []
            items = list(self.events)
            self.events.clear()
        return items
