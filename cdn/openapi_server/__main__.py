from flask import Flask, request, send_file, jsonify
from openapi_server.helpers.logging import send_log
from openapi_server.helpers.authorization import verify_login
import os
import uuid
from PIL import Image

app = Flask(__name__)

SERVICE_TYPE = "cdn"
STORAGE_DIR = "/app/openapi_server/storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

"""Verifica se una stringa è un UUID valido."""
def is_valid_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

@app.route("/upload", methods=["POST"])
def upload_image():
    session = verify_login(request.headers.get('Authorization'), service_type=SERVICE_TYPE, audience_required="private_services")
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione

    # Controlla se l'UUID è fornito nella query string
    file_uuid = request.args.get("uuid")
    if not file_uuid:
        return jsonify({"error": "UUID is required in query."}), 400

    # Verifica che l'UUID sia valido
    if not is_valid_uuid(file_uuid):
        return jsonify({"error": "Invalid UUID format."}), 400

    # Controlla che il file sia presente
    if "file" not in request.files:
        send_log("No file provided.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        send_log("Empty filename.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Empty filename."}), 400

    file_path = os.path.join(STORAGE_DIR, f"{file_uuid}.png")

    try:
        img = Image.open(file)

        if img.format != "PNG":
            return jsonify({"error": "Only PNG images are allowed."}), 400

        if os.path.exists(file_path):
            img.save(file_path, "PNG")
            send_log(f"User '{session['username']}' updated the image {file_uuid}.", level="general", service_type=SERVICE_TYPE)
            return jsonify({"message": "Image updated."}), 200

        img.save(file_path, "PNG")
        send_log(f"User '{session['username']}' saved the image: {file_uuid}", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message": f"File saved as {file_uuid}.png"}), 201

    except Exception as e:
        send_log(f"File processing error: {str(e)}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": f"File processing error: {str(e)}"}), 400

@app.route("/image/<file_uuid>", methods=["GET"])
def get_image(file_uuid):
    file_path = os.path.join(STORAGE_DIR, f"{file_uuid}.png")
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path)

@app.route("/delete/<file_uuid>", methods=["DELETE"])
def delete_image(file_uuid):
    session = verify_login(request.headers.get('Authorization'), service_type=SERVICE_TYPE, audience_required="private_services")
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione

    if not is_valid_uuid(file_uuid):
        return jsonify({"error": "Invalid UUID format."}), 400

    file_path = os.path.join(STORAGE_DIR, f"{file_uuid}.png")

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found."}), 404

    try:
        os.remove(file_path)
        send_log(f"File deleted: {file_uuid}", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message": "File successfully deleted."}), 200
    except Exception as e:
        send_log(f"Error deleting file: {str(e)}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": f"Error deleting file: {str(e)}"}), 500


@app.route("/health_check", methods=["GET"])
def health_check():
    return jsonify({"message": "Service operational."}), 200

if __name__ == "__main__":
    # secret key flask
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')
    app.config['jwt_secret_key'] = os.environ.get('JWT_SECRET_KEY')
    app.config['requests_timeout'] = int(os.environ.get('REQUESTS_TIMEOUT'))
    app.config['database_timeout'] = int(os.environ.get('DATABASE_TIMEOUT'))

    app.run(host="0.0.0.0", port=443, debug=True, ssl_context=("/app/ssl/cdn-cert.pem", "/app/ssl/cdn-key.pem"))