"""Reproduce the project's geometric artwork using Pillow (build dependency)."""
# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = (15, 28, 43)
PANEL = (27, 52, 70)
ACCENT = (38, 196, 206)
INK = (232, 244, 246)


def symbol(canvas, box):
    x, y, size = box
    def rect(coords, colour, radius=0):
        points = tuple(round(v) for v in (x + coords[0]*size, y + coords[1]*size,
                                          x + coords[2]*size, y + coords[3]*size))
        ImageDraw.Draw(canvas).rounded_rectangle(points, round(radius*size), fill=colour)
    rect((0, 0, 1, 0.82), ACCENT, 0.12)
    rect((0.055, 0.055, 0.945, 0.765), PANEL, 0.075)
    d = ImageDraw.Draw(canvas)
    d.polygon([(x+size*.42, y+size*.19), (x+size*.42, y+size*.44),
               (x+size*.63, y+size*.315)], fill=INK)
    rect((0.17, 0.53, 0.57, 0.57), INK, .01)
    rect((0.62, 0.53, 0.83, 0.57), INK, .01)
    rect((0.23, 0.63, 0.77, 0.67), INK, .01)
    d.polygon([(x+size*.25, y+size*.82), (x+size*.25, y+size),
               (x+size*.44, y+size*.82)], fill=ACCENT)


def main():
    scale = 3
    icon = Image.new('RGB', (512*scale, 512*scale), BACKGROUND)
    symbol(icon, (76*scale, 72*scale, 360*scale))
    icon.resize((512, 512), Image.Resampling.LANCZOS).save(ROOT / 'icon.png')
    fanart = Image.new('RGB', (1920, 1080), BACKGROUND)
    d = ImageDraw.Draw(fanart)
    for offset in range(0, 2400, 160):
        d.line([(offset, 0), (offset-720, 1080)], fill=(20, 37, 53), width=2)
    symbol(fanart, (660, 240, 600))
    fanart.save(ROOT / 'resources/media/fanart.jpg', quality=92)


if __name__ == '__main__':
    main()
