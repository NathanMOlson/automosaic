FROM python:3.12-slim

WORKDIR /code
COPY test/requirements.txt ./
RUN pip install -r requirements.txt

COPY common ./
COPY test ./

ENTRYPOINT ["python3", "test.py"]
