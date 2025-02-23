import sys
import logging

# Класс для перенаправления stdout в логгер
class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip():  # Игнорируем пустые строки
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass  # Не требуется для логгера

def create_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Создаем логгер
    logger = logging.getLogger()
    # Перенаправляем stdout и stderr в логгер
    sys.stdout = LoggerWriter(logger, logging.INFO)
    sys.stderr = LoggerWriter(logger, logging.ERROR)