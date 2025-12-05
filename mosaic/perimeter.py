import rasterio
import numpy as np
from skimage import measure, morphology
from scipy.ndimage import binary_fill_holes
from shapely.geometry import Polygon, Point
import geopandas as gpd

# -----------------------------------------
# USER PARAMETERS
# -----------------------------------------
tiff_path = "20220719_2227MDT_Moose_Color.tiff"
threshold_value = 128            # choose threshold appropriate for your data
buffer_dist = -0.0005
perimeter_output = "perimeter.geojson"
active_output = "active.geojson"
# -----------------------------------------

# 1. OPEN TIFF IMAGE
with rasterio.open(tiff_path) as src:
    img = src.read(1)          # Read first band
    transform = src.transform
    crs = src.crs

# 2. APPLY THRESHOLD
binary = img > threshold_value

dilate1 = morphology.binary_dilation(binary, morphology.disk(10))
dilate1 = binary_fill_holes(dilate1)

# 3. EXTRACT BLOBS → POLYGONS
# Find connected components and extract contours
contours = measure.find_contours(dilate1, level=0.5)

polygons = []
for contour in contours:
    # Convert pixel coordinates to spatial coordinates
    coords = []
    for r, c in contour:
        x, y = rasterio.transform.xy(transform, r, c)
        coords.append((x, y))

    poly = Polygon(coords)
    if poly.is_valid and poly.area > 0:
        polygons.append(poly)

# 4. UN-DILATE
buffered_polys = []
for poly in polygons:
    if poly.length < -16*buffer_dist and poly.area < 9*buffer_dist*buffer_dist:
        continue
    # buffer_dist = buffer_scale_factor * area
    buffered_polys.append(poly.buffer(buffer_dist).simplify(-buffer_dist/4))

# Save to a GeoJSON (or shapefile)
gdf = gpd.GeoDataFrame(geometry=buffered_polys, crs=crs)
gdf.to_file(perimeter_output, driver="GeoJSON")

print(f"Saved {len(buffered_polys)} polygons to {perimeter_output}")

buffer_dist = -0.0002

dilate2 = morphology.binary_dilation(binary, morphology.disk(4))
dilate2 = binary_fill_holes(dilate2)

# 3. EXTRACT BLOBS → POLYGONS
# Find connected components and extract contours
contours = measure.find_contours(dilate2, level=0.5)

polygons = []
for contour in contours:
    # Convert pixel coordinates to spatial coordinates
    coords = []
    for r, c in contour:
        x, y = rasterio.transform.xy(transform, r, c)
        coords.append((x, y))

    poly = Polygon(coords)
    if poly.is_valid and poly.area > 0:
        polygons.append(poly)

# 4. UN-DILATE
buffered_polys = []
for poly in polygons:
    if poly.length < -16*buffer_dist and poly.area < 9*buffer_dist*buffer_dist:
        buffered_polys.append(Point(poly.centroid))
        continue
    # buffer_dist = buffer_scale_factor * area
    buffered_polys.append(poly.buffer(buffer_dist).simplify(-buffer_dist/4))

# Save to a GeoJSON (or shapefile)
gdf = gpd.GeoDataFrame(geometry=buffered_polys, crs=crs)
gdf.to_file(active_output, driver="GeoJSON")

print(f"Saved {len(buffered_polys)} polygons to {active_output}")