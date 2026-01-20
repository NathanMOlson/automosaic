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

from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed


def upload(bucket_name: str, source_file_path: str, destination_blob_name: str):
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path, if_generation_match=0)
        print(f"Uploaded {source_file_path} to gs://{bucket_name}/{destination_blob_name}")
    except PreconditionFailed:
        raise FileExistsError
    
    
def download(bucket_name: str, remote_blob_name: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(remote_blob_name)
    return blob.download_as_bytes()
