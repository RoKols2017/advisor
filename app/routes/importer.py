from flask import Blueprint, request, jsonify
from app.utils.import_users import import_users_from_csv
from app.utils.import_print_events import import_print_events_from_json

importer = Blueprint("importer", __name__)

@importer.route("/import/users", methods=["POST"])
def import_users():
    if "file" not in request.files:
        return jsonify({"error": "Файл не передан"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Ожидается CSV-файл"}), 400

    result = import_users_from_csv(file)
    return jsonify(result)


@importer.route("/import/print-events", methods=["POST"])
def import_print_events():
    if "file" not in request.files:
        return jsonify({"error": "Файл не передан"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".json"):
        return jsonify({"error": "Ожидается JSON-файл"}), 400

    data = file.read().decode("utf-8")
    import json
    events = json.loads(data)
    result = import_print_events_from_json(events)
    return jsonify(result)
