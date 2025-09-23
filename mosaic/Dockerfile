FROM python:3.12-slim

WORKDIR /code
COPY mosaic/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY mosaic ./

CMD ["python3", "mosaic.py"]
