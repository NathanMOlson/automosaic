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
import glob
import tarfile
import cloud_storage
import requests


def main():
    bucket_name = os.getenv("BUCKET")
    dataset_name = os.getenv("DATASET", "/datasets/test.tar")
    batcher_url = os.getenv("BATCHER_URL")
    if bucket_name:
        print(f"Downloading {dataset_name} from {bucket_name}")
        dataset_archive = cloud_storage.download(bucket_name=bucket_name, remote_blob_name=dataset_name)
    else:
        with open(dataset_name, "rb") as f:
            dataset_archive = f.read()

    dataset_dir = "/dataset"
    os.mkdir(dataset_dir)
    with tarfile.open(fileobj=io.BytesIO(dataset_archive), mode="r") as tar:
        tar.extractall(path=dataset_dir)

    for filename in glob.glob(f"{dataset_dir}/*.jxl"):
        with open(filename, "rb") as f:
            response = requests.post(
                batcher_url,
                files={"file": f}
            )
            print(f"Uploading {filename}, response: {response.status_code}: {response.text}")


if __name__ == "__main__":
    main()
