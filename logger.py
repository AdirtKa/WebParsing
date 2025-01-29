"""Logger configuration."""

import logging
import sys
import inspect
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Пути к логам
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)  # Создаём папку logs, если её нет

# Форматирование логов
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Параметры ротации логов
MAX_LOG_SIZE = 10 * 1024 * 1024  # Максимальный размер лог-файла (10 MB)
BACKUP_COUNT = 5  # Количество резервных копий

# Создаём основной обработчик для консоли (цветной вывод)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # В консоль выводим только INFO и выше
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))


# Функция для создания логгера с динамическим именем лог-файла и ротацией
def get_logger(name: str):
    """
    make configured logger

    :param name: logger name
    :return: configured logger
    """
    logger = logging.getLogger(name)  # Создаём логгер для конкретного модуля
    logger.setLevel(logging.DEBUG)  # Общий уровень логирования

    # Если программа запущена как основной скрипт, используем имя файла
    if name == "__main__":
        # Извлекаем имя скрипта без расширения
        module_name = Path(inspect.stack()[-1].filename).stem
    else:
        # Используем имя модуля
        module_name = name.split('.')[-1]

    # Имя лог-файла будет соответствовать имени модуля
    log_file = LOG_DIR / f"{module_name}.log"

    # Обработчик для ротации лог-файла
    file_handler = RotatingFileHandler(
        log_file, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # Логируем всё в файл
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
