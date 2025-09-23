import io
import os
import tarfile
import cloud_storage


def main():
    bucket_name = os.environ["BUCKET"]
    dataset_name = os.environ["DATASET"]
    print(f"Downloading {dataset_name} from {bucket_name}")
    dataset_archive = cloud_storage.download(bucket_name=bucket_name, remote_blob_name=dataset_name)
    dataset_dir = "/dataset"
    os.mkdir(dataset_dir)
    with tarfile.open(fileobj=io.BytesIO(dataset_archive), mode="r") as tar:
        tar.extractall(path=dataset_dir)

    print("TODO: Process dataset")
    print("SUCCESS!")


if __name__ == "__main__":
    main()
