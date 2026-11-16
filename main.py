# -*- coding: utf-8 -*-
"""
CtrlCFlash - 按下 Ctrl+C 时在光标处炸出一个炫彩大 C
入口：托盘常驻 + 全局按键监听
"""

import ctypes
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
VENDOR = os.path.join(HERE, "vendor")
if os.path.isdir(VENDOR) and VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

import cfg as cfgmod
import i18n
from i18n import t
from keyboard_hook import CopyKeyWatcher
from overlay import FlashOverlay
from themes import theme_colors

SOCKET_NAME = "CtrlCFlash-SingleInstance-9f2c"


def log_error(msg):
    try:
        with open(os.path.join(cfgmod.config_dir(), "error.log"), "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def make_tray_icon(colors, size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    grad = QLinearGradient(0, 0, size, size)
    n = max(1, len(colors))
    for i, c in enumerate(colors):
        grad.setColorAt(i / n, QColor(c))
    grad.setColorAt(1.0, QColor(colors[0]))

    font = QFont("Arial")
    font.setPixelSize(int(size * 0.72))
    font.setBold(True)
    font.setWeight(QFont.Weight.Black)
    path = QPainterPath()
    path.addText(0, 0, font, "C")
    br = path.boundingRect()
    path.translate(size / 2 - br.center().x(), size / 2 - br.center().y())

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(grad)
    p.drawPath(path)
    p.end()
    return QIcon(pm)


class App:
    def __init__(self, app):
        self.app = app
        self.cfg = cfgmod.load()
        i18n.set_lang(self.cfg.get("language"))
        self.settings = None

        self.overlay = FlashOverlay(lambda: self.cfg)

        self.watcher = CopyKeyWatcher()
        self.hook_ok = self.watcher.start()

        self.poll = QTimer()
        self.poll.setInterval(30)
        self.poll.timeout.connect(self._drain)
        self.poll.start()

        # 闲置一会儿就把工作集还给系统：托盘程序大部分时间什么都不干，
        # 没必要一直押着几十兆物理内存（再动起来时系统会自动换回来）。
        self._trim = QTimer()
        self._trim.setSingleShot(True)
        self._trim.setInterval(60000)
        self._trim.timeout.connect(self._trim_memory)
        self._trim.start()

        self._build_tray()
        self._listen_single_instance()

        # 如果之前设过开机自启，顺手把注册表里的路径刷新成当前 exe 位置，
        # 免得用户把 exe 挪了地方之后自启失效。
        if cfgmod.is_autostart_enabled():
            cfgmod.set_autostart(True)

        app.aboutToQuit.connect(self._shutdown)

    # ---------------- 托盘 ----------------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(make_tray_icon(theme_colors(self.cfg)), self.app)
        self.tray.setToolTip(t("tray.tip"))

        menu = QMenu()

        self.act_toggle = QAction(t("tray.enable"), menu)
        self.act_toggle.setCheckable(True)
        self.act_toggle.setChecked(bool(self.cfg.get("enabled", True)))
        self.act_toggle.triggered.connect(self._toggle_enabled)
        menu.addAction(self.act_toggle)

        self.act_preview = QAction(t("tray.preview"), menu)
        self.act_preview.triggered.connect(self.preview)
        menu.addAction(self.act_preview)

        menu.addSeparator()

        self.act_settings = QAction(t("tray.settings"), menu)
        self.act_settings.triggered.connect(self.open_settings)
        menu.addAction(self.act_settings)

        self.act_auto = QAction(t("tray.autostart"), menu)
        self.act_auto.setCheckable(True)
        self.act_auto.setChecked(cfgmod.is_autostart_enabled())
        self.act_auto.triggered.connect(self._toggle_autostart)
        menu.addAction(self.act_auto)

        menu.addSeparator()

        self.act_quit = QAction(t("tray.quit"), menu)
        self.act_quit.triggered.connect(self.app.quit)
        menu.addAction(self.act_quit)

        self.menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def preview(self):
        self.overlay.preview_center()
        self._trim.start()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.preview()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings()

    def _toggle_enabled(self, checked):
        self.cfg["enabled"] = bool(checked)
        cfgmod.save(self.cfg)
        if not checked:
            self.overlay.set_paused()
            self._trim.start()

    def _retranslate(self):
        """语言切换后刷新托盘菜单和提示。"""
        self.tray.setToolTip(t("tray.tip"))
        self.act_toggle.setText(t("tray.enable"))
        self.act_preview.setText(t("tray.preview"))
        self.act_settings.setText(t("tray.settings"))
        self.act_auto.setText(t("tray.autostart"))
        self.act_quit.setText(t("tray.quit"))

    def _toggle_autostart(self, checked):
        ok = cfgmod.set_autostart(bool(checked))
        if not ok:
            self.act_auto.setChecked(not checked)
            QMessageBox.warning(None, t("app.title"), t("msg.autostart_fail"))
        else:
            self.cfg["autostart"] = bool(checked)
            cfgmod.save(self.cfg)

    # ---------------- 设置窗口 ----------------
    def open_settings(self):
        from settings_ui import SettingsDialog

        self._trim.stop()
        # 关掉上一个窗口对象：设置面板带一整棵控件树 + 字体枚举，
        # 常驻在后台要多吃 20MB，用完就让它被回收。
        if self.settings is not None:
            try:
                self.settings.close()
            except RuntimeError:
                pass
            self.settings = None

        dlg = SettingsDialog(self.cfg, on_change=self._on_cfg_change,
                             on_preview=self.preview)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dlg.destroyed.connect(self._on_settings_destroyed)
        self.settings = dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _on_settings_destroyed(self, *_args):
        self.settings = None
        self._trim.start()

    # ---------------- 让出内存 ----------------
    def _trim_memory(self):
        if self.settings is not None:
            # 设置窗口开着就别裁剪，免得拖动时卡顿
            self._trim.start()
            return
        try:
            k32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            k32.GetCurrentProcess.restype = ctypes.c_void_p
            psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
            psapi.EmptyWorkingSet.restype = ctypes.c_bool
            psapi.EmptyWorkingSet(k32.GetCurrentProcess())
        except Exception:
            pass

    def _on_cfg_change(self):
        cfgmod.save(self.cfg)
        lang = self.cfg.get("language")
        if lang and lang != i18n.get_lang():
            i18n.set_lang(lang)
            self._retranslate()
        self.tray.setIcon(make_tray_icon(theme_colors(self.cfg)))
        if self.act_toggle.isChecked() != bool(self.cfg.get("enabled", True)):
            self.act_toggle.setChecked(bool(self.cfg.get("enabled", True)))

    # ---------------- 事件 ----------------
    def _drain(self):
        for pos, source, _ts in self.watcher.pop_events():
            self.overlay.flash(pos)
            self._trim.start()

    def _listen_single_instance(self):
        QLocalServer.removeServer(SOCKET_NAME)
        self.server = QLocalServer()
        self.server.listen(SOCKET_NAME)
        self.server.newConnection.connect(self._on_second_instance)

    def _on_second_instance(self):
        conn = self.server.nextPendingConnection()
        if conn:
            conn.disconnectFromServer()
        self.open_settings()

    def _shutdown(self):
        try:
            self.watcher.stop()
        except Exception:
            pass
        try:
            self.server.close()
            QLocalServer.removeServer(SOCKET_NAME)
        except Exception:
            pass


def already_running():
    s = QLocalSocket()
    s.connectToServer(SOCKET_NAME)
    if s.waitForConnected(400):
        s.write(b"show")
        s.flush()
        s.waitForBytesWritten(300)
        s.disconnectFromServer()
        return True
    return False


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("CtrlCFlash")

    if already_running():
        return 0

    def excepthook(etype, value, tb):
        log_error("".join(traceback.format_exception(etype, value, tb)))

    sys.excepthook = excepthook

    instance = App(app)

    if not instance.hook_ok:
        instance.tray.showMessage(
            t("app.title"),
            t("msg.hook_fail"),
            QSystemTrayIcon.MessageIcon.Warning,
            6000,
        )

    # 首次运行给个提示
    if not os.path.exists(os.path.join(cfgmod.config_dir(), ".welcomed")):
        try:
            with open(os.path.join(cfgmod.config_dir(), ".welcomed"), "w", encoding="utf-8") as f:
                f.write("1")
        except Exception:
            pass
        instance.tray.showMessage(
            t("app.title"),
            t("msg.welcome"),
            QSystemTrayIcon.MessageIcon.Information,
            8000,
        )

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
