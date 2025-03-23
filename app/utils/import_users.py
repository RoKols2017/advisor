import csv
from app.models import User, Department
from app.extensions import db

def import_users_from_csv(file_stream):
    decoded = file_stream.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)
    created, errors = 0, []

    for row in reader:
        print("📄 Обрабатываем строку:", row)

        try:
            username = row["SamAccountName"].strip()
            fio = row["DisplayName"].strip()
            dept_code = row["OU"].strip()

            print(f"➡️ username: {username}, fio: {fio}, dept: {dept_code}")

            # ⚠️ Пропускаем без OU — и НЕ добавляем в ошибки
            if not dept_code:
                print(f"⏭️ Пропущен: {username} — без OU")
                continue

            # Найти или создать Department
            department = Department.query.filter_by(code=dept_code).first()
            if not department:
                department = Department(code=dept_code, name=dept_code.upper())
                db.session.add(department)
                db.session.flush()

            # Найти или создать пользователя
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(
                    username=username,
                    fio=fio or username,
                    department=department
                )
                db.session.add(user)
                created += 1

        except Exception as e:
            print("🔥 Ошибка при обработке строки:", e)
            errors.append(str(e))

    db.session.commit()
    return {"created": created, "errors": errors}

