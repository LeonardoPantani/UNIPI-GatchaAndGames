############# WARNING #############
#   !   This is a mock file.  !   #
###################################
from flask import jsonify
import inspect

def send_log(message, level="general", service_type="unknown", endpoint="unknown"):
    if endpoint == "unknown":
        endpoint = inspect.stack()[1][3] # name of function that called send_log
    
    print(f"LOG {level}> {message} [{service_type}, {endpoint}]")
    return jsonify({"message": "Log sent"}), 200

def query_logs(service_type, endpoint="unknown", interval=3600, level="general", start_time=None):
    log_values = []

    log_values.append({
        "timestamp": "1733153550",
        "message": "Questo è un log di prova",
        "service_type": service_type,
        "endpoint": endpoint,
        "level": level
    })

    log_values.append({
        "timestamp": "1733153551",
        "message": "Questo è un log di prova",
        "service_type": service_type,
        "endpoint": endpoint,
        "level": level
    })

    log_values.append({
        "timestamp": "1733153553",
        "message": "Questo è un log di prova",
        "service_type": service_type,
        "endpoint": endpoint,
        "level": level
    })
    
    return log_values