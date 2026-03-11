FROM ghcr.io/nathanmolson/odm:642f3115ba24a27fcba45e0cd42ceb6d653925e7

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
