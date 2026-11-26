#!/usr/bin/env python3
"""The World in One Page - Wednesday, 25 November 2026.

A deterministic, standard-library-only program that draws a newspaper
front page summing up the world news of Wednesday 25 November 2026 and
writes it to <MAKEFUN_OUTPUT_DIR>/entry.png (default /output).

No network, no randomness, no timestamps: running it twice produces
byte-identical output.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------------------
# 5x7 bitmap font, defined glyph by glyph in this file.
# Each glyph is 7 rows of 5 characters: '#' is ink, '.' is blank.
# ---------------------------------------------------------------------------

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "·": (".....", ".....", ".....", ".##..", ".....", ".....", "....."),
}

BLANK = (".....",) * 7


def glyph(ch):
    return FONT.get(ch, BLANK)


# ---------------------------------------------------------------------------
# Canvas: a plain RGB raster with simple drawing primitives.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = color[0]
                self.px[i + 1] = color[1]
                self.px[i + 2] = color[2]

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int((r * r - dy * dy) ** 0.5)
            for x in range(cx - dx, cx + dx + 1):
                self.set_px(x, y, color)

    def fill_poly(self, pts, color):
        ys = [p[1] for p in pts]
        ymin, ymax = min(ys), max(ys)
        n = len(pts)
        for y in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if y1 == y2:
                    continue
                if min(y1, y2) <= y < max(y1, y2):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                x0 = int(round(xs[i]))
                x1 = int(round(xs[i + 1]))
                for x in range(x0, x1 + 1):
                    self.set_px(x, y, color)

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, color, align="left"):
        s = s.upper()
        w = self.text_width(s, scale)
        if align == "center":
            x -= w // 2
        elif align == "right":
            x -= w
        cx = x
        for ch in s:
            g = glyph(ch)
            for r in range(7):
                row = g[r]
                for c in range(5):
                    if row[c] == "#":
                        self.rect(cx + c * scale, y + r * scale,
                                  scale, scale, color)
            cx += 6 * scale


# ---------------------------------------------------------------------------
# PNG encoder (stdlib only): signature, IHDR, one IDAT, IEND.
# ---------------------------------------------------------------------------

def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

PAPER = (247, 243, 234)
INK = (26, 26, 26)
GREY = (74, 74, 74)
RED = (178, 34, 34)
SKY_TOP = (24, 44, 74)
SKY_MID = (52, 84, 122)
SKY_LOW = (96, 128, 158)
SEA = (22, 62, 92)
SEA_LINE = (120, 165, 195)
SUN = (242, 214, 130)
HULL = (32, 32, 38)
SUPER = (232, 228, 220)
CONTAINER_A = (196, 74, 52)
CONTAINER_B = (52, 110, 84)
CONTAINER_C = (214, 164, 62)
FLAME_OUT = (226, 88, 26)
FLAME_MID = (244, 150, 34)
FLAME_IN = (250, 214, 92)
SMOKE = (112, 112, 112)
SMOKE_LIGHT = (150, 150, 150)
MINE = (14, 14, 14)

MX = 24            # left margin
CW = 976           # content width (24 .. 1000)

# ---------------------------------------------------------------------------
# The day's news, verified against reports of 25 November 2026.
# Each story is three lines of at most 26 characters at scale 3.
# ---------------------------------------------------------------------------

HEADLINE_KICKER = "STRAIT OF HORMUZ · IRAN WAR AT SEA"
HEADLINE = ["TWO MORE TANKERS HIT MINES",
            "AND BURN IN THE STRAIT OF HORMUZ"]
DECK = ["IRAN'S GUARDS SAY TWO TANKERS STRUCK MINES ON AN",
        "UNAUTHORISED ROUTE; A GAS TANKER ALSO CAUGHT FIRE"]

STORIES = [
    ("HOUTHIS HIT SAUDI REFINERY",
     "THE GROUP SAYS IT STRUCK",
     "RAS TANURA; FIRES ERUPTED"),
    ("HAMAS SECURITY CHIEF SLAIN",
     "STRIKE IN GAZA KILLS FOUR",
     "ABUELOUF, WIFE, 2 CHILDREN"),
    ("HUAWEI GUILTY IN U.S. COURT",
     "JURY FINDS HUAWEI GUILTY",
     "TRADE THEFT AND BANK FRAUD"),
    ("COP31 ENDS WITH NO DEAL",
     "POPE LEO WARNS AS CLIMATE",
     "TALKS FAIL TO AGREE A PACT"),
    ("FIRST FOREIGN ASTRONAUT",
     "PAKISTANI FLIES ABOARD",
     "SHENZHOU-24 DOCKS IN ORBIT"),
    ("SOLOMONS BAR FOREIGN BASES",
     "TREATY WITH AUSTRALIA BARS",
     "ANY FOREIGN MILITARY BASE"),
    ("19 KILLED IN SUDAN STRIKES",
     "RSF DRONES HIT TWO CITIES",
     "20 WOUNDED, LAWYERS SAY"),
    ("CIA SYSTEMS BREACHED",
     "HACKERS HIT UNCLASSIFIED",
     "CIA AND SPY CHIEF NETWORKS"),
]

BRIEFS = ["GARMENT PAY +36% IN BANGLADESH · SINNER KNEE OP",
          "GIULIANI MEDAL OF FREEDOM · REAL MADRID 5-1 PSV"]

MARKETS = ["MARKETS: DOW 50,182.95 +0.33% · BRENT $94.61 +3.51%",
           "S&P 500 7,182.78 -0.25% · NASDAQ 23,585.80 -0.62%",
           "GOLD $3,535.80 -0.73% · WTI $83.68 +1.99%"]


# ---------------------------------------------------------------------------
# Illustration: a tanker burning in the Strait of Hormuz.
# ---------------------------------------------------------------------------

def draw_art(cv, x, y, w, h):
    # Sky in three bands.
    cv.rect(x, y, w, 62, SKY_TOP)
    cv.rect(x, y + 62, w, 34, SKY_MID)
    cv.rect(x, y + 96, w, 22, SKY_LOW)
    # Sun.
    cv.fill_circle(x + w - 96, y + 34, 20, SUN)
    # Birds.
    for bx, by in ((x + 120, y + 26), (x + 150, y + 40), (x + 700, y + 22)):
        cv.line(bx - 8, by, bx, by - 6, INK)
        cv.line(bx, by - 6, bx + 8, by, INK)
    # Sea.
    cv.rect(x, y + 118, w, h - 118, SEA)
    for wy in (y + 132, y + 150, y + 168):
        for wx in range(x + 8, x + w - 40, 64):
            cv.line(wx, wy, wx + 34, wy, SEA_LINE)
    # Distant tanker silhouette on the horizon.
    cv.rect(x + 700, y + 96, 150, 22, (40, 66, 92))
    cv.rect(x + 730, y + 80, 34, 16, (40, 66, 92))
    cv.rect(x + 700, y + 118, 150, 4, (40, 66, 92))
    # Main tanker: hull, bow, superstructure, funnel, containers.
    cv.fill_poly([(x + 120, y + 138), (x + 640, y + 138),
                  (x + 600, y + 176), (x + 150, y + 176)], HULL)
    cv.rect(x + 150, y + 138, 450, 4, (60, 60, 66))
    cv.rect(x + 160, y + 96, 66, 42, SUPER)
    for wy in (y + 102, y + 116):
        for wx in range(x + 166, x + 220, 14):
            cv.rect(wx, wy, 8, 6, (30, 60, 90))
    cv.rect(x + 236, y + 104, 16, 34, (90, 30, 30))
    cv.rect(x + 236, y + 100, 16, 6, (60, 20, 20))
    # Containers on deck.
    cv.rect(x + 300, y + 112, 60, 26, CONTAINER_A)
    cv.rect(x + 366, y + 112, 60, 26, CONTAINER_B)
    cv.rect(x + 432, y + 112, 60, 26, CONTAINER_C)
    cv.rect(x + 300, y + 100, 60, 12, CONTAINER_B)
    cv.rect(x + 366, y + 100, 60, 12, CONTAINER_C)
    # Flames bursting from mid-ship.
    for pts, col in (
        ([(x + 500, y + 140), (x + 520, y + 60), (x + 540, y + 110),
          (x + 560, y + 44), (x + 580, y + 104), (x + 600, y + 66),
          (x + 620, y + 140)], FLAME_OUT),
        ([(x + 520, y + 140), (x + 534, y + 78), (x + 550, y + 116),
          (x + 566, y + 66), (x + 582, y + 118), (x + 598, y + 84),
          (x + 606, y + 140)], FLAME_MID),
        ([(x + 540, y + 140), (x + 548, y + 98), (x + 560, y + 122),
          (x + 572, y + 92), (x + 584, y + 140)], FLAME_IN),
    ):
        cv.fill_poly(pts, col)
    # Smoke drifting up and right.
    for cx, cy, r, col in ((x + 560, y + 30, 16, SMOKE),
                           (x + 596, y + 16, 20, SMOKE_LIGHT),
                           (x + 636, y + 26, 14, SMOKE),
                           (x + 620, y + 44, 12, SMOKE_LIGHT)):
        cv.fill_circle(cx, cy, r, col)
    # Naval mines in the foreground water.
    for mx, my in ((x + 800, y + 158), (x + 880, y + 166)):
        for dx, dy in ((-16, 0), (16, 0), (0, -16), (0, 16),
                       (-11, -11), (11, -11), (-11, 11), (11, 11)):
            cv.line(mx, my, mx + dx, my + dy, MINE)
        cv.fill_circle(mx, my, 11, MINE)
    # Frame.
    cv.rect(x, y, w, 3, INK)
    cv.rect(x, y + h - 3, w, 3, INK)
    cv.rect(x, y, 3, h, INK)
    cv.rect(x + w - 3, y, 3, h, INK)


# ---------------------------------------------------------------------------
# Page layout.
# ---------------------------------------------------------------------------

def build():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(MX, 16, CW, 3, INK)
    cv.text(512, 28, "THE WORLD IN ONE PAGE", 5, INK, align="center")
    cv.text(512, 74, "WEDNESDAY, 25 NOVEMBER 2026", 4, RED, align="center")
    cv.rect(MX, 108, CW, 4, INK)
    cv.rect(MX, 116, CW, 1, INK)

    # Headline block.
    cv.text(MX, 132, HEADLINE_KICKER, 3, RED)
    cv.text(MX, 160, HEADLINE[0], 4, INK)
    cv.text(MX, 196, HEADLINE[1], 4, INK)
    cv.text(MX, 240, DECK[0], 3, GREY)
    cv.text(MX, 264, DECK[1], 3, GREY)

    # Illustration.
    draw_art(cv, MX, 296, CW, 180)

    # Story grid: 2 columns x 4 rows.
    gy = 490
    row_h = 86
    row_gap = 4
    col_w = 482
    for i, story in enumerate(STORIES):
        col = i % 2
        row = i // 2
        sx = MX + col * (col_w + 12)
        sy = gy + row * (row_h + row_gap)
        cv.rect(sx, sy, col_w, 4, RED)
        cv.text(sx, sy + 12, story[0], 3, INK)
        cv.text(sx, sy + 36, story[1], 3, GREY)
        cv.text(sx, sy + 60, story[2], 3, GREY)

    # Briefs.
    by = 856
    cv.text(MX, by, "IN BRIEF", 3, RED)
    cv.rect(MX + 170, by + 10, CW - 170, 2, INK)
    cv.text(MX, by + 28, BRIEFS[0], 3, INK)
    cv.text(MX, by + 52, BRIEFS[1], 3, INK)

    # Markets.
    my = 934
    cv.rect(MX, my - 8, CW, 2, INK)
    for j, line in enumerate(MARKETS):
        cv.text(MX, my + j * 24, line, 3, INK)

    # Footer rule.
    cv.rect(MX, 1012, CW, 2, INK)
    return encode_png(cv)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(build())


if __name__ == "__main__":
    main()
