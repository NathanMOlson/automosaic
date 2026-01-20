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

from google.cloud import run_v2
from google import auth


def run_job(job_name: str, vars: dict[str, str]):

    print(f"Running job {job_name} with vars {vars}")
    credentials, project_id = auth.default()
    client = run_v2.JobsClient(credentials=credentials)

    env = []
    for key, value in vars.items():
        env.append(run_v2.types.EnvVar(name=key, value=value))

    request = run_v2.RunJobRequest(
        name=job_name,
        overrides=run_v2.types.RunJobRequest.Overrides(
            container_overrides=[run_v2.types.RunJobRequest.Overrides.ContainerOverride(env=env)])
    )

    return client.run_job(request=request)
