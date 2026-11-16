#!/usr/bin/env python3
"""Draw the v3 entry image: a colossal koi bursting out of a tiny goldfish bowl.

Everything is drawn from scratch with Pillow at 2x supersampling, then downscaled
for smooth edges. No input files, no randomness: the same run always writes the
same bytes. Output: entry.png, 1024x1024 RGB.
"""

from PIL import Image, ImageDraw, ImageFilter
import math

S = 2                      # supersample factor
W = H = 1024
CW, CH = W * S, H * S      # working canvas size

TEAL_TOP = (10, 61, 71)
TEAL_BOT = (4, 34, 43)
GOLD = (255, 214, 138)
SUN_CORE = (255, 236, 180)
ORANGE = (232, 93, 31)
ORANGE_SOFT = (240, 123, 45)
KOI_WHITE = (247, 243, 234)
KOI_SHADE = (216, 207, 192)
AQUA = (150, 220, 235)
WOOD = (107, 74, 47)
WOOD_LIGHT = (138, 103, 66)


def cubic(p0, p1, p2, p3, t):
    u = 1.0 - t
    return (
        u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
        u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1],
    )


def spine(n=90):
    """The koi's centre line: tail peduncle (in the bowl) up to the head tip."""
    p0 = (400 * S, 800 * S)
    p1 = (560 * S, 640 * S)
    p2 = (700 * S, 470 * S)
    p3 = (800 * S, 300 * S)
    return [cubic(p0, p1, p2, p3, i / (n - 1)) for i in range(n)]


def half_width(t):
    """Body half-width along the spine: narrow peduncle, fat belly, round head."""
    stops = [(0.00, 26), (0.12, 62), (0.30, 108), (0.52, 128),
             (0.72, 112), (0.88, 84), (1.00, 58)]
    for (t0, w0), (t1, w1) in zip(stops, stops[1:]):
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            f = f * f * (3 - 2 * f)
            return (w0 + (w1 - w0) * f) * S
    return 58 * S


def body_outline(pts):
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        t = i / (len(pts) - 1)
        x2, y2 = pts[min(i + 1, len(pts) - 1)]
        x1, y1 = pts[max(i - 1, 0)]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        w = half_width(t)
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def rotated_blob(layer, cx, cy, rx, ry, angle, fill):
    """Paste a rotated ellipse onto an RGBA layer."""
    tile = Image.new("RGBA", (int(rx * 4), int(ry * 4)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.ellipse([rx, ry, rx * 3, ry * 3], fill=fill)
    tile = tile.rotate(angle, resample=Image.BICUBIC, center=(rx * 2, ry * 2))
    layer.alpha_composite(tile, (int(cx - rx * 2), int(cy - ry * 2)))


def vgrad(size, top, bot):
    img = Image.new("RGB", (1, size[1]))
    px = img.load()
    for y in range(size[1]):
        f = y / max(size[1] - 1, 1)
        px[0, y] = tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3))
    return img.resize(size)


def radial_glow(size, cx, cy, radius, colour, peak=170):
    glow = Image.new("L", size, 0)
    gd = ImageDraw.Draw(glow)
    steps = 24
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(peak * (1 - i / steps) ** 2)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=a)
    glow = glow.filter(ImageFilter.GaussianBlur(radius / 6))
    tint = Image.new("RGB", size, colour)
    out = Image.new("RGB", size, (0, 0, 0))
    out.paste(tint, (0, 0), glow)
    return out


def make_background():
    bg = vgrad((CW, CH), TEAL_TOP, TEAL_BOT).convert("RGB")
    glow = radial_glow((CW, CH), 830 * S, 170 * S, 420 * S, (255, 200, 110), 120)
    bg = Image.blend(bg, Image.blend(bg, glow, 0.55), 0.5)
    # faint light rays fanning down-left from the sun
    rays = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for k, ang in enumerate((-32, -18, -4, 10)):
        a = math.radians(ang)
        x0, y0 = 830 * S, 170 * S
        x1 = x0 + math.cos(a + math.pi) * 900 * S
        y1 = y0 + math.sin(a + math.pi) * 900 * S
        rd.line([x0, y0, x1, y1], fill=(255, 230, 170, 26 - k * 3), width=26 * S)
    rays = rays.filter(ImageFilter.GaussianBlur(18 * S))
    bg = Image.alpha_composite(bg.convert("RGBA"), rays)
    # vignette: darken the corners so the fish pops
    vig = Image.new("L", (CW, CH), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-CW * 0.25, -CH * 0.25, CW * 1.25, CH * 1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220 * S))
    dark = Image.new("RGBA", (CW, CH), (2, 16, 22, 255))
    bg = Image.composite(bg, dark, vig)
    return bg


def make_sun(canvas):
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy, r = 830 * S, 170 * S, 92 * S
    d.ellipse([cx - r * 1.9, cy - r * 1.9, cx + r * 1.9, cy + r * 1.9],
              fill=(255, 210, 120, 26))
    d.ellipse([cx - r * 1.35, cy - r * 1.35, cx + r * 1.35, cy + r * 1.35],
              fill=(255, 220, 140, 60))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SUN_CORE + (255,))
    d.ellipse([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62],
              fill=(255, 248, 220, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(2 * S))
    canvas.alpha_composite(layer)
    # burst ring behind the koi's head: thin gold arcs
    ring = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    hx, hy = 780 * S, 320 * S
    for rr, al in ((120, 34), (150, 20), (180, 10)):
        rd.ellipse([hx - rr * S, hy - rr * S, hx + rr * S, hy + rr * S],
                   outline=(255, 214, 138, al), width=5 * S)
    ring = ring.filter(ImageFilter.GaussianBlur(3 * S))
    canvas.alpha_composite(ring)


def make_sill(canvas):
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top = 905 * S
    for y in range(top, CH):
        f = (y - top) / max(CH - top, 1)
        col = tuple(int(WOOD[i] + (WOOD_LIGHT[i] - WOOD[i]) * f) for i in range(3))
        d.line([(0, y), (CW, y)], fill=col + (255,))
    d.line([(0, top), (CW, top)], fill=(60, 40, 24, 255), width=4 * S)
    # wood grain
    for gy, amp in ((935, 6), (965, 9), (995, 5)):
        pts = []
        for x in range(0, CW + 1, 40 * S):
            pts.append((x, gy * S + amp * S * math.sin(x / (170 * S))))
        d.line(pts, fill=(70, 48, 28, 160), width=3 * S)
    canvas.alpha_composite(layer)


def make_bowl(canvas):
    cx, cy, r = 330 * S, 845 * S, 112 * S
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # soft shadow on the sill
    d.ellipse([cx - r * 1.15, cy + r * 0.72, cx + r * 1.15, cy + r * 0.98],
              fill=(0, 0, 0, 110))
    # glass body
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(150, 220, 235, 66))
    # water: lower two-thirds, wavy top edge
    water = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    wd = ImageDraw.Draw(water)
    wave = []
    for x in range(int(cx - r), int(cx + r) + 1, 8 * S):
        wave.append((x, cy - r * 0.18 + 7 * S * math.sin(x / (46 * S))))
    wave += [(cx + r, cy + r), (cx - r, cy + r)]
    wd.polygon(wave, fill=(90, 180, 200, 130))
    mask = Image.new("L", (CW, CH), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    water = Image.composite(water, Image.new("RGBA", (CW, CH), (0, 0, 0, 0)), mask)
    layer.alpha_composite(water)
    # rim + glass highlights
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(207, 238, 242, 235),
              width=6 * S)
    d.arc([cx - r * 0.82, cy - r * 0.86, cx - r * 0.05, cy + r * 0.28],
          start=105, end=205, fill=(255, 255, 255, 220), width=9 * S)
    d.arc([cx + r * 0.30, cy + r * 0.42, cx + r * 0.92, cy + r * 0.88],
          start=285, end=20, fill=(255, 255, 255, 130), width=6 * S)
    layer = layer.filter(ImageFilter.GaussianBlur(1 * S))
    canvas.alpha_composite(layer)
    return cx, cy, r


def make_koi(canvas):
    pts = spine()
    outline = body_outline(pts)

    body = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.polygon(outline, fill=KOI_WHITE + (255,))
    # belly shade along the lower edge
    shade = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for i, (x, y) in enumerate(pts):
        t = i / (len(pts) - 1)
        sd.ellipse([x - 5 * S, y + half_width(t) * 0.55,
                    x + 5 * S, y + half_width(t) * 0.98],
                   fill=(190, 175, 155, 60))
    shade = shade.filter(ImageFilter.GaussianBlur(10 * S))
    body.alpha_composite(shade)

    # kohaku patches, clipped to the body silhouette
    patches = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    rotated_blob(patches, 792 * S, 306 * S, 66 * S, 46 * S, -38, ORANGE + (255,))
    rotated_blob(patches, 640 * S, 512 * S, 118 * S, 74 * S, -38, ORANGE + (255,))
    rotated_blob(patches, 668 * S, 560 * S, 62 * S, 40 * S, -30, ORANGE_SOFT + (235,))
    rotated_blob(patches, 470 * S, 700 * S, 70 * S, 44 * S, -42, ORANGE + (255,))
    rotated_blob(patches, 500 * S, 736 * S, 34 * S, 22 * S, -35, ORANGE_SOFT + (220,))
    mask = Image.new("L", (CW, CH), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(outline, fill=255)
    patches = Image.composite(patches, Image.new("RGBA", (CW, CH), (0, 0, 0, 0)), mask)
    patches = patches.filter(ImageFilter.GaussianBlur(2 * S))
    body.alpha_composite(patches)

    # scale hints: faint arcs in rows along the belly
    scales = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    sc = ImageDraw.Draw(scales)
    for row, tt in enumerate([0.22, 0.38, 0.54, 0.70, 0.84]):
        for k in range(7):
            f = tt + (k - 3) * 0.028
            if not (0.05 < f < 0.97):
                continue
            idx = int(f * (len(pts) - 1))
            x, y = pts[idx]
            rr = 13 * S
            sc.arc([x - rr, y - rr * 0.7, x + rr, y + rr * 0.7],
                   start=15, end=165, fill=(150, 110, 70, 52), width=2 * S)
    scales = scales.filter(ImageFilter.GaussianBlur(1 * S))
    body.alpha_composite(scales)

    # dorsal ridge: low fin humps along the upper edge
    fin = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fin)
    for i in range(5):
        f = 0.44 + i * 0.06
        idx = int(f * (len(pts) - 1))
        x, y = pts[idx]
        x2, y2 = pts[min(idx + 1, len(pts) - 1)]
        x1, y1 = pts[max(idx - 1, 0)]
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        w = half_width(f)
        bx, by = x + nx * w, y + ny * w
        fd.polygon([(bx - 14 * S, by + 5 * S), (bx + 2 * S, by - 14 * S),
                    (bx + 18 * S, by + 3 * S)], fill=(240, 150, 90, 150))
    fin = fin.filter(ImageFilter.GaussianBlur(2 * S))
    body.alpha_composite(fin)

    # pectoral fin fanning out under the head
    rotated_blob(body, 716 * S, 428 * S, 58 * S, 26 * S, -58,
                 (244, 150, 80, 225))
    rotated_blob(body, 700 * S, 448 * S, 40 * S, 18 * S, -70,
                 (250, 180, 110, 200))

    # head: round cap, eye, mouth, barbels
    hx, hy = 800 * S, 300 * S
    hd = ImageDraw.Draw(body)
    hd.ellipse([hx - 62 * S, hy - 58 * S, hx + 62 * S, hy + 58 * S],
               fill=KOI_WHITE + (255,))
    rotated_blob(body, 818 * S, 268 * S, 46 * S, 30 * S, -38, ORANGE + (255,))
    # eye
    hd.ellipse([hx + 6 * S, hy - 34 * S, hx + 34 * S, hy - 6 * S],
               fill=(20, 16, 12, 255))
    hd.ellipse([hx + 15 * S, hy - 30 * S, hx + 27 * S, hy - 18 * S],
               fill=(255, 255, 255, 255))
    # mouth: small dark open curve at the tip
    hd.arc([hx + 34 * S, hy + 6 * S, hx + 66 * S, hy + 40 * S],
           start=300, end=90, fill=(90, 40, 20, 255), width=5 * S)
    # barbels sweeping back from the mouth
    for sgn in (1, -1):
        hd.arc([hx + 30 * S, hy + 18 * S + sgn * 6 * S,
                hx + 108 * S, hy + 66 * S + sgn * 6 * S],
               start=290, end=60, fill=(230, 210, 190, 235), width=3 * S)
    body = body.filter(ImageFilter.GaussianBlur(1 * S))
    canvas.alpha_composite(body)

    # tail: two long flowing lobes draping down over the bowl rim
    tail = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    td = ImageDraw.Draw(tail)
    bx, by = 400 * S, 800 * S
    # upper lobe sweeping left-down, broad and curved
    td.polygon([(bx + 12 * S, by - 30 * S), (340 * S, 818 * S),
                (268 * S, 858 * S), (214 * S, 906 * S), (196 * S, 946 * S),
                (238 * S, 950 * S), (292 * S, 936 * S), (344 * S, 892 * S),
                (386 * S, 844 * S), (402 * S, 812 * S)],
               fill=(247, 243, 234, 235))
    td.polygon([(bx + 8 * S, by - 14 * S), (338 * S, 826 * S),
                (292 * S, 862 * S), (248 * S, 898 * S), (232 * S, 930 * S),
                (268 * S, 940 * S), (312 * S, 908 * S), (356 * S, 862 * S),
                (392 * S, 824 * S)],
               fill=(240, 123, 45, 215))
    # lower lobe sweeping down into the bowl
    td.polygon([(bx + 18 * S, by + 6 * S), (404 * S, 856 * S),
                (394 * S, 906 * S), (376 * S, 944 * S), (360 * S, 952 * S),
                (392 * S, 950 * S), (416 * S, 918 * S), (428 * S, 872 * S),
                (424 * S, 842 * S)],
               fill=(247, 243, 234, 225))
    td.polygon([(bx + 16 * S, by + 12 * S), (400 * S, 862 * S),
                (390 * S, 908 * S), (376 * S, 950 * S), (388 * S, 966 * S),
                (408 * S, 928 * S), (414 * S, 876 * S)],
               fill=(232, 93, 31, 200))
    # fin rays: thin darker veins on the lobes
    for (x0, y0, x1, y1) in ((368, 816, 232, 936), (356, 834, 262, 944),
                             (404, 836, 384, 962), (414, 850, 402, 950)):
        td.line([(x0 * S, y0 * S), (x1 * S, y1 * S)],
                fill=(200, 120, 60, 130), width=3 * S)
    tail = tail.filter(ImageFilter.GaussianBlur(2 * S))
    canvas.alpha_composite(tail)


def make_burst(canvas, bowl):
    cx, cy, r = bowl
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # splash crown where the tail leaves the bowl: rounded blobs, not spikes
    rim_y = cy - r * 0.92
    for k in range(7):
        fx = cx - r * 0.85 + k * r * 0.28
        h = (26 + 20 * math.sin(k * 1.7)) * S
        wdt = (13 + 6 * math.cos(k * 2.3)) * S
        d.ellipse([fx - wdt, rim_y - h, fx + wdt, rim_y + 4 * S],
                  fill=(235, 250, 252, 210))
    # droplet fan arcing up-right along the leap, kept clear of the body
    drops = []
    for ring_i, (rr, count, size) in enumerate(((190, 7, 8), (300, 9, 11),
                                                (420, 7, 14), (540, 6, 17))):
        for j in range(count):
            ang = math.radians(-62 + j * (44 / max(count - 1, 1)))
            dx = cx + math.cos(ang) * rr * S * 1.15
            dy = (cy - r * 0.5) + math.sin(ang) * rr * S
            drops.append((dx, dy, (size + 3 * math.sin(j * 2.1 + ring_i)) * S))
    spine_pts = spine()
    kept = []
    for dx, dy, sz in drops:
        nearest = min((dx - px) ** 2 + (dy - py) ** 2 for px, py in spine_pts) ** 0.5
        if nearest < 105 * S:
            continue
        kept.append((dx, dy, sz))
    drops = kept
    for dx, dy, sz in drops:
        d.ellipse([dx - sz, dy - sz * 1.25, dx + sz, dy + sz * 1.25],
                  fill=(225, 245, 250, 225))
        d.ellipse([dx - sz * 0.35, dy - sz * 0.95, dx + sz * 0.15, dy - sz * 0.45],
                  fill=(255, 255, 255, 235))
    layer = layer.filter(ImageFilter.GaussianBlur(1 * S))
    canvas.alpha_composite(layer)


def grade(img):
    warm = Image.new("RGBA", img.size, (255, 190, 90, 0))
    wd = ImageDraw.Draw(warm)
    wd.ellipse([620 * S, -80 * S, CW + 80 * S, 560 * S], fill=(255, 190, 90, 26))
    img = Image.alpha_composite(img.convert("RGBA"), warm)
    return img.convert("RGB")


def main():
    canvas = make_background()
    make_sun(canvas)
    make_sill(canvas)
    bowl = make_bowl(canvas)
    make_koi(canvas)
    make_burst(canvas, bowl)
    img = grade(canvas)
    img = img.resize((W, H), Image.LANCZOS)
    img.save("entry.png", format="PNG", optimize=True)
    print("wrote entry.png", img.size)


if __name__ == "__main__":
    main()
