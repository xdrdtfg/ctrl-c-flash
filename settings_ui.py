# -*- coding: utf-8 -*-
"""设置界面：支持浅色 / 深色两套配色，所有改动即时生效并保存"""

import copy
import ctypes
import math
import os
import time

from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFontComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProxyStyle,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QStyle,
    QStyleFactory,
    QVBoxLayout,
    QWidget,
)

import cfg as cfgmod
import i18n
from i18n import t
from overlay import build_letter_path
from themes import FONT_WEIGHTS, IN_ANIMS, OUT_ANIMS, THEMES, theme_colors

WEIGHT_MAP = {
    "normal": QFont.Weight.Normal,
    "bold": QFont.Weight.Bold,
    "black": QFont.Weight.Black,
}

PRESETS = [
    ("preset.light", {"in_anim": "fade", "out_anim": "fade", "in_ms": 180, "hold_ms": 120, "out_ms": 300}),
    ("preset.standard", {"in_anim": "spray", "out_anim": "expand", "in_ms": 260, "hold_ms": 240, "out_ms": 460}),
    ("preset.bold", {"in_anim": "slam", "out_anim": "spin", "in_ms": 380, "hold_ms": 420, "out_ms": 720}),
]

# ---------------- 两套配色 ----------------

PALETTES = {
    "dark": {
        "bg": "#0A0A0C",
        "card": "#131316",
        "card_line": "#232429",
        "field": "#18191D",
        "field_line": "#2A2C33",
        "line": "#1F2025",
        "text": "#D9DBE1",
        "text_hi": "#F4F5F8",
        "text_mid": "#8B8E97",
        "text_low": "#5F626B",
        "accent": "#3F8CFF",
        "accent_hi": "#6EA8FF",
        "accent_dim": "#2563CC",
        "accent_soft": "rgba(63, 140, 255, 0.16)",
        "on_accent": "#FFFFFF",
        "track": "#26282F",
        "handle": "#F5F6F9",
        "handle_line": "none",
        "hover_bg": "#1D1F24",
        "hover_line": "#3A3D46",
        "cb_bg": "#1D1F24",
        "cb_line": "#3D414B",
        "cb_line_hover": "#5C6170",
        "tick": "#0A0A0C",
        "scroll": "#2E3038",
        "scroll_hi": "#3E414B",
        "popup": "#17181C",
        "popup_line": "#2C2F36",
        "tooltip_bg": "#1B1D22",
        "tooltip_line": "#33363E",
        "preview_a": "#1A1C22",
        "preview_b": "#08090B",
        "chevron": "#82868F",
        "shell_line": "#2C2F37",
        "dark": True,
    },
    "light": {
        "bg": "#EAF1FB",
        "card": "#FFFFFF",
        "card_line": "#DCE8F7",
        "field": "#F6FAFE",
        "field_line": "#D6E3F4",
        "line": "#DBE7F6",
        "text": "#2B3648",
        "text_hi": "#0E1B2E",
        "text_mid": "#66788F",
        "text_low": "#93A5BC",
        "accent": "#2F80ED",
        "accent_hi": "#5C9BF5",
        "accent_dim": "#1C63C9",
        "accent_soft": "rgba(47, 128, 237, 0.13)",
        "on_accent": "#FFFFFF",
        "track": "#E1EBF8",
        "handle": "#FFFFFF",
        "handle_line": "1px solid #BFD3EC",
        "hover_bg": "#EEF5FE",
        "hover_line": "#BBD2EE",
        "cb_bg": "#FFFFFF",
        "cb_line": "#C6D8EF",
        "cb_line_hover": "#9CBBE2",
        "tick": "#FFFFFF",
        "scroll": "#C8D9EE",
        "scroll_hi": "#AEC5E2",
        "popup": "#FFFFFF",
        "popup_line": "#D8E5F6",
        "tooltip_bg": "#FFFFFF",
        "tooltip_line": "#D5E3F5",
        "preview_a": "#FFFFFF",
        "preview_b": "#EAF2FD",
        "chevron": "#7C8FA8",
        "shell_line": "#D3E2F4",
        "dark": False,
    },
}


def palette(cfg):
    return PALETTES["light" if cfg.get("ui_mode") == "light" else "dark"]


def theme_strip(colors, w=52, h=14):
    pm = QPixmap(w * 2, h * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    grad = QLinearGradient(0, 0, w, h)
    n = max(1, len(colors))
    for i, c in enumerate(colors):
        grad.setColorAt(i / n, QColor(c))
    grad.setColorAt(1.0, QColor(colors[0]))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(0, 0, w, h), 4, 4)
    p.end()
    return pm


def arrow_png_path(dark):
    """生成下拉箭头图，QSS 的 ::down-arrow 只吃图片文件。"""
    try:
        d = cfgmod.config_dir()
        os.makedirs(d, exist_ok=True)
        name = "chevron_dark.png" if dark else "chevron_light.png"
        p = os.path.join(d, name)
        if not os.path.exists(p):
            pal = PALETTES["dark" if dark else "light"]
            pm = QPixmap(32, 32)
            pm.setDevicePixelRatio(2)
            pm.fill(Qt.GlobalColor.transparent)
            pa = QPainter(pm)
            pa.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(QColor(pal["chevron"]), 1.7)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pa.setPen(pen)
            path = QPainterPath()
            path.moveTo(4.6, 6.4)
            path.lineTo(8.0, 9.8)
            path.lineTo(11.4, 6.4)
            pa.drawPath(path)
            pa.end()
            pm.save(p, "PNG")
        return p.replace("\\", "/")
    except Exception:
        return ""


def brand_pixmap(pal, size=34):
    """左上角小徽标：蓝色渐变底 + 白色 C"""
    pm = QPixmap(size * 2, size * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0.0, QColor(pal["accent_hi"]))
    grad.setColorAt(1.0, QColor(pal["accent"]))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(0, 0, size, size), 10, 10)

    font = QFont("Arial")
    font.setPixelSize(int(size * 0.74))
    font.setWeight(QFont.Weight.Black)
    p.setFont(font)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRectF(0, -1, size, size), Qt.AlignmentFlag.AlignCenter, "C")
    p.end()
    return pm


def _draw_sun(p, rect, color):
    c = rect.center()
    pen = QPen(color, 1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(c, 3.1, 3.1)
    for i in range(8):
        a = i * math.pi / 4
        dx, dy = math.cos(a), math.sin(a)
        p.drawLine(
            QPointF(c.x() + dx * 5.3, c.y() + dy * 5.3),
            QPointF(c.x() + dx * 7.0, c.y() + dy * 7.0),
        )


def _draw_moon(p, rect, color):
    c = rect.center()
    outer = QPainterPath()
    outer.addEllipse(QPointF(c.x(), c.y()), 5.3, 5.3)
    inner = QPainterPath()
    inner.addEllipse(QPointF(c.x() + 2.6, c.y() - 1.7), 4.6, 4.6)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawPath(outer.subtracted(inner))


class WinButton(QWidget):
    """自绘的最小化 / 关闭按钮"""

    def __init__(self, kind, callback):
        super().__init__()
        self._kind = kind
        self._cb = callback
        self._pal = PALETTES["dark"]
        self._hover = False
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("最小化" if kind == "min" else "关闭")

    def set_palette_colors(self, pal):
        self._pal = pal
        self.update()

    def paintEvent(self, ev):
        pal = self._pal
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(1.5, 3, -1.5, -3)

        if self._hover:
            if self._kind == "close":
                p.setBrush(QColor("#E5484D") if pal["dark"] else QColor("#E5484D"))
                p.setPen(Qt.PenStyle.NoPen)
            else:
                p.setBrush(QColor(pal["hover_bg"]))
                p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r, 7, 7)

        if self._kind == "close" and self._hover:
            col = QColor("#FFFFFF")
        elif self._hover:
            col = QColor(pal["text_hi"])
        else:
            col = QColor(pal["text_mid"])

        pen = QPen(col, 1.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        c = QRectF(self.rect()).center()
        if self._kind == "min":
            p.drawLine(QPointF(c.x() - 5, c.y()), QPointF(c.x() + 5, c.y()))
        else:
            d = 4.4
            p.drawLine(QPointF(c.x() - d, c.y() - d), QPointF(c.x() + d, c.y() + d))
            p.drawLine(QPointF(c.x() + d, c.y() - d), QPointF(c.x() - d, c.y() + d))
        p.end()

    def enterEvent(self, ev):
        self._hover = True
        self.update()

    def leaveEvent(self, ev):
        self._hover = False
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._hover = False
            self.update()
            self._cb()


class ModeSwitch(QWidget):
    """浅色 / 深色切换：一颗两段胶囊"""

    changed = Signal(str)

    def __init__(self, mode, pal):
        super().__init__()
        self._mode = "light" if mode == "light" else "dark"
        self._pal = pal
        self.setFixedSize(58, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("切换浅色 / 深色界面")

    def set_mode(self, mode, pal=None):
        self._mode = "light" if mode == "light" else "dark"
        if pal is not None:
            self._pal = pal
        self.update()

    def paintEvent(self, ev):
        pal = self._pal
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(QColor(pal["field"]))
        p.setPen(QPen(QColor(pal["field_line"]), 1))
        p.drawRoundedRect(r, 15, 15)

        is_light = self._mode == "light"
        hx = 2.0 if is_light else 30.0
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(pal["accent"]))
        p.drawEllipse(QRectF(hx, 2, 26, 26))

        on = QColor(pal["on_accent"])
        off = QColor(pal["text_low"])
        _draw_sun(p, QRectF(2, 2, 26, 26), on if is_light else off)
        _draw_moon(p, QRectF(30, 2, 26, 26), off if is_light else on)
        p.end()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            target = "light" if ev.position().x() < self.width() / 2 else "dark"
            if target != self._mode:
                self._mode = target
                self.update()
                self.changed.emit(target)


class DarkStyle(QProxyStyle):
    """只重绘箭头和勾选框，其余交给 Fusion。"""

    def __init__(self, pal):
        super().__init__(QStyleFactory.create("Fusion"))
        self.update_palette(pal)

    def update_palette(self, pal):
        self.accent = QColor(pal["accent"])
        self.arrow_color = QColor(pal["chevron"])
        self.cb_bg = QColor(pal["cb_bg"])
        self.cb_line = QColor(pal["cb_line"])
        self.cb_line_hover = QColor(pal["cb_line_hover"])
        self.tick = QColor(pal["tick"])

    def pixelMetric(self, m, option=None, widget=None):
        if m in (QStyle.PixelMetric.PM_IndicatorWidth, QStyle.PixelMetric.PM_IndicatorHeight):
            return 18
        if m == QStyle.PixelMetric.PM_CheckBoxLabelSpacing:
            return 9
        return super().pixelMetric(m, option, widget)

    def drawPrimitive(self, element, option, painter, widget=None):
        PE = QStyle.PrimitiveElement
        if element in (PE.PE_IndicatorArrowDown, PE.PE_IndicatorArrowUp):
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            r = option.rect
            cx, cy = r.center().x(), r.center().y()
            w, h = 4.6, 2.7
            down = element == PE.PE_IndicatorArrowDown
            pen = QPen(self.arrow_color, 1.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            if down:
                path.moveTo(cx - w, cy - h)
                path.lineTo(cx, cy + h)
                path.lineTo(cx + w, cy - h)
            else:
                path.moveTo(cx - w, cy + h)
                path.lineTo(cx, cy - h)
                path.lineTo(cx + w, cy + h)
            painter.drawPath(path)
            painter.restore()
            return

        if element == PE.PE_IndicatorCheckBox:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            r = QRectF(option.rect).adjusted(0.5, 0.5, -0.5, -0.5)
            side = min(r.width(), r.height())
            box = QRectF(
                r.center().x() - side / 2, r.center().y() - side / 2, side, side
            )
            on = bool(option.state & QStyle.StateFlag.State_On)
            hover = bool(option.state & QStyle.StateFlag.State_MouseOver)
            enabled = bool(option.state & QStyle.StateFlag.State_Enabled)

            if on:
                g = QLinearGradient(box.topLeft(), box.bottomRight())
                g.setColorAt(0.0, self.accent.lighter(108))
                g.setColorAt(1.0, self.accent.darker(112))
                painter.setBrush(QBrush(g))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(box, 5.5, 5.5)
                tick = QPainterPath()
                tick.moveTo(box.left() + side * 0.26, box.top() + side * 0.52)
                tick.lineTo(box.left() + side * 0.43, box.top() + side * 0.70)
                tick.lineTo(box.left() + side * 0.75, box.top() + side * 0.31)
                pen = QPen(self.tick, max(1.8, side * 0.13))
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(tick)
            else:
                painter.setBrush(self.cb_bg)
                line = self.cb_line_hover if hover else self.cb_line
                painter.setPen(QPen(line, 1.4))
                painter.drawRoundedRect(box, 5.5, 5.5)

            if not enabled:
                painter.setOpacity(0.4)
            painter.restore()
            return

        super().drawPrimitive(element, option, painter, widget)


def build_qss(pal):
    bg = pal["bg"]
    card = pal["card"]
    card_line = pal["card_line"]
    field = pal["field"]
    field_line = pal["field_line"]
    line = pal["line"]
    text = pal["text"]
    text_hi = pal["text_hi"]
    text_mid = pal["text_mid"]
    text_low = pal["text_low"]
    accent = pal["accent"]
    accent_hi = pal["accent_hi"]
    accent_dim = pal["accent_dim"]
    accent_soft = pal["accent_soft"]
    on_accent = pal["on_accent"]
    track = pal["track"]
    handle = pal["handle"]
    handle_line = pal["handle_line"]
    hover_bg = pal["hover_bg"]
    hover_line = pal["hover_line"]
    scroll = pal["scroll"]
    scroll_hi = pal["scroll_hi"]
    popup = pal["popup"]
    popup_line = pal["popup_line"]
    tip_bg = pal["tooltip_bg"]
    tip_line = pal["tooltip_line"]
    shell_line = pal["shell_line"]

    arrow = arrow_png_path(pal["dark"])
    arrow_rule = (
        'QComboBox::down-arrow { image: url("%s"); width: 15px; height: 15px; }' % arrow
        if arrow
        else ""
    )

    return f"""
QDialog {{
    background: transparent;
}}
QFrame#shell {{
    background: {bg};
    border: 1px solid {shell_line};
    border-radius: 14px;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget {{
    background: transparent;
}}
/* 滚动区里的页面容器（viewport 的子控件）默认会带一层系统窗口底色，
   不显式清掉的话，卡片缝隙和四边留白会透出白色 */
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QLabel {{
    color: {text};
    background: transparent;
    font-size: 13px;
}}
QLabel#appTitle {{
    color: {text_hi};
    font-size: 19px;
    font-weight: 700;
}}
QLabel#appSub {{
    color: {text_low};
    font-size: 12px;
}}
QLabel#cardTitle {{
    color: {text_mid};
    font-size: 12px;
    font-weight: 600;
}}
QLabel#field {{
    color: {text_mid};
    font-size: 13px;
}}
QLabel#value {{
    color: {text};
    background: {field};
    border: 1px solid {field_line};
    border-radius: 7px;
    font-family: "Consolas", "Microsoft YaHei UI";
    font-size: 12px;
}}
QLabel#hint {{
    color: {text_mid};
    font-size: 12px;
}}
QLabel#faint {{
    color: {text_low};
    font-size: 12px;
}}

QFrame#card {{
    background: {card};
    border: 1px solid {card_line};
    border-radius: 13px;
}}
QFrame#seg {{
    background: {field};
    border: 1px solid {field_line};
    border-radius: 11px;
}}
QFrame#line {{
    background: {line};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

QPushButton {{
    background: {card};
    color: {text};
    border: 1px solid {hover_line};
    border-radius: 9px;
    padding: 0 16px;
    min-height: 32px;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {hover_bg};
    border-color: {accent};
    color: {text_hi};
}}
QPushButton:pressed {{
    background: {field};
}}
QPushButton[kind="ghost"] {{
    background: {card};
    border: 1px solid {hover_line};
    color: {text_mid};
}}
QPushButton[kind="ghost"]:hover {{
    background: {hover_bg};
    border-color: {accent};
    color: {text_hi};
}}
QPushButton[kind="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {accent_hi}, stop:1 {accent});
    color: {on_accent};
    border: none;
    font-weight: 600;
    min-height: 34px;
}}
QPushButton[kind="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {accent_hi}, stop:1 {accent_dim});
}}
QPushButton[kind="primary"]:pressed {{
    background: {accent_dim};
}}

QPushButton#segBtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0 20px;
    min-height: 28px;
    color: {text_mid};
    font-size: 13px;
}}
QPushButton#segBtn:hover {{
    color: {text_hi};
    background: {hover_bg};
}}
QPushButton#segBtn:checked {{
    background: {accent_soft};
    color: {accent};
    font-weight: 600;
}}

QSlider {{
    min-height: 24px;
    background: transparent;
}}
QSlider::groove:horizontal {{
    height: 4px;
    border-radius: 2px;
    background: {track};
}}
QSlider::sub-page:horizontal {{
    height: 4px;
    border-radius: 2px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {accent_dim}, stop:1 {accent_hi});
}}
QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: {handle};
    border: {handle_line};
}}
QSlider::handle:horizontal:hover {{
    background: {accent};
    border: 1px solid {accent};
}}
QSlider::handle:horizontal:pressed {{
    background: {accent_dim};
    border: 1px solid {accent_dim};
}}

QComboBox {{
    background: {field};
    color: {text};
    border: 1px solid {field_line};
    border-radius: 8px;
    padding: 4px 30px 4px 12px;
    min-height: 30px;
    font-size: 13px;
}}
QComboBox:hover {{
    border-color: {hover_line};
}}
QComboBox:focus {{
    border-color: {accent};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
    background: transparent;
}}
{arrow_rule}
QComboBox QAbstractItemView {{
    background: {popup};
    border: 1px solid {popup_line};
    border-radius: 9px;
    padding: 5px;
    color: {text};
    outline: none;
    selection-background-color: {accent_soft};
    selection-color: {accent};
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding-left: 8px;
    border-radius: 6px;
}}

QCheckBox {{
    color: {text};
    font-size: 13px;
    spacing: 9px;
}}
QCheckBox:hover {{
    color: {text_hi};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {scroll};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {scroll_hi};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QToolTip {{
    background: {tip_bg};
    color: {text};
    border: 1px solid {tip_line};
    padding: 5px 8px;
}}
"""


class LivePreview(QWidget):
    """设置面板里的迷你实时预览"""

    def __init__(self, get_cfg, get_pal):
        super().__init__()
        self.get_cfg = get_cfg
        self.get_pal = get_pal
        self.setFixedHeight(104)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._cache_key = None
        self._cache_path = None

    def _path_for(self, cfg):
        key = (cfg["font_family"], cfg["font_weight"])
        if key != self._cache_key:
            self._cache_path = build_letter_path(*key)
            self._cache_key = key
        return self._cache_path

    def paintEvent(self, ev):
        cfg = self.get_cfg()
        pal = self.get_pal()
        dark = pal["dark"]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 13.0
        clip = QPainterPath()
        clip.addRoundedRect(r, radius, radius)
        p.setClipPath(clip)

        bg = QLinearGradient(r.topLeft(), r.bottomRight())
        bg.setColorAt(0.0, QColor(pal["preview_a"]))
        bg.setColorAt(1.0, QColor(pal["preview_b"]))
        p.fillPath(clip, QBrush(bg))

        cols = theme_colors(cfg)
        amb = QColor(pal["accent"])
        amb.setAlphaF(0.12 if dark else 0.07)
        rg = QRadialGradient(r.center(), r.width() * 0.45)
        rg.setColorAt(0.0, amb)
        amb2 = QColor(amb)
        amb2.setAlphaF(0.0)
        rg.setColorAt(1.0, amb2)
        p.fillRect(r, QBrush(rg))

        target = min(self.height() - 26.0, 96.0)
        sc = target / 200.0
        path = self._path_for(cfg)

        p.save()
        p.translate(r.center())
        p.scale(sc, sc)

        grad = QConicalGradient(QPointF(0, 0), (time.monotonic() * 90) % 360)
        n = len(cols)
        for i, c in enumerate(cols):
            grad.setColorAt(i / n, QColor(c))
        grad.setColorAt(1.0, QColor(cols[0]))

        glow = cfg["glow"]
        if glow > 0:
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            for mult, a in ((2.4, 0.05), (1.4, 0.09), (0.7, 0.14)):
                col = QColor(cols[0])
                col.setAlphaF(a * (1.0 if dark else 0.5))
                pen = QPen(col, max(0.5, glow * mult / max(sc, 0.02)))
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                p.strokePath(path, pen)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        p.fillPath(path, QBrush(grad))
        outline = QColor(255, 255, 255, 60) if dark else QColor(15, 40, 80, 40)
        pen = QPen(outline, max(0.6, 1.4 / max(sc, 0.02)))
        p.strokePath(path, pen)
        p.restore()

        p.setClipping(False)
        p.setBrush(Qt.BrushStyle.NoBrush)
        border = QColor(255, 255, 255, 22) if dark else QColor(60, 110, 180, 36)
        p.setPen(QPen(border, 1))
        p.drawRoundedRect(r, radius, radius)

        f = QFont("Microsoft YaHei UI")
        f.setPixelSize(10)
        p.setFont(f)
        p.setPen(QColor(255, 255, 255, 96) if dark else QColor(45, 80, 130, 130))
        p.drawText(
            r.adjusted(14, 10, -14, 0),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            t("look.preview"),
        )
        p.setPen(QColor(255, 255, 255, 82) if dark else QColor(45, 80, 130, 112))
        p.drawText(
            r.adjusted(14, 10, -14, 0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
            f'{cfg["start_size"]} → {cfg["peak_size"]} px',
        )
        p.end()


class SettingsDialog(QDialog):
    def __init__(self, cfg, on_change, on_preview):
        super().__init__(None)
        self.cfg = cfg
        self.on_change = on_change
        self.on_preview = on_preview
        self._loading = True
        self._pal = palette(cfg)
        # 需要随语言切换重刷文案的控件登记表
        self._reg_labels = []
        self._reg_buttons = []
        self._reg_checks = []
        self._reg_combos = []
        self._reg_tips = []

        self.setWindowTitle(t("app.window"))
        avail = QApplication.primaryScreen().availableGeometry()
        self.setFixedSize(
            min(748, avail.width() - 60),
            min(726, avail.height() - 60),
        )
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._style = DarkStyle(self._pal)
        self.setStyle(self._style)
        self._drag_off = None

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        root.addWidget(self.shell)
        inner = QVBoxLayout(self.shell)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # ---------- 顶部 ----------
        header = QWidget()
        self.header = header
        hl = QHBoxLayout(header)
        hl.setContentsMargins(22, 16, 22, 14)
        hl.setSpacing(12)

        self.lbl_brand = QLabel()
        self.lbl_brand.setFixedSize(34, 34)
        self.lbl_brand.setPixmap(brand_pixmap(self._pal, 34))
        hl.addWidget(self.lbl_brand)

        tb = QVBoxLayout()
        tb.setSpacing(1)
        title = self._label("app.display", "appTitle")
        sub = self._label("app.sub", "appSub")
        tb.addWidget(title)
        tb.addWidget(sub)
        hl.addLayout(tb)
        hl.addStretch(1)

        self.mode_switch = ModeSwitch(cfg.get("ui_mode", "dark"), self._pal)
        self.mode_switch.changed.connect(self._on_mode)
        self.mode_switch.setToolTip(t("tip.mode"))
        hl.addWidget(self.mode_switch)
        hl.addSpacing(8)

        seg = QFrame()
        seg.setObjectName("seg")
        sl = QHBoxLayout(seg)
        sl.setContentsMargins(4, 4, 4, 4)
        sl.setSpacing(2)
        self.seg_group = QButtonGroup(self)
        self.seg_group.setExclusive(True)
        self.seg_buttons = []
        for i, key in enumerate(("tab.look", "tab.anim", "tab.misc")):
            b = self._button(key, "segBtn")
            b.setObjectName("segBtn")
            b.setCheckable(True)
            b.setChecked(i == 0)
            self.seg_group.addButton(b, i)
            self.seg_buttons.append(b)
            sl.addWidget(b)
        hl.addWidget(seg)
        hl.addSpacing(6)

        self.btn_min = WinButton("min", self.showMinimized)
        self.btn_close = WinButton("close", self.close)
        self.btn_min.setToolTip(t("tip.min"))
        self.btn_close.setToolTip(t("tip.close"))
        hl.addWidget(self.btn_min)
        hl.addWidget(self.btn_close)
        inner.addWidget(header)

        header.installEventFilter(self)
        header.setMouseTracking(True)

        line = QFrame()
        line.setObjectName("line")
        inner.addWidget(line)

        # ---------- 内容 ----------
        self.stack = QStackedWidget()
        self.stack.addWidget(self._wrap_scroll(self._build_look_tab()))
        self.stack.addWidget(self._wrap_scroll(self._build_anim_tab()))
        self.stack.addWidget(self._wrap_scroll(self._build_misc_tab()))
        self.seg_group.idClicked.connect(self.stack.setCurrentIndex)
        inner.addWidget(self.stack, 1)

        # ---------- 底部 ----------
        line2 = QFrame()
        line2.setObjectName("line")
        inner.addWidget(line2)

        footer = QWidget()
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(22, 10, 18, 14)
        fl.setSpacing(10)

        self.dot = QLabel()
        self.dot.setFixedSize(6, 6)
        fl.addWidget(self.dot)
        self.lbl_tip = self._label("footer.tip", "hint")
        fl.addWidget(self.lbl_tip)
        fl.addStretch(1)

        btn_reset = self._button("btn.reset", "footerReset", "ghost")
        btn_reset.clicked.connect(self._reset)
        fl.addWidget(btn_reset)

        btn_prev = self._button("btn.preview", "footerPreview", "primary")
        btn_prev.setDefault(True)
        btn_prev.clicked.connect(self.on_preview)
        fl.addWidget(btn_prev)

        btn_close = self._button("btn.close", "footerClose", "ghost")
        btn_close.clicked.connect(self.close)
        fl.addWidget(btn_close)
        inner.addWidget(footer)

        self._apply_theme()
        self._loading = False
        self._refresh_widgets()

        self._live = QTimer(self)
        self._live.setInterval(60)
        self._live.timeout.connect(self._repaint_preview)

    # 预览刷新只在这个窗口可见时跑，关掉就停表，别在后台空转
    def showEvent(self, ev):
        super().showEvent(ev)
        self._live.start()

    def hideEvent(self, ev):
        self._live.stop()
        super().hideEvent(ev)

    # ---------------- 主题 ----------------
    def _apply_theme(self):
        pal = palette(self.cfg)
        self._pal = pal
        self._style.update_palette(pal)
        self.setStyleSheet(build_qss(pal))
        self.mode_switch.set_mode(self.cfg.get("ui_mode", "dark"), pal)
        self.lbl_brand.setPixmap(brand_pixmap(pal, 34))
        self.dot.setStyleSheet("background:%s; border-radius:3px;" % pal["accent"])
        self.btn_min.set_palette_colors(pal)
        self.btn_close.set_palette_colors(pal)
        self._update_color_buttons()
        self.update()

    def _on_mode(self, mode):
        self.cfg["ui_mode"] = mode
        self._apply_theme()
        self.on_change()

    # ---------------- 语言 ----------------
    def _on_language(self, index):
        code = self.cmb_lang.itemData(index)
        if not code or code == i18n.get_lang():
            return
        self.cfg["language"] = code
        i18n.set_lang(code)
        self._retranslate()
        self.on_change()

    def _retranslate(self):
        """把登记过的控件文案按当前语言刷一遍。"""
        self.setWindowTitle(t("app.window"))
        for w, key in self._reg_labels:
            w.setText(t(key))
        for w, key in self._reg_buttons:
            w.setText(t(key))
        for w, key in self._reg_checks:
            w.setText(t(key))
        for combo, pairs in self._reg_combos:
            for i, (_data, key) in enumerate(pairs):
                if key and i < combo.count():
                    combo.setItemText(i, t(key))
        for w, key in self._reg_tips:
            w.setToolTip(t(key))
        self.mode_switch.setToolTip(t("tip.mode"))
        self.btn_min.setToolTip(t("tip.min"))
        self.btn_close.setToolTip(t("tip.close"))
        self._update_color_buttons()
        self.preview.update()
        self.update()

    # ---------------- 小部件工厂 ----------------
    @staticmethod
    def _wrap_scroll(page):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setWidget(page)
        sa.viewport().setAutoFillBackground(False)
        page.setAutoFillBackground(False)
        return sa

    def _card(self, title=None):
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 12, 18, 14)
        v.setSpacing(8)
        if title:
            v.addWidget(self._label(title, "cardTitle"))
        return card, v

    @staticmethod
    def _grid():
        g = QGridLayout()
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(8)
        g.setColumnMinimumWidth(0, 74)
        g.setColumnStretch(1, 1)
        return g

    # ---- 会跟着语言变文案的小控件，统一登记 ----
    def _label(self, key, obj=None):
        l = QLabel(t(key))
        if obj:
            l.setObjectName(obj)
        self._reg_labels.append((l, key))
        return l

    def _button(self, key, obj=None, kind=None):
        b = QPushButton(t(key))
        if obj:
            b.setObjectName(obj)
        if kind:
            b.setProperty("kind", kind)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reg_buttons.append((b, key))
        return b

    def _check(self, key):
        c = QCheckBox(t(key))
        self._reg_checks.append((c, key))
        return c

    def _reg_combo(self, combo, pairs):
        """pairs: [(itemData, i18nKey 或 None)]，None 表示文案不翻译（如 English 本身）。"""
        self._reg_combos.append((combo, list(pairs)))
        return combo

    def _field(self, key):
        l = QLabel(t(key))
        l.setObjectName("field")
        self._reg_labels.append((l, key))
        return l

    def _add_row(self, grid, row, key, widget):
        grid.addWidget(self._field(key), row, 0, Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(widget, row, 1)

    # ---------------- 外观页 ----------------
    def _build_look_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(18, 12, 18, 6)
        lay.setSpacing(10)

        self.preview = LivePreview(lambda: self.cfg, lambda: self._pal)
        lay.addWidget(self.preview)

        # 颜色
        box_theme, vb = self._card("card.color")
        g1 = self._grid()

        self.cmb_theme = QComboBox()
        self.cmb_theme.setIconSize(QSize(52, 14))
        for key, name, cols in THEMES:
            if cols is None:
                cols = self.cfg["custom_colors"]
            self.cmb_theme.addItem(theme_strip(cols), t("theme." + key), key)
        self._reg_combo(self.cmb_theme, [(k, "theme." + k) for k, _n, _c in THEMES])
        self.cmb_theme.currentIndexChanged.connect(self._mark)
        self._add_row(g1, 0, "field.theme", self.cmb_theme)

        colorrow = QWidget()
        ch = QHBoxLayout(colorrow)
        ch.setContentsMargins(0, 0, 0, 0)
        ch.setSpacing(8)
        self.btn_c1 = QPushButton()
        self.btn_c2 = QPushButton()
        for b in (self.btn_c1, self.btn_c2):
            b.setFixedSize(56, 24)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(self._pick_color)
            ch.addWidget(b)
        note = self._label("hint.swatch", "faint")
        ch.addSpacing(4)
        ch.addWidget(note)
        ch.addStretch(1)
        self._add_row(g1, 1, "field.custom", colorrow)

        self.sld_flow, self.lbl_flow = self._make_slider(0, 300, 100, "×")
        self.sld_flow.valueChanged.connect(self._mark)
        self._add_row(g1, 2, "field.flow", self._slider_wrap(self.sld_flow, self.lbl_flow))
        vb.addLayout(g1)
        lay.addWidget(box_theme)

        # 字形
        box_font, vb2 = self._card("card.glyph")
        g2 = self._grid()

        self.cmb_font = QFontComboBox()
        self.cmb_font.currentFontChanged.connect(self._mark)
        self._add_row(g2, 0, "field.font", self.cmb_font)

        self.cmb_weight = QComboBox()
        for key, name in FONT_WEIGHTS:
            self.cmb_weight.addItem(t("weight." + key), key)
        self._reg_combo(self.cmb_weight, [(k, "weight." + k) for k, _n in FONT_WEIGHTS])
        self.cmb_weight.currentIndexChanged.connect(self._mark)
        self._add_row(g2, 1, "field.weight", self.cmb_weight)

        self.sld_start, self.lbl_start = self._make_slider(8, 400, 46, " px")
        self.sld_start.valueChanged.connect(self._mark)
        self._add_row(g2, 2, "field.start", self._slider_wrap(self.sld_start, self.lbl_start))

        self.sld_peak, self.lbl_peak = self._make_slider(30, 600, 168, " px")
        self.sld_peak.valueChanged.connect(self._mark)
        self._add_row(g2, 3, "field.peak", self._slider_wrap(self.sld_peak, self.lbl_peak))

        self.sld_opacity, self.lbl_opacity = self._make_slider(10, 100, 100, "%")
        self.sld_opacity.valueChanged.connect(self._mark)
        self._add_row(g2, 4, "field.opacity", self._slider_wrap(self.sld_opacity, self.lbl_opacity))

        self.sld_glow, self.lbl_glow = self._make_slider(0, 40, 14, "")
        self.sld_glow.valueChanged.connect(self._mark)
        self._add_row(g2, 5, "field.glow", self._slider_wrap(self.sld_glow, self.lbl_glow))
        vb2.addLayout(g2)
        lay.addWidget(box_font)
        lay.addStretch(1)
        return page

    # ---------------- 动画页 ----------------
    def _build_anim_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(18, 12, 18, 6)
        lay.setSpacing(10)

        box, vb = self._card("card.motion")
        g1 = self._grid()
        self.cmb_in = QComboBox()
        for key, name in IN_ANIMS:
            self.cmb_in.addItem(t("anim_in." + key), key)
        self._reg_combo(self.cmb_in, [(k, "anim_in." + k) for k, _n in IN_ANIMS])
        self.cmb_in.currentIndexChanged.connect(self._mark)
        self._add_row(g1, 0, "field.in", self.cmb_in)

        self.cmb_out = QComboBox()
        for key, name in OUT_ANIMS:
            self.cmb_out.addItem(t("anim_out." + key), key)
        self._reg_combo(self.cmb_out, [(k, "anim_out." + k) for k, _n in OUT_ANIMS])
        self.cmb_out.currentIndexChanged.connect(self._mark)
        self._add_row(g1, 1, "field.out", self.cmb_out)
        vb.addLayout(g1)
        lay.addWidget(box)

        box2, vb2 = self._card("card.timing")
        g2 = self._grid()
        self.sld_in, self.lbl_in = self._make_slider(40, 1200, 260, " ms")
        self.sld_in.valueChanged.connect(self._mark)
        self._add_row(g2, 0, "field.in_ms", self._slider_wrap(self.sld_in, self.lbl_in))

        self.sld_hold, self.lbl_hold = self._make_slider(0, 2000, 240, " ms")
        self.sld_hold.valueChanged.connect(self._mark)
        self._add_row(g2, 1, "field.hold_ms", self._slider_wrap(self.sld_hold, self.lbl_hold))

        self.sld_out, self.lbl_out = self._make_slider(40, 2000, 460, " ms")
        self.sld_out.valueChanged.connect(self._mark)
        self._add_row(g2, 2, "field.out_ms", self._slider_wrap(self.sld_out, self.lbl_out))
        vb2.addLayout(g2)
        lay.addWidget(box2)

        box3, vb3 = self._card("card.preset")
        h3 = QHBoxLayout()
        h3.setSpacing(8)
        for key, preset in PRESETS:
            b = self._button(key, kind="ghost")
            b.clicked.connect(lambda _checked=False, p=preset: self._apply_preset(p))
            h3.addWidget(b)
        h3.addStretch(1)
        vb3.addLayout(h3)
        lay.addWidget(box3)

        box4, vb4 = self._card("card.extra")
        self.chk_shock = self._check("chk.ripple")
        self.chk_shock.toggled.connect(self._mark)
        vb4.addWidget(self.chk_shock)
        lay.addWidget(box4)

        hint = self._label("hint.duration", "hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        return page

    # ---------------- 其他页 ----------------
    def _build_misc_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(18, 12, 18, 6)
        lay.setSpacing(10)

        # 语言：放在最上面，切换后整窗文案立刻重刷
        box_lang, vb_lang = self._card("card.lang")
        g0 = self._grid()
        self.cmb_lang = QComboBox()
        for code, native in i18n.LANGS:
            self.cmb_lang.addItem(native, code)
        self._reg_combo(self.cmb_lang, [(c, None) for c, _n in i18n.LANGS])
        self.cmb_lang.currentIndexChanged.connect(self._on_language)
        self._add_row(g0, 0, "field.lang", self.cmb_lang)
        vb_lang.addLayout(g0)
        lay.addWidget(box_lang)

        box, vb = self._card("card.behavior")
        self.chk_enabled = self._check("chk.enabled")
        self.chk_enabled.toggled.connect(self._mark)
        self.chk_caret = self._check("chk.caret")
        self.chk_caret.toggled.connect(self._mark)
        self.chk_auto = self._check("chk.autostart")
        self.chk_auto.toggled.connect(self._on_autostart)
        for c in (self.chk_enabled, self.chk_caret, self.chk_auto):
            vb.addWidget(c)
        lay.addWidget(box)

        box2, vb2 = self._card("card.about")
        intro = self._label("about.intro", "hint")
        intro.setWordWrap(True)
        vb2.addWidget(intro)
        for key in ("about.b1", "about.b2", "about.b3"):
            line = self._label(key, "hint")
            line.setWordWrap(True)
            vb2.addWidget(line)
        lay.addWidget(box2)

        box3, vb3 = self._card("card.info")
        ver = self._label("app.version", "hint")
        vb3.addWidget(ver)
        path = QLabel(cfgmod.config_dir())
        path.setObjectName("faint")
        path.setWordWrap(True)
        path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        vb3.addWidget(path)

        row = QHBoxLayout()
        btn_open = self._button("btn.open_dir", kind="ghost")
        btn_open.clicked.connect(self._open_config_dir)
        row.addWidget(btn_open)
        row.addStretch(1)
        vb3.addSpacing(2)
        vb3.addLayout(row)
        lay.addWidget(box3)

        lay.addStretch(1)
        return page

    def _open_config_dir(self):
        try:
            os.startfile(cfgmod.config_dir())
        except Exception:
            pass

    # ---------------- 组件小工具 ----------------
    def _make_slider(self, lo, hi, val, suffix):
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        s.setValue(val)
        s.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl = QLabel(f"{val}{suffix}")
        lbl.setObjectName("value")
        lbl.setFixedSize(66, 24)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setProperty("suffix", suffix)
        return s, lbl

    def _slider_wrap(self, slider, label):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)
        h.addWidget(slider, 1)
        h.addWidget(label)
        return w

    def _sync_label(self, slider, label):
        suf = label.property("suffix") or ""
        if suf == "×":
            label.setText(f"{slider.value() / 100:.1f}×")
        else:
            label.setText(f"{slider.value()}{suf}")

    # ---------------- 数据同步 ----------------
    def _refresh_widgets(self):
        self._loading = True
        c = self.cfg

        idx = self.cmb_theme.findData(c.get("theme", "rainbow"))
        self.cmb_theme.setCurrentIndex(max(0, idx))
        self._update_color_buttons()

        self.sld_flow.setValue(int(round(float(c.get("flow_speed", 1.0)) * 100)))
        self.cmb_font.setCurrentFont(QFont(c["font_family"]))
        wi = self.cmb_weight.findData(c.get("font_weight", "black"))
        self.cmb_weight.setCurrentIndex(max(0, wi))

        self.sld_start.setValue(c["start_size"])
        self.sld_peak.setValue(c["peak_size"])
        self.sld_opacity.setValue(c["opacity"])
        self.sld_glow.setValue(c["glow"])

        self.chk_shock.setChecked(bool(c.get("shockwave")))

        self.cmb_in.setCurrentIndex(max(0, self.cmb_in.findData(c.get("in_anim", "spray"))))
        self.cmb_out.setCurrentIndex(max(0, self.cmb_out.findData(c.get("out_anim", "expand"))))
        self.sld_in.setValue(c["in_ms"])
        self.sld_hold.setValue(c["hold_ms"])
        self.sld_out.setValue(c["out_ms"])

        self.chk_enabled.setChecked(bool(c.get("enabled", True)))
        self.chk_caret.setChecked(bool(c.get("prefer_caret", True)))
        self.chk_auto.setChecked(cfgmod.is_autostart_enabled())
        li = self.cmb_lang.findData(i18n.get_lang())
        self.cmb_lang.setCurrentIndex(max(0, li))

        for s, l in (
            (self.sld_flow, self.lbl_flow),
            (self.sld_start, self.lbl_start),
            (self.sld_peak, self.lbl_peak),
            (self.sld_opacity, self.lbl_opacity),
            (self.sld_glow, self.lbl_glow),
            (self.sld_in, self.lbl_in),
            (self.sld_hold, self.lbl_hold),
            (self.sld_out, self.lbl_out),
        ):
            self._sync_label(s, l)

        self._loading = False

    def reload(self, cfg=None):
        if cfg is not None:
            self.cfg = cfg
        lang = self.cfg.get("language")
        if lang and lang != i18n.get_lang():
            i18n.set_lang(lang)
            self._retranslate()
        self._refresh_widgets()
        self._apply_theme()

    def _update_color_buttons(self):
        cols = self.cfg.get("custom_colors") or ["#FF2D75", "#00C2FF"]
        is_custom = self.cmb_theme.currentData() == "custom"
        tip = t("tip.custom_edit") if is_custom else t("tip.custom_pick")
        edge = "rgba(255,255,255,0.22)" if self._pal["dark"] else "rgba(0,0,0,0.12)"
        edge_h = "rgba(255,255,255,0.65)" if self._pal["dark"] else "rgba(0,0,0,0.42)"
        for btn, col in ((self.btn_c1, cols[0]), (self.btn_c2, cols[1] if len(cols) > 1 else cols[0])):
            btn.setStyleSheet(
                "QPushButton{background:%s;border:1px solid %s;border-radius:8px;}"
                "QPushButton:hover{border:1px solid %s;}" % (col, edge, edge_h)
            )
            btn.setToolTip(f"{col}  ·  {tip}")

    def _pick_color(self):
        cols = list(self.cfg.get("custom_colors") or ["#FF2D75", "#00C2FF"])
        target = 0 if self.sender() is self.btn_c1 else 1
        cur = QColor(cols[target] if target < len(cols) else cols[0])
        col = QColorDialog.getColor(cur, self, t("dlg.pick_color"))
        if col.isValid():
            while len(cols) < 2:
                cols.append(cols[0])
            cols[target] = col.name()
            self.cfg["custom_colors"] = cols
            self.cfg["theme"] = "custom"
            self.cmb_theme.setCurrentIndex(max(0, self.cmb_theme.findData("custom")))
            self._update_color_buttons()
            self._refresh_theme_icon()
            self._mark()

    def _refresh_theme_icon(self):
        for i in range(self.cmb_theme.count()):
            if self.cmb_theme.itemData(i) == "custom":
                self.cmb_theme.setItemIcon(i, theme_strip(self.cfg["custom_colors"]))

    def _mark(self, *args):
        if self._loading:
            return
        c = self.cfg
        c["theme"] = self.cmb_theme.currentData()
        c["flow_speed"] = self.sld_flow.value() / 100.0
        c["font_family"] = self.cmb_font.currentFont().family()
        c["font_weight"] = self.cmb_weight.currentData()
        c["start_size"] = self.sld_start.value()
        c["peak_size"] = max(self.sld_peak.value(), self.sld_start.value())
        c["opacity"] = self.sld_opacity.value()
        c["glow"] = self.sld_glow.value()
        c["shockwave"] = self.chk_shock.isChecked()
        c["in_anim"] = self.cmb_in.currentData()
        c["out_anim"] = self.cmb_out.currentData()
        c["in_ms"] = self.sld_in.value()
        c["hold_ms"] = self.sld_hold.value()
        c["out_ms"] = self.sld_out.value()
        c["enabled"] = self.chk_enabled.isChecked()
        c["prefer_caret"] = self.chk_caret.isChecked()

        self._update_color_buttons()
        for s, l in (
            (self.sld_flow, self.lbl_flow),
            (self.sld_start, self.lbl_start),
            (self.sld_peak, self.lbl_peak),
            (self.sld_opacity, self.lbl_opacity),
            (self.sld_glow, self.lbl_glow),
            (self.sld_in, self.lbl_in),
            (self.sld_hold, self.lbl_hold),
            (self.sld_out, self.lbl_out),
        ):
            self._sync_label(s, l)

        self.on_change()

    def _on_autostart(self, checked):
        if self._loading:
            return
        ok = cfgmod.set_autostart(bool(checked))
        if not ok:
            self._loading = True
            self.chk_auto.setChecked(not checked)
            self._loading = False

    def _repaint_preview(self):
        if self.isVisible():
            self.preview.update()

    def _apply_preset(self, preset):
        self.cfg.update(preset)
        self._refresh_widgets()
        self.on_change()

    def _reset(self):
        mode = self.cfg.get("ui_mode", "dark")
        lang = self.cfg.get("language", i18n.get_lang())
        self.cfg.clear()
        self.cfg.update(copy.deepcopy(cfgmod.DEFAULTS))
        self.cfg["ui_mode"] = mode
        self.cfg["language"] = lang
        self._refresh_widgets()
        self._refresh_theme_icon()
        self._apply_theme()
        self.on_change()

    # ---------------- 无边框拖动 ----------------
    def eventFilter(self, obj, ev):
        t = ev.type()
        if t == QEvent.Type.MouseButtonPress and ev.button() == Qt.MouseButton.LeftButton:
            self._drag_off = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif t == QEvent.Type.MouseMove and self._drag_off is not None:
            self.move(ev.globalPosition().toPoint() - self._drag_off)
        elif t == QEvent.Type.MouseButtonRelease:
            self._drag_off = None
        return super().eventFilter(obj, ev)
