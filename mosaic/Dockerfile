FROM ghcr.io/nathanmolson/odm:a9b2c96b29b69468820f78283140ad48d3445a63

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
