import os
import logging
import datetime
import logging.config
BASE_DIR = f"{os.getcwd()}/logs"
if not os.path.exists(BASE_DIR):
    os.mkdir(BASE_DIR)
logFile = datetime.datetime.now().strftime("%Y-%m-%d") + ".log"
LOGGING = {
    # 当前日志的版本号
    'version': 1,
    # 是否禁用其他的日志处理器
    'disable_existing_loggers': False,
    # 指定日志的显示格式
    "formatters": {
            "simple": {
                'format': '%(asctime)s [%(levelname)s]- %(message)s'
                # 'format': '%(asctime)s - [%(levelname)s] - %(name)s - [msg]%(message)s - [%(filename)s:%(lineno)d ]'
            },
            'standard': {
                'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(levelname)s]- %(message)s'
            },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, logFile),  # 日志文件的位置
            # 日志大小
            'maxBytes': 100 * 1024 * 1024,
            'mode': 'w+',
            # 最多10个日志文件
            'backupCount': 10,
            'formatter': 'simple',
            'encoding': 'utf-8'
        },
    },
    'loggers': {
        'root': {  # 定义了一个名为root的日志器
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'DEBUG',  # 日志器接收的最低日志级别
        },
        'file': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'INFO',  # 日志器接收的最低日志级别
        }
    }
}

logging.config.dictConfig(LOGGING)
