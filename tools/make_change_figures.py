"""Figures comparing the 2014 and 2025 land-cover maps of Lagos State.

Writes, from the two exported GeoTIFFs (same 30 m grid, values 0 water,
1 wetland/mangrove, 2 other vegetation, 3 built-up, 4 bare sand/fill):

  change_2014_2025.png        where land became built-up or sand fill, by what it was in 2014
  hotspots_2014_2025.png      2014 vs 2025 close-ups of the Lekki-Ajah corridor and Ibeju-Lekki
  swipe_zoom_2014/2025.png    16:9 views of the Lagos lagoon and Lekki corridor for a swipe block
  cover.png                   16:9 cover image for the StoryMap (change map, no text)

The figures show where change happened. Areas are reported from the Earth Engine
change table, not from these figures, because the two exports use a slightly
different boundary and 2025 training split.

Usage:
    python tools/make_change_figures.py <geoBoundaries-NGA-ADM1.geojson> <out_dir>
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
from rasterio.features import geometry_mask
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
boundaries, out_dir = sys.argv[1], Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

with open(boundaries, encoding="utf-8") as f:
    lagos = next(ft for ft in json.load(f)["features"] if ft["properties"]["shapeName"] == "Lagos")
geom = shape(lagos["geometry"])
polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]

with rasterio.open(ROOT / "results/data/lagos_landcover_2014.tif") as a, \
        rasterio.open(ROOT / "results/data/lagos_landcover_2025.tif") as b:
    assert a.transform == b.transform
    y14, y25 = a.read(1), b.read(1)
    inside = geometry_mask([lagos["geometry"]], out_shape=y14.shape, transform=a.transform, invert=True)
    bnd = a.bounds
EXTENT = (bnd.left, bnd.right, bnd.bottom, bnd.top)

LC_COLOURS = ["#1f78b4", "#33a02c", "#b2df8a", "#e31a1c", "#fdbf6f"]
LC_NAMES = ["Water", "Wetland / mangrove", "Other vegetation", "Built-up", "Bare sand / fill"]


def masked(arr):
    out = arr.astype(float)
    out[~inside] = np.nan
    return np.ma.masked_invalid(out)


def outline(ax, lw=0.6, colour="black"):
    for p in polys:
        x, y = p.exterior.xy
        ax.plot(x, y, color=colour, lw=lw)


# ---- change classes ---------------------------------------------------------
# 0 outside, 1 water (both years), 2 land with no change to built/fill,
# 3 vegetation -> built/fill, 4 wetland -> built/fill, 5 water -> built/fill
urban25 = (y25 == 3) | (y25 == 4)
urban14 = (y14 == 3) | (y14 == 4)
chg = np.full(y14.shape, 2, dtype=np.uint8)
chg[(y14 == 0) & (y25 == 0)] = 1
chg[urban14 & urban25] = 6                       # already built-up or fill in 2014
chg[(y14 == 2) & urban25] = 3
chg[(y14 == 1) & urban25] = 4
chg[(y14 == 0) & urban25] = 5
chg[~inside] = 0
CHG_COLOURS = ["#ffffff", "#c6dbef", "#e8e8e8", "#f28e2b", "#c51b8a", "#ffd92f", "#9e9e9e"]
CHG_NAMES = {3: "Vegetation → built-up or sand fill", 4: "Wetland / mangrove → built-up or sand fill",
             5: "Water → built-up or sand fill", 6: "Already built-up or fill in 2014",
             2: "Other land, no change to built-up", 1: "Water"}
CHG_CMAP = ListedColormap(CHG_COLOURS)


def chg_img(ax, data=chg):
    show = np.ma.masked_where(data == 0, data)
    ax.imshow(show, cmap=CHG_CMAP, vmin=-0.5, vmax=6.5, extent=EXTENT, interpolation="nearest")


# 1. full-state change map
fig, ax = plt.subplots(figsize=(14, 4.4))
ax.set_facecolor("#f4f6f8")
chg_img(ax)
outline(ax)
ax.set_xlim(bnd.left, bnd.right)
ax.set_ylim(bnd.bottom, bnd.top)
ax.set_aspect("equal")
ax.set_xlabel("Longitude (°E)")
ax.set_ylabel("Latitude (°N)")
ax.set_title("Where Lagos became built-up or sand fill, 2014 → 2025", loc="left", fontsize=14, fontweight="bold")
order = [4, 3, 5, 6, 2, 1]
ax.legend(handles=[Patch(color=CHG_COLOURS[k], label=CHG_NAMES[k]) for k in order], loc="upper center",
          bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=True, fontsize=10)
ax.text(0.0, -0.48, "Pixel-by-pixel comparison of the 2014 and 2025 Random Forest maps (Landsat, 30 m). "
        "Provisional, pending independent validation. Atta Albert, 2026.",
        transform=ax.transAxes, fontsize=8, color="#444444", va="top")
fig.savefig(out_dir / "change_2014_2025.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)

# 2. hotspots: 2014 vs 2025 close-ups
HOTSPOTS = [("Lekki–Ajah corridor", (3.44, 3.66, 6.415, 6.50)),
            ("Ibeju-Lekki (Free Trade Zone area)", (3.88, 4.10, 6.40, 6.485))]
fig, axs = plt.subplots(2, 2, figsize=(14, 6.6))
for row, (name, (x0, x1, yb, yt)) in enumerate(HOTSPOTS):
    for col, (yr, arr) in enumerate([("2014", y14), ("2025", y25)]):
        ax = axs[row, col]
        ax.set_facecolor("#dce6f0")
        ax.imshow(masked(arr), cmap=ListedColormap(LC_COLOURS), vmin=-0.5, vmax=4.5, extent=EXTENT,
                  interpolation="nearest")
        ax.set_xlim(x0, x1)
        ax.set_ylim(yb, yt)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{name}, {yr}", loc="left", fontsize=12, fontweight="bold")
        km = 5 / 110.6
        ax.plot([x1 - km - 0.01, x1 - 0.01], [yb + 0.006] * 2, color="black", lw=3)
        ax.text(x1 - km / 2 - 0.01, yb + 0.009, "5 km", ha="center", va="bottom", fontsize=9)
fig.legend(handles=[Patch(color=c, label=n) for c, n in zip(LC_COLOURS, LC_NAMES)], loc="lower center",
           ncol=5, frameon=True, fontsize=10, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(out_dir / "hotspots_2014_2025.png", dpi=170, facecolor="white")
plt.close(fig)

# 3. 16:9 swipe views of the Lagos lagoon and Lekki corridor
ZX0, ZX1, ZY0, ZY1 = 3.30, 3.88, 6.39, 6.715   # 16:9 at equal degrees
for yr, arr in [("2014", y14), ("2025", y25)]:
    fig = plt.figure(figsize=(16, 9))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#dce6f0")
    ax.imshow(masked(arr), cmap=ListedColormap(LC_COLOURS), vmin=-0.5, vmax=4.5, extent=EXTENT,
              interpolation="nearest")
    outline(ax, lw=0.8)
    ax.set_xlim(ZX0, ZX1)
    ax.set_ylim(ZY0, ZY1)
    ax.set_axis_off()
    ax.text(0.015, 0.97, yr, transform=ax.transAxes, fontsize=54, fontweight="bold", va="top",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=8))
    ax.legend(handles=[Patch(color=c, label=n) for c, n in zip(LC_COLOURS, LC_NAMES)], loc="lower left",
              ncol=1, frameon=True, fontsize=15, framealpha=0.92)
    km = 5 / 110.6
    ax.plot([ZX1 - km - 0.015, ZX1 - 0.015], [ZY0 + 0.012] * 2, color="black", lw=5)
    ax.text(ZX1 - km / 2 - 0.015, ZY0 + 0.017, "5 km", ha="center", va="bottom", fontsize=15)
    ax.text(0.99, 0.97, "Lagos lagoon and the Lekki corridor", transform=ax.transAxes, fontsize=17,
            ha="right", va="top", bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=6))
    fig.savefig(out_dir / f"swipe_zoom_{yr}.png", dpi=120, facecolor="white")
    plt.close(fig)

# 4. cover: dark change map, no text
fig = plt.figure(figsize=(16, 9))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor("#0b1d2e")
dark = ["#0b1d2e", "#123a5c", "#2b3a33", "#f28e2b", "#ff3fa4", "#ffd92f", "#7c7c7c"]
show = np.ma.masked_where(chg == 0, chg)
ax.imshow(show, cmap=ListedColormap(dark), vmin=-0.5, vmax=6.5, extent=EXTENT, interpolation="nearest")
outline(ax, lw=0.5, colour="#5d7385")
ax.set_xlim(3.33, 3.92)
ax.set_ylim(6.375, 6.707)
ax.set_axis_off()
fig.savefig(out_dir / "cover.png", dpi=120, facecolor="#0b1d2e")
plt.close(fig)
print("saved figures to", out_dir)
