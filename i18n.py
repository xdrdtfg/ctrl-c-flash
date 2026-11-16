# -*- coding: utf-8 -*-
"""界面语言包：简体中文 / English

所有对用户可见的文案都从这里取。键名统一用 "区域.名称"，
值为 (中文, English) 二元组，t() 按当前语言选一条返回。
"""

LANGS = [("zh", "简体中文"), ("en", "English")]
LANG_NAME = dict(LANGS)

_current = "zh"

# (中文, English)
STRINGS = {
    # ---------- 通用 / 托盘 ----------
    "app.title": ("Ctrl+C 雷霆大C", "Ctrl+C Thunder C"),
    "app.display": ("雷霆大 C", "Thunder C"),
    "app.window": ("Ctrl+C 雷霆大C · 设置", "Ctrl+C Thunder C · Settings"),
    "app.sub": ("Ctrl+C 复制特效 · 设置", "Ctrl+C copy flash · Settings"),
    "app.version": ("Ctrl+C 雷霆大 C   v1.0.0", "Ctrl+C Thunder C   v1.0.0"),

    "tray.tip": (
        "Ctrl+C 雷霆大C\n左键单击：预览   右键：菜单",
        "Ctrl+C Thunder C\nLeft click: preview   ·   Right click: menu",
    ),
    "tray.enable": ("启用复制特效", "Enable copy flash"),
    "tray.preview": ("预览效果", "Preview"),
    "tray.settings": ("设置…", "Settings…"),
    "tray.autostart": ("开机自动启动", "Start with Windows"),
    "tray.quit": ("退出", "Quit"),

    "msg.autostart_fail": (
        "写入开机启动项失败，可能被系统权限拦截。",
        "Could not write the startup entry — it may be blocked by system permissions.",
    ),
    "msg.hook_fail": (
        "全局按键监听启动失败，可能是被安全软件拦截。复制特效将无法触发。",
        "Global key hook failed to start — likely blocked by security software. "
        "The copy flash will not trigger.",
    ),
    "msg.welcome": (
        "已经在后台跑起来了。如果任务栏右下角没看到彩色的 C 图标，"
        "点一下时间旁边的 ^ 展开隐藏图标，把它拖出来就行。\n"
        "然后随便复制点什么试试。",
        "Up and running in the background. If you don't see the colored C near the clock, "
        "click the ^ arrow to show hidden icons and drag it out.\n"
        "Then copy something and watch.",
    ),

    # ---------- 页签 ----------
    "tab.look": ("外观", "Look"),
    "tab.anim": ("动画", "Motion"),
    "tab.misc": ("其它", "Other"),

    # ---------- 外观页 ----------
    "look.preview": ("实时预览", "LIVE PREVIEW"),
    "card.color": ("颜色", "Color"),
    "card.glyph": ("字形", "Glyph"),
    "field.theme": ("炫彩样式", "Style"),
    "field.custom": ("自定义两色", "Custom"),
    "field.flow": ("流光速度", "Flow"),
    "field.font": ("字体", "Font"),
    "field.weight": ("字重", "Weight"),
    "field.start": ("起始大小", "Start"),
    "field.peak": ("最大大小", "Peak"),
    "field.opacity": ("不透明度", "Opacity"),
    "field.glow": ("辉光强度", "Glow"),
    "hint.swatch": ("点色块可改色", "Click a swatch to recolor"),

    # ---------- 动画页 ----------
    "card.motion": ("动作方式", "Motion"),
    "card.timing": ("节奏", "Timing"),
    "card.preset": ("快捷风格", "Presets"),
    "card.extra": ("额外效果", "Extras"),
    "field.in": ("出现方式", "Enter"),
    "field.out": ("消失方式", "Exit"),
    "field.in_ms": ("出现时长", "Enter ms"),
    "field.hold_ms": ("停留时长", "Hold ms"),
    "field.out_ms": ("消失时长", "Exit ms"),
    "preset.light": ("轻盈", "Subtle"),
    "preset.standard": ("标准", "Standard"),
    "preset.bold": ("夸张", "Dramatic"),
    "chk.ripple": ("出现时带一圈向外扩散的光晕", "Ripple ring on appear"),
    "hint.duration": (
        "整套动画总时长最好别超过 1.5 秒，太久了会挡住视线。",
        "Keep the whole sequence under ~1.5 s — anything longer gets in the way.",
    ),

    # ---------- 其它页 ----------
    "card.lang": ("语言", "Language"),
    "field.lang": ("界面", "Interface"),
    "card.behavior": ("行为", "Behavior"),
    "chk.enabled": ("启用复制特效", "Enable the copy flash"),
    "chk.caret": ("优先定位到文字光标（关闭则跟随鼠标位置）",
                  "Anchor at the text caret (off: follow the mouse)"),
    "chk.autostart": ("开机自动启动", "Start with Windows"),
    "card.about": ("说明", "How it works"),
    "about.intro": (
        "常驻后台监听全局 Ctrl+C，触发时读取系统插入符坐标，"
        "在那一瞬间的位置画一个渐变的大 C，播完自动消失。",
        "Sits in the tray and listens for Ctrl+C. On a copy it reads the system caret "
        "position, paints a gradient C there, then fades away.",
    ),
    "about.b1": ("·  左键单击托盘图标 = 预览效果", "·  Left click the tray icon = preview"),
    "about.b2": ("·  右键托盘图标 = 菜单 / 设置", "·  Right click the tray icon = menu / settings"),
    "about.b3": (
        "·  有些程序不给系统暴露光标位置，这时会退回到鼠标处",
        "·  Some apps never expose their caret — the flash falls back to the mouse",
    ),
    "card.info": ("关于", "About"),
    "btn.open_dir": ("打开配置文件夹", "Open config folder"),

    # ---------- 底部与提示 ----------
    "footer.tip": ("改动即时生效，不用保存", "Changes apply instantly — nothing to save"),
    "btn.reset": ("恢复默认", "Reset"),
    "btn.preview": ("预览动画", "Preview"),
    "btn.close": ("关闭", "Close"),
    "tip.min": ("最小化", "Minimize"),
    "tip.close": ("关闭", "Close"),
    "tip.mode": ("切换浅色 / 深色界面", "Switch light / dark"),
    "tip.custom_pick": ("点击即可换成自定义色", "Click to use your custom color"),
    "tip.custom_edit": ("点击修改颜色", "Click to edit the color"),
    "dlg.pick_color": ("选择颜色", "Pick a color"),

    # ---------- 主题 ----------
    "theme.rainbow": ("彩虹流光", "Rainbow flow"),
    "theme.aurora": ("北极极光", "Aurora"),
    "theme.neon": ("霓虹果冻", "Neon jelly"),
    "theme.fire": ("烈焰熔岩", "Molten"),
    "theme.gold": ("鎏金", "Gilded"),
    "theme.ice": ("冰霜", "Frost"),
    "theme.candy": ("糖果粉", "Candy"),
    "theme.matrix": ("矩阵绿", "Matrix"),
    "theme.cyber": ("赛博紫电", "Cyber violet"),
    "theme.custom": ("自定义渐变", "Custom gradient"),

    # ---------- 入场动画 ----------
    "anim_in.spray": ("缩放冲入", "Zoom in"),
    "anim_in.rotate": ("旋转飞入", "Spin in"),
    "anim_in.fade": ("淡入浮现", "Fade in"),
    "anim_in.blink": ("闪烁登场", "Blink in"),
    "anim_in.bounce": ("弹性弹跳", "Bounce in"),
    "anim_in.slam": ("雷霆砸落", "Slam in"),

    # ---------- 出场动画 ----------
    "anim_out.fade": ("淡出消失", "Fade out"),
    "anim_out.expand": ("放大消散", "Expand out"),
    "anim_out.shrink": ("缩小消失", "Shrink out"),
    "anim_out.spin": ("旋转飞出", "Spin out"),
    "anim_out.blink": ("闪烁熄灭", "Blink out"),
    "anim_out.float": ("上飘消散", "Float up"),

    # ---------- 字重 ----------
    "weight.normal": ("常规", "Regular"),
    "weight.bold": ("加粗", "Bold"),
    "weight.black": ("特粗", "Heavy"),
}


def detect_language():
    """跟随系统：Windows 界面语言是中文就中文，否则英文。"""
    try:
        import ctypes

        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        if (langid & 0x3FF) == 0x04:  # LANG_CHINESE
            return "zh"
        return "en"
    except Exception:
        return "zh"


def normalize(lang):
    return lang if lang in ("zh", "en") else detect_language()


def set_lang(lang):
    global _current
    _current = normalize(lang)
    return _current


def get_lang():
    return _current


def t(key, **fmt):
    pair = STRINGS.get(key)
    if pair is None:
        return key
    text = pair[0] if _current == "zh" else pair[1]
    if fmt:
        try:
            text = text.format(**fmt)
        except Exception:
            pass
    return text


def label(prefix, key):
    """theme.rainbow / anim_in.spray 这类拼出来的键，缺了就用原 key 兜底。"""
    return t(prefix + "." + str(key))
