import logging
import colorlog

def setup_logger():
    # Создаем обработчик для терминала
    handler = colorlog.StreamHandler()
    # Настраиваем цвета для каждого уровня
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler.setFormatter(formatter)

    # 3. Настраиваем основной логгер
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


# Создаем объект логгера для импорта
logger = setup_logger()