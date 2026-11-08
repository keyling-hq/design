"""Build Keyling's logo files and Android icons from the marks on logo/marks.html.

Usage: python build_icons.py [--hub <res dir>] [--plugin <res dir>] [--plugin-logo <dir>]

Always writes the flat SVGs in logo/. With --hub or --plugin it also writes the launcher, notification and
menu icons into those Android res directories; --plugin-logo copies the plugin's SVGs into another
directory (the plugin repository's logo/). Needs node, shapely and svgelements.
"""
import argparse
import os
import subprocess
import sys
import tempfile

from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from flatten import flatten  # noqa: E402

LOGO = os.path.join(os.path.dirname(HERE), "logo")
NAVY, WHITE, PERIWINKLE, GREY = "#15172B", "#FFFFFF", "#7C9CFF", "#757575"
MARKS = {"H1g": "keyling-logo", "C2": "ling-happy", "P5": "kp2a-plugin"}


def coords(g):
    for p in getattr(g, "geoms", [g]):
        yield from p.exterior.coords


def fit_circle(g, cx, cy, r):
    """Scale and move g so every point lies within the circle, centred on its bounding box."""
    x0, y0, x1, y1 = g.bounds
    bx, by = (x0 + x1) / 2, (y0 + y1) / 2
    far = max(((x - bx) ** 2 + (y - by) ** 2) ** 0.5 for x, y in coords(g))
    s = r / far
    return affinity.affine_transform(g, [s, 0, 0, s, cx - bx * s, cy - by * s])


def fit_box(g, size, pad):
    x0, y0, x1, y1 = g.bounds
    s = (size - 2 * pad) / max(x1 - x0, y1 - y0)
    tx = (size - (x1 - x0) * s) / 2 - x0 * s
    ty = (size - (y1 - y0) * s) / 2 - y0 * s
    return affinity.affine_transform(g, [s, 0, 0, s, tx, ty])


def d(g, sep=" "):
    out = []
    for p in getattr(g, "geoms", [g]):
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)[:-1]
            out.append("M" + "L".join(f"{x:.2f}{sep}{y:.2f}" for x, y in pts) + "Z")
    return "".join(out)


def svg(g, size, color, bg=None):
    rect = f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
            f'{rect}<path fill="{color}" fill-rule="evenodd" d="{d(g)}"/></svg>\n')


def vector(g, size, dp, color):
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            f'    android:width="{dp}dp"\n    android:height="{dp}dp"\n'
            f'    android:viewportWidth="{size}"\n    android:viewportHeight="{size}">\n'
            f'    <path\n        android:fillColor="#FF{color[1:]}"\n        android:fillType="evenOdd"\n'
            f'        android:pathData="{d(g, ",")}" />\n</vector>\n')


def color_res(name, value):
    return (f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            f'    <color name="{name}">{value}</color>\n</resources>\n')


ADAPTIVE = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hub", help="the hub app's res directory")
    ap.add_argument("--plugin", help="the KeePass2Android plugin's res directory")
    ap.add_argument("--plugin-logo", help="a directory for copies of the plugin's SVGs")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["node", os.path.join(HERE, "export_marks.js"), os.path.join(LOGO, "marks.html"), tmp,
                        *(f"{k}={v}" for k, v in MARKS.items())], check=True, stdout=subprocess.DEVNULL)
        logo, ling, plugin = (flatten(os.path.join(tmp, f"{name}.svg")) for name in MARKS.values())

    # Plain single-path SVGs, 512 px, the mark filling the square with a small margin.
    for name, g in (("keyling-logo", logo), ("ling-happy", ling)):
        big = fit_box(g, 512, 16)
        write(os.path.join(LOGO, f"{name}.svg"), svg(big, 512, NAVY))
        write(os.path.join(LOGO, f"{name}-white.svg"), svg(big, 512, WHITE))
    # GitHub avatars are shown cropped to a circle in places, so the mark stays inside one.
    write(os.path.join(LOGO, "github-avatar.svg"), svg(fit_circle(logo, 250, 250, 198), 500, WHITE, NAVY))
    plugin_big = fit_box(plugin, 512, 16)
    for folder in filter(None, (LOGO, args.plugin_logo)):
        write(os.path.join(folder, "kp2a-plugin.svg"), svg(plugin_big, 512, NAVY))
        write(os.path.join(folder, "kp2a-plugin-white.svg"), svg(plugin_big, 512, WHITE))
        write(os.path.join(folder, "kp2a-plugin-icon.svg"),
              svg(fit_circle(plugin, 256, 256, 200), 512, NAVY, PERIWINKLE))

    # Adaptive launcher icons are 108 dp with a 66 dp safe circle.
    if args.hub:
        write(os.path.join(args.hub, "drawable", "ic_launcher_foreground.xml"),
              vector(fit_circle(logo, 54, 54, 31), 108, 108, WHITE))
        write(os.path.join(args.hub, "values", "ic_launcher_background.xml"), color_res("ic_launcher_background", NAVY))
        write(os.path.join(args.hub, "drawable", "ic_notification.xml"), vector(fit_box(logo, 24, 1), 24, 24, WHITE))
        # Drawn in the app's own screens and tinted there, so the mark fills its box with no margin.
        write(os.path.join(args.hub, "drawable", "keyling_logo.xml"), vector(fit_box(logo, 512, 0), 512, 128, WHITE))
        write(os.path.join(args.hub, "drawable", "ling_happy.xml"), vector(fit_box(ling, 512, 0), 512, 128, WHITE))
    if args.plugin:
        # The keycap's rounded corners stay inside the mask, so the plugin's mark can use the whole safe circle.
        write(os.path.join(args.plugin, "drawable", "ic_launcher_foreground.xml"),
              vector(fit_circle(plugin, 54, 54, 33), 108, 108, NAVY))
        write(os.path.join(args.plugin, "values", "ic_launcher_background.xml"),
              color_res("ic_launcher_background", PERIWINKLE))
        write(os.path.join(args.plugin, "mipmap-anydpi", "ic_launcher.xml"), ADAPTIVE)
        # Shown by KeePass2Android next to the plugin's entry actions, in the grey of Material's action icons.
        write(os.path.join(args.plugin, "drawable", "ic_keyling.xml"), vector(fit_box(logo, 24, 1), 24, 24, GREY))


if __name__ == "__main__":
    main()
