import logging
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models import (
    User, Printer, PrinterModel, Building, Department,
    PrintEvent, Computer, Port
)

logger = logging.getLogger("import_events")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("import_events.log", mode='a', encoding='utf-8')
handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
logger.addHandler(handler)


def ci_filter(model, column, value):
    """Case-insensitive query filter"""
    return model.query.filter(func.lower(column) == value.lower()).first()


def import_print_events_from_json(events):
    created, errors = 0, []

    for e in events:
        try:
            with db.session.begin_nested():
                username = (e.get("Param3") or "").strip().lower()
                document_name = e.get("Param2") or ""
                document_id = int(e.get("Param1") or 0)
                byte_size = int(e.get("Param7") or 0)
                pages = int(e.get("Param8") or 0)
                timestamp_ms = int(e.get("TimeCreated").replace("/Date(", "").replace(")/", ""))
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                job_id = e.get("JobID") or "UNKNOWN"

                if PrintEvent.query.filter_by(job_id=job_id).first():
                    continue

                printer_name = (e.get("Param5") or "")
                printer_parts = printer_name.strip().lower().split("-")
                if len(printer_parts) != 5:
                    errors.append(f"❌ Неверный формат принтера: {printer_name}")
                    continue

                model_code, bld_code, dept_code, room_number, printer_index = printer_parts
                printer_index = int(printer_index)

                building = ci_filter(Building, Building.code, bld_code) or Building(code=bld_code, name=bld_code.upper())
                db.session.add(building)

                department = ci_filter(Department, Department.code, dept_code) or Department(code=dept_code, name=dept_code.upper())
                db.session.add(department)

                model = ci_filter(PrinterModel, PrinterModel.code, model_code) or PrinterModel(
                    code=model_code,
                    manufacturer=model_code.split()[0],
                    model=model_code
                )
                db.session.add(model)

                printer = Printer.query.filter(
                    func.lower(Printer.room_number) == room_number,
                    Printer.printer_index == printer_index,
                    Printer.building_id == building.id
                ).first() or Printer(
                    model=model,
                    building=building,
                    department=department,
                    room_number=room_number,
                    printer_index=printer_index,
                    is_active=True
                )
                db.session.add(printer)

                user = ci_filter(User, User.username, username)
                if not user:
                    errors.append(f"❌ Пользователь не найден: {username}")
                    continue

                # Computer
                computer = None
                computer_name = (e.get("Param4") or "").strip().lower()
                if computer_name:
                    computer = ci_filter(Computer, Computer.hostname, computer_name)
                    if not computer:
                        parts = computer_name.split("-")
                        if len(parts) == 4:
                            bld, dept, room, num = parts
                            num = int(num) if num.isdigit() else 0
                            cb = ci_filter(Building, Building.code, bld) or Building(code=bld, name=bld.upper())
                            cd = ci_filter(Department, Department.code, dept) or Department(code=dept, name=dept.upper())
                            db.session.add_all([cb, cd])
                            computer = Computer(
                                hostname=computer_name,
                                building=cb,
                                department=cd,
                                room_number=room,
                                number_in_room=num
                            )
                        else:
                            computer = Computer(
                                hostname=computer_name,
                                full_name=computer_name
                            )
                        db.session.add(computer)

                # Port
                port = None
                port_name = (e.get("Param6") or "").strip().lower()
                port_parts = port_name.split("-")
                if len(port_parts) == 5:
                    port_model, port_bld, port_dept, port_room, port_index = port_parts
                    port_index = int(port_index) if port_index.isdigit() else 0

                    pb = ci_filter(Building, Building.code, port_bld) or Building(code=port_bld, name=port_bld.upper())
                    pd = ci_filter(Department, Department.code, port_dept) or Department(code=port_dept, name=port_dept.upper())
                    db.session.add_all([pb, pd])

                    port = ci_filter(Port, Port.name, port_name) or Port(
                        name=port_name,
                        building=pb,
                        department=pd,
                        room_number=port_room,
                        printer_index=port_index
                    )
                    db.session.add(port)

                event = PrintEvent(
                    document_id=document_id,
                    document_name=document_name,
                    user=user,
                    printer=printer,
                    job_id=job_id,
                    timestamp=timestamp,
                    byte_size=byte_size,
                    pages=pages,
                    computer=computer,
                    port=port
                )
                db.session.add(event)
                created += 1

        except Exception as ex:
            db.session.rollback()
            logger.error(f"🔥 Ошибка события: {str(ex)}")
            errors.append(str(ex))

    db.session.commit()
    return {"created": created, "errors": errors}
