# Copyright (c) 2025-2026 Lab 308, LLC.

# This file is part of automosaic
# (see ${https://github.com/NathanMOlson/automosaic}).

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import io
import os
import shutil
import tarfile
import cloud_storage

from opendm import config
from lightning_ortho import LightningOrtho


def main():
    bucket_name = os.getenv("BUCKET")
    if bucket_name:
        dataset_name = os.environ["DATASET"]
        print(f"Downloading {dataset_name} from {bucket_name}")
        dataset_archive = cloud_storage.download(bucket_name=bucket_name, remote_blob_name=dataset_name)
    else:
        with open("/datasets/test.tar", "rb") as f:
            dataset_archive = f.read()

    dataset_dir = "/dataset"
    os.mkdir(dataset_dir)
    with tarfile.open(fileobj=io.BytesIO(dataset_archive), mode="r") as tar:
        tar.extractall(path=dataset_dir)

    args = config.config()
    args.project_path = dataset_dir
    args.fast_orthophoto = True
    args.feature_threshold_scale = 1
    args.ignore_ypr = True

    app = LightningOrtho(args)
    outputs = {}
    retcode = app.execute(outputs)

    if retcode == 0:
        mosaic_file = os.path.join(outputs["tree"].odm_meshing, "mosaic.tiff")
        if bucket_name:
            output_name = os.path.splitext(dataset_name)[0] + ".tiff"
            cloud_storage.upload(bucket_name, mosaic_file, output_name)
            print(f"Uploaded {output_name} to {bucket_name}")
        else:
            shutil.copyfile(mosaic_file, "/datasets/test.tiff")
        print("SUCCESS!")
    else:
        exit(retcode)


if __name__ == "__main__":
    main()
