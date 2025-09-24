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
        while True:
            time.sleep(1)
            if time.time() - self.start_time < self.keepalive_time:
                req = urllib.request.Request(self.endpoint)

                auth_req = google.auth.transport.requests.Request()
                id_token = google.oauth2.id_token.fetch_id_token(auth_req, self.service_url)

                req.add_header("Authorization", f"Bearer {id_token}")
                self.executor.submit(urllib.request.urlopen, req)


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
