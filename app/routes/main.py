from collections import OrderedDict
from flask import Blueprint, render_template, request, send_file
import io
import xlsxwriter
from app.extensions import db
from app.models import PrintEvent, User, Printer, Department, PrinterModel
from datetime import datetime

main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/")
def index():
    return render_template("index.html")

@main_blueprint.route("/users")
def users():
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        query = query.filter(
            (User.username.ilike(f"%{q}%")) |
            (User.fio.ilike(f"%{q}%"))
        )
    all_users = query.order_by(User.username.asc()).all()
    return render_template("users.html", users=all_users)

@main_blueprint.route("/print-events")
def print_events():
    from sqlalchemy import func
    dept_code = request.args.get("dept", "").strip().lower()
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    base_query = PrintEvent.query.join(User).join(Printer).join(Department)

    if dept_code:
        base_query = base_query.filter(Printer.department.has(Department.code.ilike(f"%{dept_code}%")))

    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            base_query = base_query.filter(PrintEvent.timestamp >= start_dt)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            base_query = base_query.filter(PrintEvent.timestamp <= end_dt)
        except ValueError:
            pass

    # 🔁 Сначала считаем общее число страниц без LIMIT
    total_pages = base_query.with_entities(func.sum(PrintEvent.pages)).scalar() or 0

    # 🧾 Только потом получаем события (ограниченные)
    events = base_query.order_by(PrintEvent.timestamp.desc()).limit(500).all()

    all_departments = Department.query.order_by(Department.code).all()

    return render_template("print_events.html",
                           events=events,
                           total_pages=total_pages,
                           departments=all_departments,
                           selected_dept=dept_code,
                           start_date=start_date_str,
                           end_date=end_date_str)


@main_blueprint.route("/print-tree")
def print_tree():
    from sqlalchemy import func
    from app.models import PrintEvent, Department, Printer, PrinterModel, User
    from datetime import datetime

    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    query = db.session.query(
        Department.code.label("dept_code"),
        Department.name.label("dept_name"),
        Printer.id.label("printer_id"),
        Printer.room_number,
        Printer.printer_index,
        PrinterModel.code.label("model_code"),
        User.fio.label("user_fio"),
        PrintEvent.document_name,
        func.sum(PrintEvent.pages).label("page_sum"),
        func.max(PrintEvent.timestamp).label("last_time")
    ).join(Printer, Printer.id == PrintEvent.printer_id) \
        .join(PrinterModel, PrinterModel.id == Printer.model_id) \
        .join(Department, Department.id == Printer.department_id) \
        .join(User, User.id == PrintEvent.user_id)

    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            query = query.filter(PrintEvent.timestamp >= start_dt)
        except ValueError:
            pass
    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(PrintEvent.timestamp <= end_dt)
        except ValueError:
            pass

    query = query.group_by(
        Department.id, Printer.id, User.id,
        PrintEvent.document_name, PrinterModel.code
    )

    rows = query.all()

    total_pages = 0
    max_lengths = {
        "dept": 0,
        "printer": 0,
        "user": 0,
        "doc": 0
    }

    # ➕ Первый проход: собрать данные + длины
    temp_tree = {}

    for row in rows:
        dept_name = f"{row.dept_code} — {row.dept_name}"
        printer_name = f"{row.model_code}-{row.room_number}-{row.printer_index}"
        user_name = row.user_fio
        doc_name = row.document_name

        # обновить длины
        max_lengths["dept"] = max(max_lengths["dept"], len(dept_name))
        max_lengths["printer"] = max(max_lengths["printer"], len(printer_name))
        max_lengths["user"] = max(max_lengths["user"], len(user_name))
        max_lengths["doc"] = max(max_lengths["doc"], len(doc_name))

        total_pages += row.page_sum

        temp_tree.setdefault(dept_name, {"total": 0, "printers": {}})
        dept = temp_tree[dept_name]
        dept["total"] += row.page_sum

        dept["printers"].setdefault(printer_name, {"total": 0, "users": {}})
        printer = dept["printers"][printer_name]
        printer["total"] += row.page_sum

        printer["users"].setdefault(user_name, {"total": 0, "docs": {}})
        user = printer["users"][user_name]
        user["total"] += row.page_sum

        user["docs"].setdefault(doc_name, []).append({
            "pages": row.page_sum,
            "timestamp": row.last_time
        })

    def pad(s, key):
        return s.ljust(max_lengths[key])

    for dept in temp_tree.values():
        for printer in dept["printers"].values():
            for user in printer["users"].values():
                # считаем total страниц на каждый документ
                doc_totals = {
                    doc: sum(entry["pages"] for entry in entries)
                    for doc, entries in user["docs"].items()
                }

                # сортируем документы по total pages (убывание)
                sorted_docs = OrderedDict(
                    sorted(user["docs"].items(), key=lambda x: doc_totals[x[0]], reverse=True)
                )

                # выравниваем названия документов
                padded_docs = OrderedDict()
                for doc, entries in sorted_docs.items():
                    MAX_DOC_WIDTH = 80
                    if len(doc) > MAX_DOC_WIDTH:
                        padded_name = doc[:MAX_DOC_WIDTH - 1] + "…"  # без .ljust!
                    else:
                        padded_name = doc.ljust(MAX_DOC_WIDTH)
                    padded_docs[padded_name] = entries

                user["docs"] = padded_docs
    # 🔁 Второй проход: выравнивание + сортировка
    tree = {
        pad(dept, "dept"): {
            "total": d["total"],
            "printers": {
                pad(printer, "printer"): {
                    "total": p["total"],
                    "users": {
                        pad(user, "user"): u
                        for user, u in sorted(p["users"].items(), key=lambda x: x[1]["total"], reverse=True)
                    }
                }
                for printer, p in sorted(d["printers"].items(), key=lambda x: x[1]["total"], reverse=True)
            }
        }
        for dept, d in sorted(temp_tree.items(), key=lambda x: x[1]["total"], reverse=True)
    }

    return render_template("print_tree.html",
                           tree=tree,
                           total_pages=total_pages,
                           start_date=start_date_str,
                           end_date=end_date_str)


@main_blueprint.route("/print-tree/export")
def export_tree_excel():
    # 🔁 Повтори ту же выборку данных, что и в print_tree()
    # Для простоты, здесь можно использовать текущий `print_tree()` как отдельную функцию,
    # или собрать аналогичный список событий

    from app.models import PrintEvent, Department, Printer, PrinterModel, User
    from datetime import datetime
    from sqlalchemy import func

    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    query = db.session.query(
        Department.code.label("dept_code"),
        Department.name.label("dept_name"),
        PrinterModel.code.label("model_code"),
        Printer.room_number,
        Printer.printer_index,
        User.fio.label("user_fio"),
        PrintEvent.document_name,
        PrintEvent.pages,
        PrintEvent.timestamp
    ).join(Printer, Printer.id == PrintEvent.printer_id) \
     .join(PrinterModel, PrinterModel.id == Printer.model_id) \
     .join(Department, Department.id == Printer.department_id) \
     .join(User, User.id == PrintEvent.user_id)

    # Фильтр по дате
    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            query = query.filter(PrintEvent.timestamp >= start_dt)
        except:
            pass
    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(PrintEvent.timestamp <= end_dt)
        except:
            pass

    rows = query.order_by(Department.name, Printer.room_number, User.fio, PrintEvent.timestamp).all()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = workbook.add_worksheet("Print Events")

    # Заголовки
    headers = ["Отдел", "Принтер", "ФИО", "Документ", "Страниц", "Дата"]
    for col, h in enumerate(headers):
        ws.write(0, col, h)

    # Заполнение
    for i, row in enumerate(rows, start=1):
        printer_name = f"{row.model_code}-{row.room_number}-{row.printer_index}"
        ws.write(i, 0, f"{row.dept_code} — {row.dept_name}")
        ws.write(i, 1, printer_name)
        ws.write(i, 2, row.user_fio)
        ws.write(i, 3, row.document_name)
        ws.write(i, 4, row.pages)
        ws.write(i, 5, row.timestamp.strftime('%d.%m.%Y %H:%M'))

    workbook.close()
    output.seek(0)

    return send_file(output,
                     download_name="print_events_tree.xlsx",
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
