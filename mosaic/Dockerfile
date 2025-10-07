FROM ghcr.io/nathanmolson/odm:5d12c734bd9c1a3ea4435164206475f012489bd2

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
