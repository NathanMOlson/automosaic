FROM python:3.12-slim

WORKDIR /code
COPY batcher/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY batcher ./

ENV FLASK_APP=upload_server PYTHONUNBUFFERED=1 STORAGE_BUCKET=lab308-dev KEEPALIVE_SECONDS=60
EXPOSE 8000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8000"]
