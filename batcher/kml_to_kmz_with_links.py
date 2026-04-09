# vibe-coded

import zipfile
from pathlib import Path
import requests
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

def kml_to_kmz_with_links(kml_path, kmz_path):
    kml_path = Path(kml_path)
    base_dir = kml_path.parent

    tree = ET.parse(kml_path)
    root = tree.getroot()

    ns = {"kml": "http://www.opengis.net/kml/2.2"}

    files_to_add = {kml_path: kml_path.name}

    # find all <NetworkLink><Link><href>
    for href in root.findall(".//kml:NetworkLink/kml:Link/kml:href", ns):
        url = href.text.strip()

        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            r = requests.get(url)
            fname = Path(parsed.path).name or "linked.kml"
            local_path = base_dir / fname
            with open(local_path, "wb") as f:
                f.write(r.content)
        else:
            local_path = (base_dir / url).resolve()

        files_to_add[local_path] = local_path.name
        href.text = local_path.name  # rewrite reference

    # write updated KML
    temp_kml = base_dir / "_doc.kml"
    tree.write(temp_kml, encoding="utf-8", xml_declaration=True)

    # create KMZ
    with zipfile.ZipFile(kmz_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(temp_kml, "doc.kml")
        for path, arcname in files_to_add.items():
            if path != kml_path:
                z.write(path, arcname)

    temp_kml.unlink()

# usage
kml_to_kmz_with_links("/mnt/c/Users/natha/Downloads/Merritt/Merritt_Fire.kml", "/mnt/c/Users/natha/Downloads/Merritt/Merritt_Fire.kmz")