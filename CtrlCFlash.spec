# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置

体积优化思路：PyInstaller 的 Qt 钩子会把整包 PySide6 依赖都塞进来，
其中一大半是这个托盘小工具永远用不到的。这里在 Analysis 之后按文件名
把它们从 TOC 里摘掉，44MB -> 25MB 左右，功能和界面完全不变。

被摘掉的东西及理由：
  opengl32sw.dll         纯软件 OpenGL 兜底（19.7MB），只用 QPainter 光栅绘制，用不到
  Qt6Quick/Qml/QmlModels 由虚拟键盘输入法插件带进来的，本程序不用 QML
  Qt6VirtualKeyboard     同上
  Qt6Pdf + qpdf 插件     不显示 PDF
  libcrypto/libssl/tls   只走 QLocalServer 命名管道做单实例，不碰网络 TLS
  translations/*.qm      Qt 自带 20 多种语言的按钮文案，只留简体中文
  tiff/webp/jpeg 插件    只保存 PNG
"""

import os

BLOCK_EXACT = {
    "pyside6/opengl32sw.dll",
    "pyside6/qt6quick.dll",
    "pyside6/qt6qml.dll",
    "pyside6/qt6qmlmodels.dll",
    "pyside6/qt6virtualkeyboard.dll",
    "pyside6/qt6pdf.dll",
    "libcrypto-3-x64.dll",
    "libssl-3-x64.dll",
    "pyside6/plugins/imageformats/qpdf.dll",
    "pyside6/plugins/imageformats/qtiff.dll",
    "pyside6/plugins/imageformats/qwebp.dll",
    "pyside6/plugins/imageformats/qjpeg.dll",
}

# 保留的 Qt 自带翻译（QColorDialog / QMessageBox 的标准按钮还靠它）
KEEP_TRANSLATIONS = {"qtbase_zh_cn.qm", "qt_zh_cn.qm"}


def _norm(dest):
    return dest.replace("\\", "/").lstrip("./").lower()


def _drop(dest):
    d = _norm(dest)
    if d in BLOCK_EXACT:
        return True
    if d.startswith("pyside6/plugins/tls/"):
        return True
    if d.startswith("pyside6/plugins/platforminputcontexts/"):
        return True
    if d.startswith("pyside6/translations/"):
        return os.path.basename(d) not in KEEP_TRANSLATIONS
    return False


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.Qt3DCore",
        "PySide6.QtMultimedia",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "tkinter",
    ],
    noarchive=False,
)

before = len(a.binaries)
a.binaries = [x for x in a.binaries if not _drop(x[0])]
a.datas = [x for x in a.datas if not _drop(x[0])]
print("[spec] binaries %d -> %d, datas %d" % (before, len(a.binaries), len(a.datas)))

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CtrlCFlash",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.join(SPECPATH, "app.ico"),
)
