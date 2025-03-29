import os
import time
import glob
import logging

from app.utils.import_users import import_users_from_csv
from app.utils.import_print_events import import_print_events_from_json

IMPORT_DIR = './import_dir'
SLEEP_TIME = 10  # seconds

logger = logging.getLogger("import_daemon")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("import_daemon.log", mode='a', encoding='utf-8')
handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
logger.addHandler(handler)


def process_ad_users():
    users_file = os.path.join(IMPORT_DIR, 'ad_users.csv')
    if os.path.isfile(users_file):
        logger.info("👥 Найден ad_users.csv")
        try:
            with open(users_file, "rb") as f:
                result = import_users_from_csv(f)
            logger.info(f"✅ Пользователи загружены: {result}")
            os.remove(users_file)
            logger.info("🗑️ ad_users.csv удалён")
        except Exception as e:
            logger.error(f"💥 Ошибка при импорте пользователей: {e}")


def process_print_events():
    json_files = sorted(
        glob.glob(os.path.join(IMPORT_DIR, '*-prn-event*.json')),
        key=os.path.getctime
    )
    for json_file in json_files:
        logger.info(f"🖨️ Найден файл событий: {os.path.basename(json_file)}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                import json
                events = json.load(f)
            result = import_print_events_from_json(events)
            logger.info(f"✅ События загружены: {result}")
            os.remove(json_file)
            logger.info(f"🗑️ Файл {os.path.basename(json_file)} удалён")
        except Exception as e:
            logger.error(f"💥 Ошибка при импорте событий {json_file}: {e}")


if __name__ == "__main__":
    logger.info("🟣 Daemon запущен, наблюдаем за каталогом импорта...")
    while True:
        process_ad_users()
        process_print_events()
        time.sleep(SLEEP_TIME)
