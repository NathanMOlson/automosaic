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

import os
import traceback
import sys

from opendm import system
from opendm import log
from opendm import config
from opendm import io
from opendm.progress import progressbc

from stages.dataset import ODMLoadDatasetStage
from stages.run_opensfm import ODMOpenSfMStage
from stages.odm_filterpoints import ODMFilterPoints
from stages.dem2mosaic import DEM2Mosaic
from opendm.arghelpers import args_to_dict, save_opts, find_rerun_stage


class LightningOrtho:
    def __init__(self, args):
        """
        Initializes the application and defines the ODM application pipeline stages
        """
        json_log_paths = [os.path.join(args.project_path, "log.json")]

        if args.copy_to:
            json_log_paths.append(args.copy_to)

        log.logger.init_json_output(json_log_paths, args)

        dataset = ODMLoadDatasetStage('dataset', args, progress=5.0)
        opensfm = ODMOpenSfMStage('opensfm', args, progress=25.0)
        filterpoints = ODMFilterPoints('odm_filterpoints', args, progress=52.0)
        dem2mosaic = DEM2Mosaic('dem2mosaic', args, progress=88.0)

        # Normal pipeline
        self.first_stage = dataset

        dataset.connect(opensfm).connect(filterpoints).connect(dem2mosaic)

    def execute(self, outputs):
        try:
            self.first_stage.run(outputs)
            log.logger.log_json_success()
            return 0
        except system.SubprocessException as e:
            print("")
            print("===== Dumping Info for Geeks (developers need this to fix bugs) =====")
            print(str(e))
            stack_trace = traceback.format_exc()
            print(stack_trace)
            print("===== Done, human-readable information to follow... =====")
            print("")

            code = e.errorCode
            log.logger.log_json_stage_error(str(e), code, stack_trace)

            if code == 139 or code == 134 or code == 1 or code == 3221225477:
                # Segfault
                log.ODM_ERROR("Uh oh! Processing stopped because of strange values in the reconstruction. This is often a sign that the input data has some issues or the software cannot deal with it. Have you followed best practices for data acquisition? See https://docs.opendronemap.org/flying/")
            elif code == 137 or code == 3221226505:
                log.ODM_ERROR("Whoops! You ran out of memory! Add more RAM to your computer, if you're using docker configure it to use more memory, for WSL2 make use of .wslconfig (https://docs.microsoft.com/en-us/windows/wsl/wsl-config#configure-global-options-with-wslconfig), resize your images, lower the quality settings or process the images using a cloud provider (e.g. https://webodm.net).")
            elif code == 132:
                log.ODM_ERROR("Oh no! It looks like your CPU is not supported (is it fairly old?). You can still use ODM, but you will need to build your own docker image. See https://github.com/OpenDroneMap/ODM#build-from-source")
            elif code == 3:
                log.ODM_ERROR("ODM can't find a program that is required for processing to run! Did you do a custom build of ODM? (cool!) Make sure that all programs required by ODM are in the right place and are built correctly.")
            else:
                log.ODM_ERROR("The program exited with a strange error code. Please report it at https://community.opendronemap.org")

            # TODO: more?

            return code
        except system.ExitException as e:
            log.ODM_ERROR(str(e))
            log.logger.log_json_stage_error(str(e), 1, traceback.format_exc())
            sys.exit(1)
        except Exception as e:
            log.logger.log_json_stage_error(str(e), 1, traceback.format_exc())
            raise e
        finally:
            log.logger.close()


def odm_version():
    try:
        with open("VERSION") as f:
            return f.read().split("\n")[0].strip()
    except:
        return "?"


def main():
    args = config.config()

    log.ODM_INFO('Initializing ODM %s - %s' % (odm_version(), system.now()))

    progressbc.set_project_name(args.name)
    args.project_path = os.path.join(args.project_path, args.name)

    if not io.dir_exists(args.project_path):
        log.ODM_ERROR('Directory %s does not exist.' % args.name)
        exit(1)

    opts_json = os.path.join(args.project_path, "options.json")
    auto_rerun_stage, opts_diff = find_rerun_stage(opts_json, args, config.rerun_stages, config.processopts)
    if auto_rerun_stage is not None and len(auto_rerun_stage) > 0:
        log.ODM_INFO("Rerunning from: %s" % auto_rerun_stage[0])
        args.rerun_from = auto_rerun_stage

    # Print args
    args_dict = args_to_dict(args)
    log.ODM_INFO('==============')
    for k in args_dict.keys():
        log.ODM_INFO('%s: %s%s' % (k, args_dict[k], ' [changed]' if k in opts_diff else ''))
    log.ODM_INFO('==============')

    # If user asks to rerun everything, delete all of the existing progress directories.
    if args.rerun_all:
        log.ODM_INFO("Rerun all -- Removing old data")
        for d in [os.path.join(args.project_path, p) for p in get_processing_results_paths()] + [
                os.path.join(args.project_path, "opensfm"),
                os.path.join(args.project_path, "odm_filterpoints"),
                os.path.join(args.project_path, "dem2mosaic")]:
            rm_r(d)

    app = LightningOrtho(args)
    outputs = {}
    retcode = app.execute(outputs)

    if retcode == 0:
        save_opts(opts_json, args)
        log.ODM_INFO('ODM app finished - %s' % system.now())
    else:
        exit(retcode)


if __name__ == '__main__':
    main()