from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils.import_users import import_users_from_csv
from app.utils.import_print_events import import_print_events_from_json
import json

uploader = Blueprint("uploader", __name__)

@uploader.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        ftype = request.form.get("type")
        file = request.files.get("file")

        if not file or file.filename == "":
            flash("❌ Файл не выбран", "danger")
            return redirect(request.url)

        try:
            if ftype == "users" and file.filename.endswith(".csv"):
                result = import_users_from_csv(file)

            elif ftype == "events" and file.filename.endswith(".json"):
                data = file.read().decode("utf-8-sig")
                events = json.loads(data)
                result = import_print_events_from_json(events)

            else:
                flash("❌ Неверный формат файла", "danger")
                return redirect(request.url)

            # Вывод результата
            flash(f"✅ Импортировано: {result['created']}", "success")

            if result["errors"]:
                flash(f"⚠️ Ошибки: {len(result['errors'])}", "warning")

                # Показываем только первые 5 ошибок
                for err in result["errors"][:5]:
                    flash(f"❌ {err}", "danger")

        except Exception as ex:
            flash(f"💥 Неожиданная ошибка: {str(ex)}", "danger")

        return redirect(request.url)

    return render_template("upload.html")
