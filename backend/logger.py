# 静态日志类，所有模块可通过 Logger.logger 访问
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class Logger:
    log_dir = 'logs/'
    logger = None
    _initialized = False

    @staticmethod
    def get_log_filename():
        today = datetime.now().strftime('%Y-%m-%d')
        return os.path.join(Logger.log_dir, f'ai_doctor_{today}.log')

    @staticmethod
    def custom_namer(default_name):
        base, ext = os.path.splitext(default_name)
        if ext.startswith('.'):
            ext = ext[1:]
        if ext:
            return os.path.join(Logger.log_dir, f'ai_doctor_{ext}.log')
        return default_name

    def __init__(self):
        if Logger._initialized:
            return
        os.makedirs(Logger.log_dir, exist_ok=True)
        log_handler = TimedRotatingFileHandler(
            filename=Logger.get_log_filename(),
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8',
            utc=False,
        )
        log_handler.namer = Logger.custom_namer
        logging.basicConfig(
            level=logging.INFO,
            encoding='utf-8',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                log_handler,
                logging.StreamHandler(),
            ],
        )
        Logger.logger = logging.getLogger('ai_doctor')
        Logger._initialized = True
