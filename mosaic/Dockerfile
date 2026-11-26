FROM ghcr.io/nathanmolson/odm:550c997a3de7982c360f94a4213afa18c8659db4

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
