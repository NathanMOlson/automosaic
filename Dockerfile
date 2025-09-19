FROM python:3.12-slim

WORKDIR /code
COPY . ./

RUN pip install -r requirements.txt

ENV FLASK_APP=upload_server PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8000", "--cert=adhoc"]
