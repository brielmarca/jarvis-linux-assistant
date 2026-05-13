from pathlib import Path
from typing import Any

import yaml

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()

REQUIRED_FIELDS = {
    "assistant_name": str,
    "language": str,
    "ollama_model": str,
    "ollama_host": str,
}

OPTIONAL_FIELDS = {
    "enable_voice": bool,
    "enable_tts": bool,
    "enable_wake_word": bool,
    "whisper_model": str,
    "whisper_device": str,
    "wake_word": str,
    "wake_word_model": str,
    "wake_word_sensitivity": float,
    "ollama_timeout": (int, float),
    "require_confirmation_for_dangerous_commands": bool,
    "tts_model": str,
}

VALID_LANGUAGES = {"pt-PT", "en-US", "es-ES", "fr-FR", "de-DE", "it-IT", "ja-JP", "ko-KR", "zh-CN"}
VALID_WHISPER_MODELS = {"tiny", "base", "small", "medium", "large", "large-v2", "large-v3"}


class ConfigValidationResult:
    def __init__(self):
        self.valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.fixed: list[str] = []

    def add_error(self, msg: str):
        self.valid = False
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_fixed(self, msg: str):
        self.fixed.append(msg)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def summary(self) -> str:
        parts = []
        if self.errors:
            parts.append(f"Errors ({len(self.errors)}):\n" + "\n".join(f"  - {e}" for e in self.errors))
        if self.warnings:
            parts.append(f"Warnings ({len(self.warnings)}):\n" + "\n".join(f"  - {w}" for w in self.warnings))
        if self.fixed:
            parts.append(f"Fixed ({len(self.fixed)}):\n" + "\n".join(f"  - {f}" for f in self.fixed))
        if not parts:
            parts.append("Config is valid")
        return "\n".join(parts)


def validate_config(config_path: Path | None = None) -> ConfigValidationResult:
    result = ConfigValidationResult()

    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

    if not config_path.exists():
        result.add_error(f"Config file not found: {config_path}")
        return result

    try:
        config = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        result.add_error(f"Invalid YAML: {e}")
        return result

    if not isinstance(config, dict):
        result.add_error("Config is not a dictionary")
        return result

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in config:
            result.add_error(f"Missing required field: '{field}'")
        elif not isinstance(config[field], expected_type):
            result.add_error(f"Field '{field}' should be {expected_type.__name__}, got {type(config[field]).__name__}")

    for field, expected_type in OPTIONAL_FIELDS.items():
        if field in config and not isinstance(config[field], expected_type):
            result.add_warning(f"Field '{field}' should be {expected_type.__name__}, got {type(config[field]).__name__}")

    lang = config.get("language")
    if lang and lang not in VALID_LANGUAGES:
        result.add_warning(f"Unrecognized language '{lang}'. Valid: {', '.join(sorted(VALID_LANGUAGES))}")

    whisper = config.get("whisper_model")
    if whisper and whisper not in VALID_WHISPER_MODELS:
        result.add_warning(f"Unrecognized whisper model '{whisper}'. Valid: {', '.join(VALID_WHISPER_MODELS)}")

    host = config.get("ollama_host", "")
    if host and not host.startswith("http"):
        result.add_warning(f"ollama_host should start with http:// or https://, got '{host}'")

    timeout = config.get("ollama_timeout", 30)
    if isinstance(timeout, (int, float)) and (timeout < 1 or timeout > 120):
        result.add_warning(f"ollama_timeout should be between 1 and 120 seconds, got {timeout}")

    enabled = config.get("enabled_skills", [])
    if not isinstance(enabled, list):
        result.add_error("enabled_skills should be a list")
    elif not enabled:
        result.add_warning("No skills are enabled")

    perms = config.get("permissions", {})
    if not isinstance(perms, dict):
        result.add_warning("permissions should be a dictionary")

    return result
