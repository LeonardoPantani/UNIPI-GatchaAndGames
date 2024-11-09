FROM python:3.9-slim

# Setting current workdir
WORKDIR /usr/src/app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . ./openapi_server

EXPOSE 8080

CMD ["python3", "-m", "openapi_server"]