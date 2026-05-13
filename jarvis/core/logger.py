import logging
import sys
from datetime import datetime
from pathlib import Path


class JarvisLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.log_dir = Path.home() / ".jarvis" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.callbacks = []

        self.logger = logging.getLogger("jarvis")
        self.logger.setLevel(logging.DEBUG)

        fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")

        fh = logging.FileHandler(
            self.log_dir / f"jarvis_{datetime.now().strftime('%Y%m%d')}.log"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(fmt)
        self.logger.addHandler(sh)

    def on_log(self, callback):
        self.callbacks.append(callback)

    def _log(self, level, msg):
        getattr(self.logger, level)(msg)
        for cb in self.callbacks:
            try:
                cb(level, msg)
            except Exception:
                pass

    def info(self, msg):
        self._log("info", msg)

    def debug(self, msg):
        self._log("debug", msg)

    def warning(self, msg):
        self._log("warning", msg)

    def error(self, msg):
        self._log("error", msg)

    def critical(self, msg):
        self._log("critical", msg)

    def get_recent(self, n=100):
        log_file = self.log_dir / f"jarvis_{datetime.now().strftime('%Y%m%d')}.log"
        if not log_file.exists():
            return []
        lines = log_file.read_text().strip().split("\n")
        return lines[-n:]
