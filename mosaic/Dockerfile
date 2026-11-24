FROM ghcr.io/nathanmolson/odm:a889913ade263c49e251b803f9c785052d170794

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
