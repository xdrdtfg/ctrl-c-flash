# -*- coding: utf-8 -*-
"""
炫彩大 C 浮层

一个无边框、置顶、点击穿透的透明窗口，在光标处渲染一个渐变大字母 C，
并按配置播放入场 / 停留 / 出场动画。
"""

import math
import time

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import QWidget

from themes import theme_colors

TEXT = "C"
BASE_PX = 200.0  # 归一化基准：字形高度被缩放到这个像素数

WEIGHT_MAP = {
    "normal": QFont.Weight.Normal,
    "bold": QFont.Weight.Bold,
    "black": QFont.Weight.Black,
}


# ---------------- 缓动函数 ----------------

def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def ease_out_back(p, s=1.9):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1


def ease_out_elastic(p):
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * p) * math.sin((p * 10 - 0.75) * c4) + 1


def _to_logical(x, y):
    """Win32 物理像素 -> Qt 逻辑坐标（兼顾多屏不同缩放）。"""
    for scr in QGuiApplication.screens():
        dpr = scr.devicePixelRatio() or 1.0
        g = scr.geometry()
        px0 = round(g.x() * dpr)
        py0 = round(g.y() * dpr)
        px1 = px0 + round(g.width() * dpr)
        py1 = py0 + round(g.height() * dpr)
        if px0 <= x <= px1 and py0 <= y <= py1:
            return g.x() + (x - px0) / dpr, g.y() + (y - py0) / dpr
    scr = QGuiApplication.primaryScreen()
    d = (scr.devicePixelRatio() if scr else 1.0) or 1.0
    return x / d, y / d


def build_letter_path(family, weight, text=TEXT, base=BASE_PX):
    """构建字形路径，并把字形高度归一化到 base 像素，便于按高度缩放。"""
    font = QFont(family)
    font.setPixelSize(int(base))
    font.setWeight(WEIGHT_MAP.get(weight, QFont.Weight.Black))
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    path = QPainterPath()
    path.addText(0, 0, font, text)
    br = path.boundingRect()
    if br.height() > 0.01:
        k = base / br.height()
        path = QTransform().scale(k, k).map(path)
    br = path.boundingRect()
    path.translate(-br.center().x(), -br.center().y())
    return path


def _brightest(cols):
    """取主题里最跳的颜色（重饱和、兼顾亮度），白底黑底都看得见。"""
    def key(c):
        q = QColor(c)
        return q.saturationF() * 0.75 + q.valueF() * 0.25
    return max(cols, key=key)


class FlashOverlay(QWidget):
    def __init__(self, get_cfg):
        super().__init__(None)
        self.get_cfg = get_cfg

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._t0 = None
        self._path = None
        self._path_key = None

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    # ---------------- 几何 ----------------

    @staticmethod
    def _window_side(cfg):
        peak = cfg["peak_size"]
        glow = cfg["glow"]
        return int(max(240, peak * 1.42 + glow * 2.0 + 24))

    def _build_path(self, cfg):
        key = (cfg["font_family"], cfg["font_weight"])
        if key == self._path_key and self._path is not None:
            return
        self._path = build_letter_path(cfg["font_family"], cfg["font_weight"])
        self._path_key = key

    # ---------------- 动画状态 ----------------

    def _state(self, t):
        cfg = self.get_cfg()
        t_in = max(1, cfg["in_ms"])
        t_hold = cfg["hold_ms"]
        t_out = max(1, cfg["out_ms"])
        start, peak = float(cfg["start_size"]), float(cfg["peak_size"])

        size = peak
        alpha = 1.0
        angle = 0.0
        dx = dy = 0.0

        if t < t_in:
            p = t / t_in
            mode = cfg["in_anim"]
            if mode == "rotate":
                e = ease_out_back(p, 1.3)
                size = start + (peak - start) * e
                angle = -220.0 * (1 - ease_out_cubic(p))
                alpha = min(1.0, p * 2.6)
            elif mode == "fade":
                size = start + (peak - start) * ease_out_cubic(p)
                alpha = p
            elif mode == "blink":
                size = start + (peak - start) * ease_out_cubic(p)
                alpha = min(1.0, p * 5) * (0.18 + 0.82 * abs(math.sin(p * math.pi * 4)))
            elif mode == "bounce":
                size = start + (peak - start) * ease_out_elastic(p)
                alpha = min(1.0, p * 3.0)
            elif mode == "slam":
                size = peak * (1.0 + 1.15 * (1 - ease_out_cubic(p)))
                alpha = min(1.0, p * 4.0)
            else:  # spray
                size = start + (peak - start) * ease_out_back(p)
                alpha = min(1.0, p * 2.2)
        elif t < t_in + t_hold:
            p = (t - t_in) / max(1, t_hold)
            size = peak * (1.0 + 0.015 * math.sin(p * math.pi * 2))
            alpha = 1.0
        else:
            p = min(1.0, (t - t_in - t_hold) / t_out)
            mode = cfg["out_anim"]
            if mode == "expand":
                size = peak * (1 + 0.75 * p)
                alpha = (1 - p) ** 0.8
            elif mode == "shrink":
                size = peak * (1 - 0.94 * p)
                alpha = (1 - p) ** 0.7
            elif mode == "spin":
                angle = 200.0 * p
                size = peak * (1 - 0.65 * p)
                alpha = 1 - p
            elif mode == "blink":
                size = peak * (1 - 0.25 * p)
                alpha = (1 - p) * (0.25 + 0.75 * abs(math.cos(p * math.pi * 4)))
            elif mode == "float":
                dy = -80.0 * p
                size = peak * (1 + 0.12 * p)
                alpha = 1 - p
            else:  # fade
                alpha = 1 - p

        shock = None
        if cfg.get("shockwave"):
            s0 = t_in * 0.42
            span = 460.0
            if s0 <= t <= s0 + span:
                shock = (t - s0) / span

        flash = max(0.0, 1.0 - t / 110.0) if t < 110 else 0.0

        return {
            "size": max(1.0, size),
            "alpha": max(0.0, min(1.0, alpha)),
            "angle": angle,
            "dx": dx,
            "dy": dy,
            "shock": shock,
            "flash": flash,
            "t": t,
        }

    # ---------------- 绘制 ----------------

    def _brush(self, cfg, t):
        cols = theme_colors(cfg)
        speed = cfg.get("flow_speed", 1.0)
        hue = (t * 0.001 * 260.0 * speed) % 360.0
        grad = QConicalGradient(QPointF(0, 0), hue)
        n = len(cols)
        for i, c in enumerate(cols):
            grad.setColorAt(i / n, QColor(c))
        grad.setColorAt(1.0, QColor(cols[0]))
        return QBrush(grad), QColor(cols[0])

    def paintEvent(self, ev):
        if self._t0 is None:
            return
        cfg = self.get_cfg()
        t = (time.monotonic() - self._t0) * 1000.0
        st = self._state(t)
        if st["alpha"] <= 0.003:
            return

        self._build_path(cfg)
        if self._path is None:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        opacity = cfg["opacity"] / 100.0
        alpha = st["alpha"] * opacity

        if st["shock"] is not None:
            self._draw_shock(p, w / 2, w / 2, st["shock"], cfg, alpha)

        p.save()
        p.translate(w / 2 + st["dx"], w / 2 + st["dy"])
        if st["angle"]:
            p.rotate(st["angle"])
        s = st["size"] / BASE_PX
        p.scale(s, s)

        brush, main = self._brush(cfg, t)
        inv = 1.0 / max(s, 0.02)

        # 辉光（SourceOver：白底不脏，深底也够亮）
        glow = cfg["glow"]
        if glow > 0:
            halo = QColor(main).lighter(145)
            for mult, a in ((1.7, 0.085), (1.05, 0.12), (0.55, 0.17)):
                col = QColor(halo)
                col.setAlphaF(min(1.0, a * alpha))
                pen = QPen(col, max(0.5, glow * mult * inv))
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.strokePath(self._path, pen)

        # 主体
        p.setOpacity(alpha)
        p.fillPath(self._path, brush)

        # 入场闪白
        if st["flash"] > 0.01:
            white = QColor(255, 255, 255)
            white.setAlphaF(min(1.0, st["flash"] * 0.75))
            p.fillPath(self._path, QBrush(white))

        # 亮边勾形
        pen = QPen(QColor(255, 255, 255, 48), max(0.6, 1.2 * inv))
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.strokePath(self._path, pen)

        p.restore()

    def _draw_shock(self, p, cx, cy, prog, cfg, alpha):
        if prog <= 0 or prog >= 1:
            return
        cols = theme_colors(cfg)
        peak = cfg["peak_size"]
        r = peak * (0.28 + 0.38 * ease_out_cubic(prog))
        a = (1 - prog) ** 1.6 * alpha * 0.38
        if a <= 0.01 or r <= 2:
            return

        col = QColor(_brightest(cols))
        grad = QRadialGradient(QPointF(cx, cy), r)
        c_in = QColor(col)
        c_in.setAlphaF(0.0)
        c_mid = QColor(col)
        c_mid.setAlphaF(0.0)
        c_ring = QColor(col)
        c_ring.setAlphaF(min(1.0, a))
        c_out = QColor(col)
        c_out.setAlphaF(0.0)
        grad.setColorAt(0.00, c_in)
        grad.setColorAt(0.80, c_mid)
        grad.setColorAt(0.94, c_ring)
        grad.setColorAt(1.00, c_out)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setBrush(Qt.BrushStyle.NoBrush)

    # ---------------- 播放控制 ----------------

    def flash(self, pos=None, preview=False):
        cfg = self.get_cfg()
        if not cfg["enabled"] and not preview:
            return

        if pos is None:
            scr = QGuiApplication.primaryScreen()
            g = scr.geometry()
            d = scr.devicePixelRatio() or 1.0
            pos = (int(g.center().x() * d), int(g.center().y() * d))

        lx, ly = _to_logical(int(pos[0]), int(pos[1]))
        side = self._window_side(cfg)
        self.resize(side, side)

        lift = cfg["peak_size"] * 0.16
        self.move(int(round(lx - side / 2)), int(round(ly - side / 2 - lift)))

        self._t0 = time.monotonic()
        self.show()
        self.raise_()
        self.update()
        if not self._timer.isActive():
            self._timer.start()

    def preview_center(self):
        scr = QGuiApplication.primaryScreen()
        g = scr.geometry()
        d = scr.devicePixelRatio() or 1.0
        self.flash((int(g.center().x() * d), int(g.center().y() * d)), preview=True)

    def _tick(self):
        if self._t0 is None:
            self._timer.stop()
            return
        cfg = self.get_cfg()
        total = cfg["in_ms"] + cfg["hold_ms"] + cfg["out_ms"] + 60
        if (time.monotonic() - self._t0) * 1000.0 > total:
            self._timer.stop()
            self._t0 = None
            self.hide()
            return
        self.update()

    def set_paused(self):
        self._timer.stop()
        self._t0 = None
        self.hide()
