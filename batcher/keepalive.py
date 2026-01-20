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

import requests
import time
import urllib
import google.auth.transport.requests
import google.oauth2.id_token
from concurrent.futures import ThreadPoolExecutor


class KeepAlive:
    def __init__(self, service_url: str, keepalive_time: float) -> None:
        self.service_url = service_url
        self.endpoint = f"{service_url}/keepalive"
        self.keepalive_time = keepalive_time
        self.executor = ThreadPoolExecutor()
        self.future = self.executor.submit(self.task)
        self.start_time = time.time()

    def poke(self) -> None:
        self.start_time = time.time()

    def task(self) -> None:
        futures = []
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, self.service_url)
        while True:
            try:
                time.sleep(1)
                if len(futures) > 0 and futures[0].done():
                    res = futures[0].result()
                    if res.status != 200:
                        print(f"Keepalive request failed: {res.status}, re-requesting ID token")
                        id_token = google.oauth2.id_token.fetch_id_token(auth_req, self.service_url)
                    del futures[0]
                if time.time() - self.start_time < self.keepalive_time:
                    req = urllib.request.Request(self.endpoint)
                    req.add_header("Authorization", f"Bearer {id_token}")
                    futures.append(self.executor.submit(urllib.request.urlopen, req))
            except Exception as e:
                print(f"Exception in keepalive thread: {e}")


def make_authorized_get_request(endpoint, audience):
    """
    make_authorized_get_request makes a GET request to the specified HTTP endpoint
    by authenticating with the ID token obtained from the google-auth client library
    using the specified audience value.
    """

    # Cloud Run uses your service's hostname as the `audience` value
    # audience = 'https://my-cloud-run-service.run.app/'
    # For Cloud Run, `endpoint` is the URL (hostname + path) receiving the request
    # endpoint = 'https://my-cloud-run-service.run.app/my/awesome/url'

    req = urllib.request.Request(endpoint)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)

    req.add_header("Authorization", f"Bearer {id_token}")
    response = urllib.request.urlopen(req)
