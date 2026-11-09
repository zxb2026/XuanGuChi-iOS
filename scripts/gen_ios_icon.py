# -*- coding: utf-8 -*-
"""生成 App 图标 1024×1024（纯标准库，无 PIL 依赖，CI 上可直接跑）。

画面：深色行情底 + 涨红 K 线柱 + 金色趋势线，和 App 内 #12141A 主题一致。
输出：ios/XuanGuChi/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png
"""
import os
import struct
import zlib

SIZE = 1024
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "ios", "XuanGuChi", "Assets.xcassets", "AppIcon.appiconset", "AppIcon-1024.png")

BG_TOP = (0x1E, 0x22, 0x2C)
BG_BOT = (0x12, 0x14, 0x1A)
GRID = (0x23, 0x27, 0x32)
RED = (0xE6, 0x39, 0x32)
RED_DIM = (0xC9, 0x30, 0x2C)
GOLD = (0xFF, 0xC8, 0x57)

buf = bytearray(SIZE * SIZE * 3)


def clamp(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def put(x, y, rgb):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        i = (y * SIZE + x) * 3
        buf[i] = clamp(rgb[0])
        buf[i + 1] = clamp(rgb[1])
        buf[i + 2] = clamp(rgb[2])


def rect(x0, y0, x1, y1, rgb):
    for y in range(int(y0), int(y1)):
        row = (y * SIZE) * 3
        for x in range(int(x0), int(x1)):
            i = row + x * 3
            buf[i] = clamp(rgb[0])
            buf[i + 1] = clamp(rgb[1])
            buf[i + 2] = clamp(rgb[2])


def blend_rect(x0, y0, x1, y1, rgb, alpha):
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            i = (y * SIZE + x) * 3
            for k in range(3):
                buf[i + k] = clamp(buf[i + k] * (1 - alpha) + rgb[k] * alpha)


# 1) 竖向渐变底
for y in range(SIZE):
    t = y / (SIZE - 1)
    r = BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t
    g = BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t
    b = BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t
    row = y * SIZE * 3
    for x in range(SIZE):
        i = row + x * 3
        buf[i] = clamp(r)
        buf[i + 1] = clamp(g)
        buf[i + 2] = clamp(b)

# 2) 背景网格
for gy in range(64, SIZE, 128):
    blend_rect(0, gy, SIZE, gy + 2, GRID, 0.85)
for gx in range(64, SIZE, 128):
    blend_rect(gx, 0, gx + 2, SIZE, GRID, 0.55)

# 3) K 线柱（全部涨红，逐根抬高）
candles = [
    # (x_center, body_top, body_bottom)  —— top < bottom
    (268, 668, 742),
    (432, 596, 690),
    (596, 486, 604),
    (760, 368, 520),
]
CW = 86
for cx, top, bottom in candles:
    wick_x0 = cx - 7
    rect(wick_x0, top - 46, cx + 7, top, RED_DIM)          # 上影
    rect(wick_x0, bottom, cx + 7, bottom + 46, RED_DIM)     # 下影
    rect(cx - CW // 2, top, cx + CW // 2, bottom, RED)
    # 柱内高光，避免大色块发闷
    blend_rect(cx - CW // 2, top, cx - CW // 2 + 22, bottom, (255, 255, 255), 0.10)

# 4) 金色趋势线（从左下穿过各柱高点向上）
pts = [(212, 806), (268, 700), (432, 648), (596, 556), (760, 322), (838, 268)]
for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
    steps = max(abs(x1 - x0), abs(y1 - y0))
    for s in range(steps + 1):
        t = s / steps if steps else 0
        x = int(x0 + (x1 - x0) * t)
        y = int(y0 + (y1 - y0) * t)
        rect(x - 5, y - 5, x + 5, y + 5, GOLD)

# 5) 底部基准线
blend_rect(160, 862, 864, 868, GOLD, 0.55)

# 6) 四角轻微暗角
for y in range(SIZE):
    for x in range(0, SIZE, 1):
        dx = (x - SIZE / 2) / (SIZE / 2)
        dy = (y - SIZE / 2) / (SIZE / 2)
        d = (dx * dx + dy * dy) ** 0.5
        if d > 0.78:
            i = (y * SIZE + x) * 3
            k = min(1.0, (d - 0.78) / 0.5) * 0.35
            for c in range(3):
                buf[i + c] = clamp(buf[i + c] * (1 - k))


def write_png(path, data, width, height):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(data[y * width * 3:(y + 1) * width * 3])

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


write_png(OUT, buf, SIZE, SIZE)
print("icon written: %s (%d bytes)" % (OUT, os.path.getsize(OUT)))
