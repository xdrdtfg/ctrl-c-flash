# -*- coding: utf-8 -*-
"""配置读写：JSON 持久化到 %APPDATA%\\CtrlCFlash\\config.json"""

import copy
import json
import os
import sys

import i18n

APP_NAME = "CtrlCFlash"

DEFAULTS = {
    "enabled": True,
    # 外观
    "theme": "rainbow",
    "custom_colors": ["#FF2D75", "#00C2FF"],
    "font_family": "Microsoft YaHei",
    "font_weight": "black",
    "start_size": 46,
    "peak_size": 168,
    "opacity": 100,
    "glow": 14,
    "shockwave": False,
    "flow_speed": 1.0,
    # 界面
    "ui_mode": "dark",
    "language": "",  # 空 = 跟随系统，首次启动自动判定后写回 zh / en
    # 动画
    "in_anim": "spray",
    "out_anim": "expand",
    "in_ms": 260,
    "hold_ms": 240,
    "out_ms": 460,
    # 行为
    "prefer_caret": True,
    "autostart": False,
}


def config_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def config_path():
    return os.path.join(config_dir(), "config.json")


def load():
    cfg = copy.deepcopy(DEFAULTS)
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for k, v in data.items():
                if k in cfg:
                    cfg[k] = v
    except FileNotFoundError:
        pass
    except Exception:
        # 配置损坏时回到默认值，不让它把程序拖垮
        pass
    return sanitize(cfg)


def save(cfg):
    tmp = config_path() + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, config_path())
    except Exception:
        pass


def sanitize(cfg):
    """数值夹紧，防止异常配置把窗口画崩。"""
    def clamp(v, lo, hi, default):
        try:
            v = int(v)
        except Exception:
            return default
        return max(lo, min(hi, v))

    cfg["start_size"] = clamp(cfg.get("start_size"), 8, 400, 46)
    cfg["peak_size"] = clamp(cfg.get("peak_size"), 20, 600, 168)
    if cfg["peak_size"] < cfg["start_size"]:
        cfg["peak_size"] = cfg["start_size"]
    cfg["opacity"] = clamp(cfg.get("opacity"), 10, 100, 100)
    cfg["glow"] = clamp(cfg.get("glow"), 0, 40, 14)
    cfg["in_ms"] = clamp(cfg.get("in_ms"), 40, 2000, 260)
    cfg["hold_ms"] = clamp(cfg.get("hold_ms"), 0, 3000, 240)
    cfg["out_ms"] = clamp(cfg.get("out_ms"), 40, 3000, 460)

    colors = cfg.get("custom_colors")
    if not isinstance(colors, list) or len(colors) < 2:
        cfg["custom_colors"] = list(DEFAULTS["custom_colors"])

    try:
        cfg["flow_speed"] = max(0.0, min(3.0, float(cfg.get("flow_speed", 1.0))))
    except Exception:
        cfg["flow_speed"] = 1.0

    if cfg.get("ui_mode") not in ("light", "dark"):
        cfg["ui_mode"] = "dark"
    if cfg.get("language") not in ("zh", "en"):
        cfg["language"] = i18n.detect_language()
    return cfg


def set_autostart(enable):
    """通过 HKCU Run 项实现开机自启。返回是否成功。"""
    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}"'
                else:
                    cmd = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def is_autostart_enabled():
    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_QUERY_VALUE) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except Exception:
        return False
