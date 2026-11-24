FROM ghcr.io/nathanmolson/odm:0c48ae4ec712afb64dc300d31519928df844a8ad

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

ENTRYPOINT ["python3", "mosaic.py"]
