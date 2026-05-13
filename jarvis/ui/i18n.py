import json
import logging
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

log = logging.getLogger("jarvis.i18n")


class TranslationManager(QObject):
    languageChanged = pyqtSignal(str)

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._translations: dict[str, str] = {}
        self._fallback: dict[str, str] = {}
        self._current_lang = "en"
        self._translations_dir = Path(__file__).parent.parent.parent / "translations"
        self._load_file("en")

    def _load_file(self, lang: str) -> bool:
        path = self._translations_dir / f"{lang}.json"
        if not path.exists():
            log.warning("Translation file not found: %s", path)
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if lang == "en":
                self._fallback = data
            self._translations = data
            log.info("Loaded translation file: %s (%d keys)", path, len(data))
            return True
        except Exception as e:
            log.error("Failed to load translation %s: %s", path, e)
            return False

    def set_language(self, lang: str):
        if lang == self._current_lang and self._translations:
            return
        if not self._load_file(lang):
            fallback_path = self._translations_dir / "en.json"
            if fallback_path.exists():
                self._translations = json.loads(fallback_path.read_text(encoding="utf-8"))
                log.info("Falling back to English for language: %s", lang)
        self._current_lang = lang
        log.info("Language switched to: %s", lang)
        self.languageChanged.emit(lang)

    def get(self, key: str, **kwargs) -> str:
        value = self._translations.get(key)
        if value is None:
            value = self._fallback.get(key)
        if value is None:
            log.debug("Missing translation key: %s", key)
            return key
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value
        return value

    def current_language(self) -> str:
        return self._current_lang


tr = TranslationManager()
t = tr.get
