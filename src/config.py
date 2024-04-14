from pathlib import Path

DB_PATH = Path(__file__).parent.resolve() / "db/data.sqlite"


ERROR_LOG_FILENAME = "error.log"

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s:%(name)s:%(process)d:%(lineno)d %(levelname)s %(module)s.%(funcName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[%(levelname)s] in %(module)s.%(funcName)s: %(message)s",
        },
    },
    "handlers": {
        "logfile": {
            "formatter": "default",
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOG_FILENAME,
            "backupCount": 2,
        },
        "verbose_output": {
            "formatter": "simple",
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": [
                "verbose_output",
                "logfile",
            ],
        },
        "testing": {
            "level": "DEBUG",
            "handlers": [
                "verbose_output",
            ],
        },
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "logfile"
        ]
    },
}

