FROM ghcr.io/nathanmolson/425cad2cc5a23ae7ec97b29b747aa5d96952f916

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
