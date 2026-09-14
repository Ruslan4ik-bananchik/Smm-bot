import sys
from pathlib import Path
from logging import Logger, getLogger, StreamHandler, Formatter, DEBUG, INFO, ERROR
from logging.handlers import RotatingFileHandler
from application.ports.outbound.logger_port import LoggerPort
from .tz_clock import TZClock


class InfraLogger(LoggerPort):
    """
    Инфраструктурный логгер для проекта.
    Объединяет настройку логирования в консоль, в файл и в отдельный файл ошибок.
    Поддерживает таймзону Екатеринбурга.
    """

    def __init__(
        self,
        tz_clock: TZClock,
        name: str = "main",
        log_dir: str = "logs",
        console_level: int = INFO,
        file_level: int = INFO,
        error_level: int = ERROR,
    ):
        self.logger: Logger = getLogger(name)
        self.logger.setLevel(DEBUG)
        self.logger.handlers.clear()

        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(exist_ok=True)

        formatter = Formatter(
            '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        formatter.converter = lambda ts: tz_clock.now().timetuple()

        # Консоль
        console_handler = StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Основной файл с ротацией
        file_handler = RotatingFileHandler(
            log_dir_path / f"{name}.log",
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Файл ошибок
        error_handler = RotatingFileHandler(
            log_dir_path / f"{name}_errors.log",
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(error_level)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

    # --- Методы порта ---
    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def exception(self, msg: str):
        self.logger.exception(msg)
