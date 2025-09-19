
import io
import multiprocessing as mp
from numpy.typing import NDArray
import numpy as np
import os
import math
import exifread
import pytz
import tarfile

from tempfile import mkdtemp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime


class PhotoInfo:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        with open(filename, 'rb') as f:
            tags = exifread.process_file(f, details=False, extract_thumbnail=False)

        self.lat = self.dms_to_decimal(tags['GPS GPSLatitude'], tags['GPS GPSLatitudeRef'])
        self.lon = self.dms_to_decimal(tags['GPS GPSLongitude'], tags['GPS GPSLongitudeRef'])

        str_time = tags['EXIF DateTimeOriginal'].values
        utc_time = datetime.strptime(str_time, "%Y:%m:%d %H:%M:%S")
        timezone = pytz.timezone('UTC')
        epoch = timezone.localize(datetime.utcfromtimestamp(0))
        self.t_utc = (timezone.localize(utc_time) - epoch).total_seconds()

        if tags['GPS GPSSpeedRef'].values[0] == "K":
            self.groundspeed = self.float_value(tags['GPS GPSSpeed'])*1000/3600
        else:
            raise ValueError(f"Unknown GPS Speed Ref: {tags['GPS GPSSpeedRef']}")
        if tags['GPS GPSTrackRef'].values[0] == "T":
            track = self.float_value(tags['GPS GPSTrack'])
        else:
            raise ValueError(f"Unknown GPS Track Ref: {tags['GPS GPSTrackRef']}")
        self.v = self.groundspeed*np.array([math.cos(math.radians(track)), math.sin(math.radians(track))])
        self.dir = self.v / np.linalg.norm(self.v)

    def dms_to_decimal(self, dms, sign):
        """Converts dms coords to decimal degrees"""
        degrees, minutes, seconds = self.float_values(dms)

        if degrees is not None and minutes is not None and seconds is not None:
            return (-1 if sign.values[0] in 'SWsw' else 1) * (
                degrees +
                minutes / 60 +
                seconds / 3600
            )

    def float_values(self, tag):
        if isinstance(tag.values, list):
            result = []
            for v in tag.values:
                if isinstance(v, int):
                    result.append(float(v))
                elif isinstance(v, tuple) and len(v) == 1 and isinstance(v[0], float):
                    result.append(v[0])
                elif v.den != 0:
                    result.append(float(v.num) / float(v.den))
                else:
                    result.append(None)
            return result
        elif hasattr(tag.values, 'den'):
            return [float(tag.values.num) / float(tag.values.den) if tag.values.den != 0 else None]
        else:
            return [None]

    def float_value(self, tag):
        v = self.float_values(tag)
        if len(v) > 0:
            return v[0]


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
        self.executor = ThreadPoolExecutor()
        self.input_future = self.executor.submit(self.input_task)
        self.photo_future = self.executor.submit(self.photo_task)

    def check_for_orbit(self) -> bool:
        photo = self.photos[-1]

        min_orbit_time = 2*math.pi*photo.groundspeed/9.81  # assume 45 deg max bank
        start_index = None

        for i in range(len(self.photos) - 2, -1, -1):
            other = self.photos[i]
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
        while True:
            filename = self.input_queue.get()
            try:
                photo = PhotoInfo(filename)
            except ValueError as e:
                print(f"Failed to add photo: {filename} missing metadata: {e}")
                continue
            save_image(photo)
            detect_features(filename)
            self.photo_queue.put(photo)

    def photo_task(self) -> None:
        while True:
            photo = self.photo_queue.get()
            self.photos.append(photo)
            self.photos.sort(key=lambda x: x.t_utc)
            if self.check_for_orbit():
                self.photos = []


def detect_features(filename: str) -> None:
    print("detecting features")


def assemble_dataset(photos: list[str]) -> None:
    try:
        print(f"Assembling dataset from {len(photos)} photos")

        image_dir = "images"
        opensfm_dir = "opensfm"
        features_dir = os.path.join(opensfm_dir, "features")
        output_tar = "dataset.tar"

        with tarfile.open(output_tar, mode='w') as tar:

            for filepath in photos:
                tar.add(filepath, arcname=os.path.join(image_dir, os.path.basename(filepath)))
                features_filepath = filepath + ".npz"
                if os.path.exists(features_filepath):
                    tar.add(features_filepath, arcname=os.path.join(features_dir, os.path.basename(features_filepath)))

            stats_dir = os.path.join(opensfm_dir, "stats")
            stats_file_info = tarfile.TarInfo(name=os.path.join(stats_dir, "stats.json"))
            stats_file_info.size = 0
            tar.addfile(stats_file_info, fileobj=io.BytesIO())
    except Exception as e:
        print(e)
