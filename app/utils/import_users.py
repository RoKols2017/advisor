import csv
import logging
from sqlalchemy import func
from app.models import User, Department
from app.extensions import db

logger = logging.getLogger("import_users_logger")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("import_users.log", mode='a', encoding='utf-8')
handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
logger.addHandler(handler)

def import_users_from_csv(file_stream):
    decoded = file_stream.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)
    created, errors = 0, []

    for row in reader:
        try:
            username = row.get("SamAccountName", "").strip()
            fio = row.get("DisplayName", "").strip()
            dept_code = row.get("OU", "").strip().lower()

            if not dept_code:
                continue  # Пропускаем без OU

            department = Department.query.filter(func.lower(Department.code) == dept_code).first()
            if not department:
                department = Department(code=dept_code, name=dept_code.upper())
                db.session.add(department)

            user = User.query.filter(func.lower(User.username) == username.lower()).first()
            if not user:
                user = User(
                    username=username,
                    fio=fio or username,
                    department=department
                )
                db.session.add(user)
                created += 1

        except Exception as e:
            logger.error(f"🔥 Ошибка строки {row}: {e}")
            errors.append(str(e))

    db.session.commit()
    return {"created": created, "errors": errors}
