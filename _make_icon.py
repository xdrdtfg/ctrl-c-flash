# -*- coding: utf-8 -*-
"""生成多尺寸 app.ico"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "vendor"))

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QApplication

app = QApplication([])

COLORS = ["#FF0057", "#FF8A00", "#FFE600", "#2BFF88", "#00D9FF", "#7B5CFF", "#FF28C8"]


def render(size):
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    font = QFont("Arial")
    font.setPixelSize(int(size * 0.92))
    font.setWeight(QFont.Weight.Black)
    path = QPainterPath()
    path.addText(0, 0, font, "C")
    br = path.boundingRect()
    path.translate(size / 2 - br.center().x(), size / 2 - br.center().y())
    br = path.boundingRect()

    grad = QLinearGradient(br.left(), br.top(), br.right(), br.bottom())
    n = len(COLORS)
    for i, c in enumerate(COLORS):
        grad.setColorAt(i / n, QColor(c))
    grad.setColorAt(1.0, QColor(COLORS[0]))

    if size >= 32:
        pen = QPen(QColor(255, 255, 255, 110), max(1.0, size * 0.02))
        p.strokePath(path, pen)
    p.fillPath(path, QBrush(grad))
    p.end()
    return img


sizes = [16, 24, 32, 48, 64, 128, 256]
blobs = []
for s in sizes:
    img = render(s)
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    blobs.append(bytes(ba))

count = len(sizes)
header = struct.pack("<HHH", 0, 1, count)
offset = 6 + 16 * count
entries = b""
payload = b""
for s, blob in zip(sizes, blobs):
    w = 0 if s >= 256 else s
    entries += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(blob), offset)
    offset += len(blob)
    payload += blob

out = os.path.join(HERE, "app.ico")
with open(out, "wb") as f:
    f.write(header + entries + payload)
print("wrote", out, os.path.getsize(out), "bytes")

# 顺便存一张预览图
render(256).save(os.path.join(HERE, "icon_preview.png"))
