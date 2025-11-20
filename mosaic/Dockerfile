FROM ghcr.io/nathanmolson/odm:93e1c60d77ca9b9de0bf72591390c4995b8a413b

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
