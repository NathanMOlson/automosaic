import glob
import io
import os
import shutil
import tarfile
import cloud_storage

from opendm import config
from lightning_ortho import LightningOrtho


def main_orig():
    bucket_name = os.getenv("BUCKET")
    if bucket_name:
        dataset_name = os.environ["DATASET"]
        print(f"Downloading {dataset_name} from {bucket_name}")
        dataset_archive = cloud_storage.download(bucket_name=bucket_name, remote_blob_name=dataset_name)
    else:
        with open("/datasets/test.tar", "rb") as f:
            dataset_archive = f.read()

    dataset_dir = "/dataset"
    try:
        os.mkdir(dataset_dir)
        with tarfile.open(fileobj=io.BytesIO(dataset_archive), mode="r") as tar:
            tar.extractall(path=dataset_dir)
    except:
        pass
    # try:
    #     shutil.rmtree(os.path.join(dataset_dir, "opensfm"))
    # except:
    #     pass

    args = config.config()
    args.project_path = dataset_dir
    args.fast_orthophoto = True
    args.feature_threshold_scale = 1
    args.ignore_ypr = True
    args.use_fixed_camera_params = False
    # args.sfm_algorithm = 'triangulation'

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

def main():
    for dataset_dir in glob.glob("/datasets/tri/dataset3"):
        print(dataset_dir)
        args = config.config()
        args.project_path = dataset_dir
        args.fast_orthophoto = True
        args.feature_threshold_scale = 1
        args.ignore_ypr = False
        args.use_fixed_camera_params = False
        args.sfm_algorithm = 'triangulation'
        args.camera_lens = 'perspective'

        app = LightningOrtho(args)
        outputs = {}
        retcode = app.execute(outputs)


if __name__ == "__main__":
    main()
