FROM ubuntu:24.04

RUN apt-get update
RUN apt-get install -y python3 python3-pip

WORKDIR /storage
COPY . ./

RUN pip install -r requirements.txt --break-system-packages

ENTRYPOINT ["python3", "/storage/save_images.py", "/images"]
