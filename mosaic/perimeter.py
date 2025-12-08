import rasterio
import numpy as np
import numpy.typing as npt
from skimage import measure, morphology
from scipy.ndimage import binary_fill_holes
from shapely.geometry import Polygon, Point, MultiPoint
from shapely.ops import unary_union
import geopandas as gpd
import pygeohash as pgh
from pykml import parser
from pykml.factory import KML_ElementMaker as KML
from lxml import etree

# -----------------------------------------
# USER PARAMETERS
# -----------------------------------------
tiff_path = "/home/nathan/perimeter/20220719_2227MDT_Moose_Color.tiff"
threshold_value = 128
perimeter_output = "/mnt/c/Users/natha/Downloads/perimeter.kml"
active_output = "/mnt/c/Users/natha/Downloads/active.kml"
current_month_kml_name = "current_month.kml"
# -----------------------------------------


def make_polygons(binary_img: npt.NDArray, buffer_dist, dilate_radius, keep_points: bool) -> gpd.GeoDataFrame:

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
    points = []
    for poly in polygons:
        if poly.length < -16*buffer_dist and poly.area < 9*buffer_dist*buffer_dist:
            if keep_points:
                points.append(Point(poly.centroid))
            continue
        # buffer_dist = buffer_scale_factor * area
        buffered_poly = poly.buffer(buffer_dist).simplify(-buffer_dist/4)
        buffered_polys.append(buffered_poly)
    buffered_polys = [unary_union(buffered_polys)]
    if points:
        buffered_polys.append(MultiPoint(points))

    return gpd.GeoDataFrame(geometry=buffered_polys, crs=crs)


def combine_kmls(kml1_name: str, kml2_name: str, output_name: str) -> None:
    with open(kml1_name) as f:
        kml1 = parser.parse(f)
    with open(kml2_name) as f:
        kml2 = parser.parse(f)

    doc = KML.Document(KML.Style(KML.LineStyle(KML.color("ff0000ff"),
                                               KML.width(4)),
                                 KML.PolyStyle(KML.color("550000ff"),
                                               KML.fill(1),
                                               KML.outline(1)),
                                 id="perimeterStyle"),
                       KML.Style(KML.LineStyle(KML.color("ff00ffff"),
                                               KML.width(2)),
                                 KML.PolyStyle(KML.color("7700ffff"),
                                               KML.fill(1),
                                               KML.outline(1)),
                                 KML.IconStyle(KML.color("ff00ffff"),
                                               KML.scale(0.7),
                                               KML.Icon(KML.href("http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"))),
                                 KML.LabelStyle(KML.scale(0)),
                                 id="activeStyle"))
    for pm in kml1.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        name = pm.attrib.get('id').split('.')[0]
        pm.insert(0, KML.name(name))
        pm.insert(1, KML.styleUrl("perimeterStyle"))
        doc.append(pm)
    for pm in kml2.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        name = pm.attrib.get('id').split('.')[0]
        pm.insert(0, KML.name(name))
        pm.insert(1, KML.styleUrl("activeStyle"))
        doc.append(pm)

    with open(output_name, "wb") as f:
        f.write(etree.tostring(doc, pretty_print=True))


def do_bboxes_intersect(bb1: rasterio.coords.BoundingBox, bb2: rasterio.coords.BoundingBox) -> bool:
    return not rasterio.coords.disjoint_bounds(bb1, bb2)


def bbox_union(bb1: rasterio.coords.BoundingBox, bb2: rasterio.coords.BoundingBox) -> rasterio.coords.BoundingBox:
    return rasterio.coords.BoundingBox(left=min(bb1.left, bb2.left),
                                       bottom=min(bb1.bottom, bb2.bottom),
                                       right=max(bb1.right, bb2.right),
                                       top=max(bb1.top, bb2.top))


def make_bbox_placemark(bbox: rasterio.coords.BoundingBox):
    coords_str = f"{bbox.left},{bbox.top}\n"
    coords_str += f"{bbox.right},{bbox.top}\n"
    coords_str += f"{bbox.right},{bbox.bottom}\n"
    coords_str += f"{bbox.left},{bbox.bottom}\n"
    coords_str += f"{bbox.left},{bbox.top}"
    return KML.Placemark(KML.Polygon(KML.outerBoundaryIs(KML.LinearRing(KML.coordinates(coords_str)))),
                         KML.styleUrl("boundsStyle"))


with rasterio.open(tiff_path) as src:
    img = src.read(1)
    transform = src.transform
    crs = src.crs
    bounds = src.bounds
    timestr = src.tags().get("TIFFTAG_DATETIME").replace(" ", "_").replace(":", "-")

binary = img > threshold_value

perimeter = make_polygons(binary, buffer_dist=-0.0005, dilate_radius=10, keep_points=False)
perimeter.to_file(perimeter_output, driver="KML")
active = make_polygons(binary, buffer_dist=-0.0002, dilate_radius=4, keep_points=True)
active.to_file(active_output, driver="KML")

centroid = perimeter.geometry.centroid
incident_name = pgh.encode(centroid.y[0], centroid.x[0], precision=8)
output_file = f"{incident_name}_{timestr}.kml"

combine_kmls(perimeter_output, active_output, output_file)

try:
    with open(current_month_kml_name) as f:
        current_month_kml = parser.parse(f).getroot()
except FileNotFoundError:
    current_month_kml = KML.kml(KML.Document(KML.Style(KML.LineStyle(KML.color("ffaaaaaa"),
                                                                     KML.width(4)),
                                                       KML.PolyStyle(KML.color("55555555"),
                                                                     KML.fill(0),
                                                                     KML.outline(1)),
                                                       id="boundsStyle")))


new_view_network_link = KML.NetworkLink(KML.Link(KML.href(output_file)))

found_match = False
for region in current_month_kml.Document.findall('.//{http://www.opengis.net/kml/2.2}Region'):
    lla_box = region.find('{http://www.opengis.net/kml/2.2}LatLonAltBox')
    existing_bbox = rasterio.coords.BoundingBox(left=lla_box.find('{http://www.opengis.net/kml/2.2}west'),
                                                bottom=lla_box.find('{http://www.opengis.net/kml/2.2}south'),
                                                right=lla_box.find('{http://www.opengis.net/kml/2.2}east'),
                                                top=lla_box.find('{http://www.opengis.net/kml/2.2}north'))
    if do_bboxes_intersect(bounds, existing_bbox):
        found_match = True
        new_bbox = bbox_union(bounds, existing_bbox)
        lla_box.west = new_bbox.left
        lla_box.south = new_bbox.bottom
        lla_box.east = new_bbox.right
        lla_box.north = new_bbox.top
        region.getparent().Placemark = make_bbox_placemark(new_bbox)
        region.getparent().append(new_view_network_link)
        break

if not found_match:
    current_month_kml.Document.append(KML.Folder(KML.name(incident_name),
                                                 make_bbox_placemark(bounds),
                                                 KML.Region(KML.LatLonAltBox(KML.north(bounds.top),
                                                                             KML.south(bounds.bottom),
                                                                             KML.east(bounds.right),
                                                                             KML.west(bounds.left))),
                                                 new_view_network_link))

with open(current_month_kml_name, "wb") as f:
    f.write(etree.tostring(current_month_kml, pretty_print=True))
