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


TRUTHY: tuple[str, ...] = ("1", "true", "yes", "on")


def _flag(name: str, default: bool) -> bool:
    """Parse a boolean-ish environment variable (1/true/yes/on -> True).

    Parameters
    ----------
    name : str
        The name of the environment variable to parse.
    default : bool
        The default value to return if the environment variable is not set.

    """
    _env = os.environ.get(name, str(default))
    _env = _env.strip().lower()

    return _env in TRUTHY


# When False, the batcher still receives and archives every image, but skips the
# segmentation subsystem entirely: it does not accumulate orbits, assemble
# datasets, or trigger mosaic jobs. Lets ingestion keep running (data still lands
# in the bucket) while the segmentation path is being debugged.
#
# Defaults True so existing deployments are unchanged until SEGMENTATION is
# explicitly set (e.g. SEGMENTATION=0 on the Cloud Run service).
SEGMENTATION = _flag("SEGMENTATION", True)
