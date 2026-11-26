"""Draw a land-cover map of Lagos State from an exported GeoTIFF.

The GeoTIFF comes from gee_wetland_change.js (values 0 water, 1 wetland/mangrove,
2 other vegetation, 3 built-up, 4 bare sand/fill). Pixels outside Lagos are also
stored as 0, so the map is masked with the Lagos State outline from geoBoundaries.
All years are drawn with the same extent, colours and layout, so the figures can
be compared side by side or in a swipe view.

Usage:
    python tools/make_landcover_figure.py <landcover.tif> <geoBoundaries-NGA-ADM1.geojson> <year> <out.png> "<footer>" [swipe]

With "swipe", the figure is drawn at exactly 16:9 with a large year label and no
title, so two years line up in an ArcGIS StoryMaps swipe block without cropping.
"""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from rasterio.features import geometry_mask
from shapely.geometry import shape

tif, boundaries, year, out, footer = sys.argv[1:6]
SWIPE = len(sys.argv) > 6 and sys.argv[6] == "swipe"

COLOURS = ["#1f78b4", "#33a02c", "#b2df8a", "#e31a1c", "#fdbf6f"]
NAMES = ["Water", "Wetland / mangrove", "Other vegetation", "Built-up", "Bare sand / fill"]
SENSOR = "Landsat 8" if int(year) < 2022 else "Landsat 8/9"

with open(boundaries, encoding="utf-8") as f:
    lagos = next(feat for feat in json.load(f)["features"] if feat["properties"]["shapeName"] == "Lagos")
geom = shape(lagos["geometry"])

with rasterio.open(tif) as src:
    data = src.read(1).astype(float)
    outside = geometry_mask([lagos["geometry"]], out_shape=data.shape, transform=src.transform, invert=False)
    b = src.bounds
data[outside] = np.nan

if SWIPE:
    fig = plt.figure(figsize=(16, 9))
    ax = fig.add_axes([0.06, 0.30, 0.92, 0.62])
else:
    fig, ax = plt.subplots(figsize=(14, 4.4))
ax.set_facecolor("#dce6f0")
ax.imshow(np.ma.masked_invalid(data), cmap=ListedColormap(COLOURS), vmin=-0.5, vmax=4.5,
          extent=(b.left, b.right, b.bottom, b.top), interpolation="nearest")
polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
for p in polys:
    x, y = p.exterior.xy
    ax.plot(x, y, color="black", lw=0.6)
ax.set_xlim(b.left, b.right)
ax.set_ylim(b.bottom, b.top)
ax.set_aspect("equal")
ax.set_xlabel("Longitude (°E)")
ax.set_ylabel("Latitude (°N)")
if SWIPE:
    ax.text(0.015, 0.95, year, transform=ax.transAxes, fontsize=44, fontweight="bold", va="top",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=6))
else:
    ax.set_title(f"Land cover of Lagos State, {year} (dry season, {SENSOR}, Random Forest)",
                 loc="left", fontsize=14, fontweight="bold")

# north arrow and 20 km scale bar (1° longitude ≈ 110.6 km at 6.5° N)
ax.annotate("", xy=(4.31, 6.67), xytext=(4.31, 6.60), arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))
ax.text(4.31, 6.585, "N", ha="center", va="top", fontweight="bold")
x0, y0, km = 4.05, 6.395, 20 / 110.6
ax.plot([x0, x0 + km], [y0, y0], color="black", lw=4)
ax.text(x0 + km / 2, y0 + 0.008, "20 km", ha="center", va="bottom", fontsize=9)

ax.legend(handles=[Patch(color=c, label=n) for c, n in zip(COLOURS, NAMES)], loc="upper center",
          bbox_to_anchor=(0.5, -0.2), ncol=5, frameon=True, fontsize=14 if SWIPE else 10)
ax.text(0.0, -0.38, footer, transform=ax.transAxes, fontsize=11 if SWIPE else 8, color="#444444", va="top")
if SWIPE:
    fig.savefig(out, dpi=150, facecolor="white")
else:
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
print("saved", out)
