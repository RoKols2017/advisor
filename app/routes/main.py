from flask import Blueprint, render_template, request
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
    dept_code = request.args.get("dept", "").strip().lower()
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    query = PrintEvent.query.join(User).join(Printer).join(Department)

    # 🔽 Фильтр по подразделению
    if dept_code:
        query = query.filter(Printer.department.has(Department.code.ilike(f"%{dept_code}%")))

    # 📅 Фильтр по дате
    if start_date_str:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        query = query.filter(PrintEvent.timestamp >= start_dt)
    if end_date_str:
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(PrintEvent.timestamp <= end_dt)

    events = query.order_by(PrintEvent.timestamp.desc()).limit(500).all()
    total_pages = sum(event.pages for event in events if event.pages)

    all_departments = Department.query.order_by(Department.code).all()

    return render_template("print_events.html",
                           events=events,
                           total_pages=total_pages,
                           departments=all_departments,
                           selected_dept=dept_code)

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
        func.sum(PrintEvent.pages).label("page_sum")
    ).join(Printer, Printer.id == PrintEvent.printer_id) \
        .join(PrinterModel, PrinterModel.id == Printer.model_id) \
        .join(Department, Department.id == Printer.department_id) \
        .join(User, User.id == PrintEvent.user_id)

    # Фильтр по дате
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

    # Группировка до документа
    query = query.group_by(Department.id, Printer.id, User.id, PrintEvent.document_name, PrinterModel.code)

    rows = query.all()

    tree = {}
    total_pages = 0

    # Строим дерево
    tree = {}
    total_pages = 0

    for row in rows:
        dept_key = f"{row.dept_code} — {row.dept_name}"
        printer_key = f"{row.model_code}-{row.room_number}-{row.printer_index}"
        user_key = row.user_fio
        doc_name = row.document_name

        tree.setdefault(dept_key, {"total": 0, "printers": {}})
        dept = tree[dept_key]

        dept["total"] += row.page_sum
        total_pages += row.page_sum

        dept["printers"].setdefault(printer_key, {"total": 0, "users": {}})
        printer = dept["printers"][printer_key]
        printer["total"] += row.page_sum

        printer["users"].setdefault(user_key, {"total": 0, "docs": {}})
        user = printer["users"][user_key]
        user["total"] += row.page_sum

        user["docs"][doc_name] = row.page_sum

    return render_template("print_tree.html",
                           tree=tree,
                           total_pages=total_pages,
                           start_date=start_date_str,
                           end_date=end_date_str)
