FROM odm_b_jxl2

WORKDIR /code
COPY . ./

RUN pip install -r requirements.txt --break-system-packages

ENTRYPOINT ["python3", "/code/automosaic.py"]
