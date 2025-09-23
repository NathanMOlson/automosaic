FROM python:3.12-slim

WORKDIR /code
COPY common ./
COPY mosaic ./

RUN pip install -r requirements.txt

CMD ["python3", "mosaic.py"]
