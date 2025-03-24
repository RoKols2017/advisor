from datetime import datetime
from app.extensions import db
from app.models import (
    User, Printer, PrinterModel, Building, Department,
    PrintEvent, Computer, Port
)

def import_print_events_from_json(events):
    created, errors = 0, []

    for e in events:
        try:
            username = e.get("Param3")
            document_name = e.get("Param2")
            document_id = int(e.get("Param1") or 0)
            byte_size = int(e.get("Param7") or 0)
            pages = int(e.get("Param8") or 0)
            timestamp_ms = int(e.get("TimeCreated").replace("/Date(", "").replace(")/", ""))
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)

            # ✅ Используем реальный JobID
            job_id = e.get("JobID") or "UNKNOWN"
            existing_event = PrintEvent.query.filter_by(job_id=job_id).first()
            if existing_event:
                print(f"⏭️ Пропущен дубликат job_id={job_id}")
                continue

            # 🎯 Парсинг имени принтера (Param5)
            printer_name = e.get("Param5", "")
            printer_parts = printer_name.split("-")
            if len(printer_parts) != 5:
                errors.append(f"❌ Неверный формат имени принтера: {printer_name}")
                continue

            model_code, bld_code, dept_code, room_number, printer_index = printer_parts
            try:
                printer_index = int(printer_index)
            except ValueError:
                errors.append(f"❌ Некорректный индекс принтера: {printer_index}")
                continue

            # Building
            building = Building.query.filter_by(code=bld_code).first()
            if not building:
                building = Building(code=bld_code, name=bld_code.upper())
                db.session.add(building)
                db.session.flush()

            # Department
            department = Department.query.filter_by(code=dept_code).first()
            if not department:
                department = Department(code=dept_code, name=dept_code.upper())
                db.session.add(department)
                db.session.flush()

            # PrinterModel
            model = PrinterModel.query.filter_by(code=model_code).first()
            if not model:
                model = PrinterModel(
                    code=model_code,
                    manufacturer=model_code.split()[0],
                    model=model_code
                )
                db.session.add(model)
                db.session.flush()

            # Printer
            printer = Printer.query.filter_by(
                building_id=building.id,
                room_number=room_number,
                printer_index=printer_index
            ).first()

            if not printer:
                try:
                    printer = Printer(
                        model=model,
                        building=building,
                        department=department,
                        room_number=room_number,
                        printer_index=printer_index,
                        is_active=True
                    )
                    db.session.add(printer)
                    db.session.flush()
                except Exception as ex:
                    db.session.rollback()
                    errors.append(f"❌ Ошибка при добавлении принтера {printer_name}: {str(ex)}")
                    continue

            # User
            user = User.query.filter_by(username=username).first()
            if not user:
                errors.append(f"❌ Пользователь не найден: {username}")
                continue

            # 🧠 Компьютер (Param4)
            computer = None
            computer_name = e.get("Param4", "")
            comp_parts = computer_name.split("-")
            if len(comp_parts) == 4:
                comp_bld, comp_dept, comp_room, comp_num = comp_parts
                try:
                    comp_num = int(comp_num)
                except:
                    comp_num = 0

                comp_bld_obj = Building.query.filter_by(code=comp_bld).first()
                if not comp_bld_obj:
                    comp_bld_obj = Building(code=comp_bld, name=comp_bld.upper())
                    db.session.add(comp_bld_obj)
                    db.session.flush()

                comp_dept_obj = Department.query.filter_by(code=comp_dept).first()
                if not comp_dept_obj:
                    comp_dept_obj = Department(code=comp_dept, name=comp_dept.upper())
                    db.session.add(comp_dept_obj)
                    db.session.flush()

                computer = Computer.query.filter_by(hostname=computer_name).first()
                if not computer:
                    computer = Computer(
                        hostname=computer_name,
                        full_name=None,
                        building=comp_bld_obj,
                        department=comp_dept_obj,
                        room_number=comp_room,
                        number_in_room=comp_num
                    )
                    db.session.add(computer)
                    db.session.flush()
            else:
                # 👇 поддержка коротких имён ПК
                computer = Computer.query.filter_by(hostname=computer_name).first()
                if not computer:
                    computer = Computer(
                        hostname=computer_name,
                        full_name=computer_name
                    )
                    db.session.add(computer)
                    db.session.flush()

            # Порт (Param6)
            port = None
            port_name = e.get("Param6", "")
            port_parts = port_name.split("-")
            if len(port_parts) == 5:
                port_model, port_bld, port_dept, port_room, port_index = port_parts
                try:
                    port_index = int(port_index)
                except:
                    port_index = 0

                port_bld_obj = Building.query.filter_by(code=port_bld).first()
                if not port_bld_obj:
                    port_bld_obj = Building(code=port_bld, name=port_bld.upper())
                    db.session.add(port_bld_obj)
                    db.session.flush()

                port_dept_obj = Department.query.filter_by(code=port_dept).first()
                if not port_dept_obj:
                    port_dept_obj = Department(code=port_dept, name=port_dept.upper())
                    db.session.add(port_dept_obj)
                    db.session.flush()

                port = Port.query.filter_by(name=port_name).first()
                if not port:
                    port = Port(
                        name=port_name,
                        building=port_bld_obj,
                        department=port_dept_obj,
                        room_number=port_room,
                        printer_index=port_index
                    )
                    db.session.add(port)
                    db.session.flush()

            # Финально: создаём PrintEvent
            try:
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
                errors.append(f"❌ Ошибка при создании события: {str(ex)}")

        except Exception as ex:
            db.session.rollback()
            errors.append(f"💥 Общая ошибка: {str(ex)}")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        errors.append(f"💥 Ошибка при коммите: {str(e)}")

    return {"created": created, "errors": errors}
