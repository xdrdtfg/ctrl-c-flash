# -*- coding: utf-8 -*-
"""颜色主题与动画方案定义"""

# (key, 显示名, 颜色序列)
THEMES = [
    ("rainbow", "彩虹流光", ["#FF0057", "#FF8A00", "#FFE600", "#2BFF88", "#00D9FF", "#7B5CFF", "#FF28C8"]),
    ("aurora", "北极极光", ["#00FFC6", "#00C2FF", "#5B8CFF", "#B36BFF", "#00FFC6"]),
    ("neon", "霓虹果冻", ["#00FFF0", "#00A2FF", "#B400FF", "#FF2BD6", "#00FFF0"]),
    ("fire", "烈焰熔岩", ["#FFF200", "#FFB300", "#FF4D00", "#C10000", "#FFB300"]),
    ("gold", "鎏金", ["#FFE27A", "#FFC02E", "#C89000", "#FFD54A", "#FFE27A"]),
    ("ice", "冰霜", ["#EAF9FF", "#7FD4FF", "#2FA8F0", "#0055A8", "#7FD4FF"]),
    ("candy", "糖果粉", ["#FFC2E2", "#FF5FA2", "#C13BFF", "#6B5BFF", "#FF5FA2"]),
    ("matrix", "矩阵绿", ["#B8FFD0", "#4DFF88", "#00C853", "#00601F", "#4DFF88"]),
    ("cyber", "赛博紫电", ["#F0D0FF", "#C24BFF", "#7B2BFF", "#1E6BFF", "#F0D0FF"]),
    ("custom", "自定义渐变", None),
]

THEME_MAP = {k: (name, cols) for k, name, cols in THEMES}


def theme_colors(cfg):
    key = cfg.get("theme", "rainbow")
    if key == "custom":
        cols = cfg.get("custom_colors") or ["#FF2D75", "#00C2FF"]
        if len(cols) < 2:
            cols = ["#FF2D75", "#00C2FF"]
        return cols
    cols = THEME_MAP.get(key, THEME_MAP["rainbow"])[1]
    return cols


def theme_name(key):
    return THEME_MAP.get(key, ("未知", None))[0]


IN_ANIMS = [
    ("spray", "缩放冲入"),
    ("rotate", "旋转飞入"),
    ("fade", "淡入浮现"),
    ("blink", "闪烁登场"),
    ("bounce", "弹性弹跳"),
    ("slam", "雷霆砸落"),
]

OUT_ANIMS = [
    ("fade", "淡出消失"),
    ("expand", "放大消散"),
    ("shrink", "缩小消失"),
    ("spin", "旋转飞出"),
    ("blink", "闪烁熄灭"),
    ("float", "上飘消散"),
]

IN_MAP = dict(IN_ANIMS)
OUT_MAP = dict(OUT_ANIMS)

FONT_WEIGHTS = [
    ("normal", "常规"),
    ("bold", "加粗"),
    ("black", "特粗"),
]
