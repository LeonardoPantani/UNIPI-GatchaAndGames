import requests
import json
import time
import inspect

# level = general / info / warning / error
def send_log(message, level="general", service_type="unknown", endpoint="unknown"):
    if endpoint == "unknown":
        endpoint = inspect.stack()[1][3] # name of function that called send_log
    
    url = 'http://logging_loki:3100/loki/api/v1/push'
    timestamp = str(int(time.time() * 1e9))
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


def query_logs(service_type, endpoint="unknown", interval=3600, level="general", start_time=None):
    loki_url = "http://logging_loki:3100/loki/api/v1/query_range"
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Ensure interval is a valid number
        interval = float(interval)
        
        # Ensure start_time is a valid number
        if start_time is None:
            start_time_ns = int(time.time() * 1e9) - int(interval * 1e9)
        else:
            start_time_float = float(start_time)
            start_time_ns = int(start_time_float * 1e9)
        
        end_time_ns = start_time_ns + int(interval * 1e9)
        query = f'{{service="{service_type}", endpoint="{endpoint}", level="{level}"}}'
        params = {
            "query": query,
            "start": start_time_ns,
            "end": end_time_ns,
            "limit": 1000
        }
        # Send the query to Loki
        response = requests.get(loki_url, params=params, headers=headers)
        response.raise_for_status()
        
        logs = response.json().get("data", {}).get("result", [])
        
        log_values = []

        for result in logs:
            for log_entry in result.get("values", []):
                timestamp, message = log_entry
                log_values.append({
                    "timestamp": timestamp,
                    "message": message,
                    "service_type": service_type,
                    "endpoint": endpoint,
                    "level": level
                })
        
        return log_values
    except ValueError as ve:
        # Handle invalid start_time or interval
        print(f"Invalid input: start_time={start_time}, interval={interval}. Error: {ve}")
        return None
    except requests.exceptions.RequestException as re:
        # Handle network errors
        print(f"Request error: {re}")
        return None