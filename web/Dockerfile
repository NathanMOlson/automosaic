FROM ubuntu:24.04

RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /web
COPY . ./

RUN pip install -r requirements.txt  --break-system-packages

ENV FLASK_APP=image_server
EXPOSE 8000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8000"]