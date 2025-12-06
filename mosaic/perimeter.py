import rasterio
import numpy as np
import numpy.typing as npt
from skimage import measure, morphology
from scipy.ndimage import binary_fill_holes
from shapely.geometry import Polygon, Point
import geopandas as gpd

# -----------------------------------------
# USER PARAMETERS
# -----------------------------------------
tiff_path = "/home/nathan/perimeter/20220719_2227MDT_Moose_Color.tiff"
threshold_value = 128
perimeter_output = "/mnt/c/Users/natha/Downloads/perimeter.geojson"
active_output = "/mnt/c/Users/natha/Downloads/active.geojson"
# -----------------------------------------


def make_polygons(binary_img: npt.NDArray, output: str, buffer_dist, dilate_radius, keep_points: bool) -> None:

    dilate1 = morphology.binary_dilation(binary_img, morphology.disk(dilate_radius))
    dilate1 = binary_fill_holes(dilate1)

    # EXTRACT BLOBS → POLYGONS
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

    # UN-DILATE
    buffered_polys = []
    for poly in polygons:
        if poly.length < -16*buffer_dist and poly.area < 9*buffer_dist*buffer_dist:
            if keep_points:
                buffered_polys.append(Point(poly.centroid))
            continue
        # buffer_dist = buffer_scale_factor * area
        buffered_polys.append(poly.buffer(buffer_dist).simplify(-buffer_dist/4))

    # Save to a GeoJSON (or shapefile)
    gdf = gpd.GeoDataFrame(geometry=buffered_polys, crs=crs)
    gdf.to_file(output, driver="GeoJSON")

    print(f"Saved {len(buffered_polys)} polygons to {output}")


with rasterio.open(tiff_path) as src:
    img = src.read(1)
    transform = src.transform
    crs = src.crs

binary = img > threshold_value

make_polygons(binary, perimeter_output, buffer_dist=-0.0005, dilate_radius=10, keep_points=False)
make_polygons(binary, active_output, buffer_dist=-0.0002, dilate_radius=4, keep_points=True)
