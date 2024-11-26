import requests
import json
import time

SERVICE_TYPE = "auth"

def send_log(message, level="general", service_type=SERVICE_TYPE, endpoint="unknown"):
    url = 'http://logging_loki:3100/loki/api/v1/push'
    timestamp = str(int(time.time() * 1e9))  # Current time in nanoseconds
    log_entry = {
        "streams": [
            {
                "stream": {
                    "level": level,
                    "service": service_type,
                    "endpoint": endpoint,
                },
                "values": [
                    [timestamp, message]
                ]
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(log_entry), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending log: {e}")
