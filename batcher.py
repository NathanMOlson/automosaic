
import multiprocessing as mp
import shutil
from numpy.typing import NDArray
import numpy as np
import cv2
from opendm.photo import ODM_Photo
from opensfm import features
from opensfm.config import default_config
from opendm import config
import os
import math
import sys

from tempfile import mkdtemp
from concurrent.futures import ProcessPoolExecutor


class PhotoInfo:
    def __init__(self, photo: ODM_Photo) -> None:
        if photo.filename is None or photo.utc_time is None \
                or photo.latitude is None or photo.longitude is None:
            raise ValueError
        self.filename = photo.filename
        self.lat = photo.latitude
        self.lon = photo.longitude
        self.t_utc = photo.utc_time / 1000.0
        self.v = None
        self.groundspeed = None
        self.dir = None

        if photo.speed_x is not None and photo.speed_y is not None:
            self.v = np.array([photo.speed_x, photo.speed_y])
            self.groundspeed = np.linalg.norm(self.v)
            self.dir = self.v / self.groundspeed


def approx_displacement(p1: PhotoInfo, p2: PhotoInfo) -> NDArray:
    mid_lat = (p1.lat + p2.lat) / 2
    DEG_LEN = 6371000*math.radians(1)
    # fails across international dateline!
    d = DEG_LEN*np.array([p2.lat-p1.lat, (p2.lon-p1.lon)*math.cos(math.radians(mid_lat))])
    return d


def save_image(image: PhotoInfo):
    print(f"Saving {image.filename}")


class Batcher:
    def __init__(self) -> None:
        self.photos: list[PhotoInfo] = []
        self.input_queue: mp.Queue[str] = mp.Queue(1024)
        self.photo_queue: mp.Queue[PhotoInfo] = mp.Queue(1024)
        self.executor = ProcessPoolExecutor()
        self.input_future = self.executor.submit(self.input_task)
        self.photo_future = self.executor.submit(self.photo_task)

    def check_for_orbit(self) -> bool:
        photo = self.photos[-1]

        if photo.v is None:
            print(f"{photo.filename} has no velocity metadata, attempting to approximate it")
            for other in reversed(self.photos):
                if photo.t_utc - other.t_utc > 2 and photo.t_utc - other.t_utc < 20:
                    photo.v = approx_displacement(other, photo)/(photo.t_utc - other.t_utc)
                    photo.groundspeed = np.linalg.norm(photo.v)
                    photo.dir = photo.v / photo.groundspeed
                    break

        if photo.v is None:
            print(f"{photo.filename} has no velocity metadata, ignoring")
            return False

        min_orbit_time = 2*math.pi*photo.groundspeed/9.81  # assume 45 deg max bank
        start_index = None

        for i in range(len(self.photos) - 2, -1, -1):
            other = self.photos[i]
            if other.v is None:
                continue
            if photo.t_utc - other.t_utc < min_orbit_time:
                continue
            if np.dot(photo.dir, other.dir) < 0.7:
                continue
            d = approx_displacement(other, photo)
            if np.dot(photo.dir, d) <= 0:
                continue
            if np.linalg.norm(d) < 1000:
                start_index = i
                break
        if start_index is None:
            return False

        files = []
        for i in range(start_index, len(self.photos)):
            files.append(self.photos[i].filename)
            # Mark the image as mosaiced by creating an empty file with the same name and ".mosaiced" appended
            with open(self.photos[i].filename + ".mosaiced", "w") as f:
                pass
        assemble_dataset(files)

        return True

    def on_new_file(self, filename: str) -> None:
        if filename.split('.')[-1] != "jxl":
            return
        self.input_queue.put(filename)

    def input_task(self) -> None:
        filename = self.input_queue.get()
        try:
            photo = PhotoInfo(ODM_Photo(filename))
            photo.filename = filename
        except ValueError:
            print(f"Failed to add photo: {filename} missing metadata")
        save_image(photo)
        detect_features(filename)
        self.photo_queue.put(photo)
        

    def photo_task(self) -> None:
        photo = self.photo_queue.get()
        self.photos.append(photo)
        self.photos.sort(key=lambda x: x.t_utc)
        if self.check_for_orbit():
            self.photos = []


def detect_features(filename: str) -> None:
    img = cv2.imread(filename, flags=cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH)
    config = default_config()
    config["feature_type"] = "DSPSIFT"

    p, f, c = features.extract_features(img, config, is_panorama=False)
    size = p[:, 2]
    order = np.argsort(size)
    p_sorted = p[order, :]
    f_sorted = f[order, :]
    c_sorted = c[order, :]
    features_data = features.FeaturesData(points=p_sorted, descriptors=f_sorted, colors=c_sorted, semantic=None)
    features_data.save(filename + ".npz", config)


def assemble_dataset(photos: list[str]) -> None:
    print(f"Assembling dataset from {len(photos)} photos")

    root_dir = mkdtemp(dir="/datasets")
    image_dir = os.path.join(root_dir, "images")
    os.mkdir(image_dir)
    opensfm_dir = os.path.join(root_dir, "opensfm")
    os.mkdir(opensfm_dir)
    features_dir = os.path.join(opensfm_dir, "features")
    os.mkdir(features_dir)

    for filepath in photos:
        features_filepath = filepath + ".npz"
        shutil.move(filepath, os.path.join(image_dir, os.path.basename(filepath)))
        shutil.move(features_filepath, os.path.join(features_dir, os.path.basename(features_filepath)))

    stats_dir = os.path.join(opensfm_dir, "stats")
    os.mkdir(stats_dir)
    with open(os.path.join(stats_dir, "stats.json"), "w") as f:
        f.write("{}\n")
