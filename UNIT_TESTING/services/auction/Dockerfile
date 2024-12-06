FROM python:3.13-rc-alpine


# Setting current workdir
WORKDIR /usr/src/app

# Install curl and other dependencies (if necessary)
RUN apk update && apk add --no-cache curl

# Copy requirements file
COPY requirements.txt /usr/src/app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 443

ENTRYPOINT ["python3"]
CMD ["-m", "openapi_server"]