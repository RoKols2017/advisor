from flask import Blueprint, request, jsonify
from app.utils.import_print_events import import_print_events_from_json

importer = Blueprint("importer", __name__)

@importer.route("/import/print-events", methods=["POST"])
def import_print_events():
    try:
        events = request.get_json()
        if not isinstance(events, list):
            return jsonify({"error": "Invalid format. Expected list of events"}), 400

        result = import_print_events_from_json(events)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
