import json
from pathlib import Path


class TranslationManager:
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
        self._translations = {}
        self._fallback = {}
        self._current_lang = "en"
        self._callbacks = []
        self._load_fallback()
        self._translations_dir = Path(__file__).parent.parent.parent / "translations"

    def _load_fallback(self):
        p = Path(__file__).parent.parent.parent / "translations" / "en.json"
        if p.exists():
            self._fallback = json.loads(p.read_text(encoding="utf-8"))

    def set_language(self, lang: str):
        self._current_lang = lang
        lang_file = self._translations_dir / f"{lang}.json"
        if lang_file.exists():
            self._translations = json.loads(lang_file.read_text(encoding="utf-8"))
        else:
            self._translations = {}
        for cb in self._callbacks:
            cb()

    def get(self, key: str, **kwargs) -> str:
        value = self._translations.get(key)
        if value is None:
            value = self._fallback.get(key)
        if value is None:
            return key
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value
        return value

    def on_change(self, callback):
        self._callbacks.append(callback)

    def current_language(self) -> str:
        return self._current_lang


tr = TranslationManager()
t = tr.get
