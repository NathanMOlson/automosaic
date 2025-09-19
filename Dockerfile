FROM odm_b_jxl2

WORKDIR /code
COPY . ./

RUN pip install -r requirements.txt --break-system-packages

ENV FLASK_APP=upload_server
EXPOSE 8000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8000", "--cert=adhoc"]
