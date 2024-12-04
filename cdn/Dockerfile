FROM python:3-alpine

WORKDIR /usr/src/app

RUN apk update && apk add --no-cache curl libjpeg-turbo-dev zlib-dev

COPY requirements.txt /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 443

ENTRYPOINT ["python3"]
CMD ["-m", "openapi_server"]