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
