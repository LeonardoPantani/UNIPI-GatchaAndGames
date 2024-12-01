from flask import Flask, request, send_file, jsonify
from helpers.logging import send_log
import os
import uuid
from PIL import Image

app = Flask(__name__)

SERVICE_TYPE="cdn"
STORAGE_DIR = "./storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

def is_valid_uuid(value):
    """Verifica se una stringa è un UUID valido."""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


@app.route("/upload", methods=["POST"])
def upload_image():
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
            send_log("Image updated.", level="general", service_type=SERVICE_TYPE)
            return jsonify({"message": "Image updated."}), 200


        img.save(file_path, "PNG")
        send_log(f"Image saved as: {file_uuid}", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message": f"File saved as {file_uuid}.png."}), 201

    except Exception as e:
        return jsonify({"error": f"File processing error: {str(e)}"}), 400

@app.route("/image/<file_uuid>", methods=["GET"])
def get_image(file_uuid):
    file_path = os.path.join(STORAGE_DIR, f"{file_uuid}.png")
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path)

@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
