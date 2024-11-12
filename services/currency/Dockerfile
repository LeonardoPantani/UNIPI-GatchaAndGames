FROM python:3-alpine

# Setting current workdir
WORKDIR /usr/src/app

# Copy requirements file
COPY requirements.txt /usr/src/app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 3003

ENTRYPOINT ["python3"]
CMD ["-m", "openapi_server"]