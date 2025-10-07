import os
import math

from opendm import log
from opendm import io
from opendm import system
from opendm import types
from opendm.dem import commands


def run_dem2mosaic(reconstruction_path: str, dem_path: str, georef_path: str, output_dir: str) -> None:
    system.run(f"dem2mosaic {reconstruction_path} {dem_path} {georef_path} {output_dir}")


class DEM2Mosaic(types.ODM_Stage):
    def process(self, args, outputs):
        tree = outputs['tree']

        # define paths and create working directories
        system.mkdir_p(tree.odm_meshing)

        mosaic_dir = tree.odm_meshing
        mosaic_file = os.path.join(mosaic_dir, "mosaic.tiff")

        if not io.file_exists(mosaic_file) or self.rerun():

            log.ODM_INFO(f"Writing mosaic file in: {mosaic_dir}")

            multiplier = math.pi / 2.0
            radius_steps = commands.get_dem_radius_steps(tree.filtered_point_cloud_stats, 3, args.orthophoto_resolution, multiplier=multiplier)
            dsm_resolution = radius_steps[0] / multiplier

            log.ODM_INFO('ODM 2.5D DSM resolution: %s' % dsm_resolution)

            if args.fast_orthophoto:
                dsm_resolution *= 8.0

            tmp_directory = os.path.join(tree.odm_meshing, 'tmp')

            dem_type = 'mesh_dsm'

            commands.create_dem(
                tree.filtered_point_cloud,
                dem_type,
                output_type='max',
                radiuses=radius_steps,
                gapfill=True,
                outdir=tmp_directory,
                resolution=dsm_resolution,
                max_workers=args.max_concurrency,
                apply_smoothing=True,
                max_tiles=None
            )

            try:
                os.symlink(tree.dataset_raw, os.path.join(tree.opensfm, "images"))
            except FileExistsError:
                pass

            run_dem2mosaic(reconstruction_path=tree.opensfm_reconstruction,
                           dem_path=os.path.join(tmp_directory, f"{dem_type}.tif"),
                           georef_path=tree.odm_georeferencing_coords,
                           output_dir=mosaic_dir)

        else:
            log.ODM_WARNING(f"Found a valid Mosaic file in: {mosaic_dir}")
