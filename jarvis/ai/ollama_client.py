import json
from pathlib import Path
from typing import Any, Callable

import requests
import yaml

from jarvis.core.context_window import ContextManager
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class OllamaClient:
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
        self.config = self._load_config()
        self.model = self.config.get("ollama_model", "llama3:latest")
        self.host = self.config.get("ollama_host", "http://localhost:11434")
        self.timeout = self.config.get("ollama_timeout", 30)
        self.context_length = int(self.config.get("ollama_context_length", 4096))
        self.available = False
        self.context = ContextManager(max_tokens=self.context_length)
        self._check_available()
        if self.available:
            self._resolve_model()

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text()) or {}
        return {}

    def _check_available(self):
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            self.available = r.status_code == 200
            if self.available:
                log.info(f"Ollama available at {self.host}")
            else:
                log.warning(f"Ollama not available (HTTP {r.status_code})")
        except requests.ConnectionError:
            self.available = False
            log.warning("Ollama not running. AI features unavailable.")
        except Exception as e:
            self.available = False
            log.warning(f"Ollama check failed: {e}")

    def _resolve_model(self):
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            if r.status_code != 200:
                return
            data = r.json()
            available = [m["name"] for m in data.get("models", [])]
            if not available:
                log.warning("No models available in Ollama")
                self.available = False
                return
            log.debug(f"Ollama available models: {available}")
            if self.model in available:
                log.info(f"Using configured model: {self.model}")
                return
            log.warning(
                f"Configured model '{self.model}' not found. "
                f"Available: {available}. Falling back to '{available[0]}'."
            )
            self.model = available[0]
        except Exception as e:
            log.warning(f"Model resolution failed: {e}")

    def _parse_error_response(self, response: requests.Response) -> str:
        try:
            body = response.json()
            msg = body.get("error", "")
            if msg:
                return msg
        except (json.JSONDecodeError, ValueError):
            pass
        try:
            text = response.text[:500]
            if text:
                return text
        except Exception:
            pass
        return f"HTTP {response.status_code}"

    def ask(self, prompt: str, system_prompt: str = None, stream: bool = False, on_token: Callable = None) -> str:
        if not self.available:
            return "AI is not available. Please start Ollama with 'ollama serve'."

        if system_prompt is None:
            system_prompt = (
                f"You are {self.config.get('assistant_name', 'Jarvis')}, "
                f"a helpful Linux desktop assistant. "
                f"Respond in {self.config.get('language', 'pt-PT')}. "
                f"Keep responses concise and helpful. "
                f"If asked to perform a system action, explain what you would do."
            )

        context_content = self.context.get_full_context()
        full_prompt = f"{context_content}\n\n{prompt}" if context_content else prompt

        endpoint = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "system": system_prompt,
            "stream": stream,
        }

        log.debug(f"Ollama request: POST {endpoint}")
        log.debug(f"Ollama model: {self.model}")
        log.debug(f"Ollama payload keys: {list(payload.keys())}")
        log.debug(f"Ollama prompt length: {len(full_prompt)} chars")

        try:
            r = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                stream=stream,
            )
            if r.status_code != 200:
                error_detail = self._parse_error_response(r)
                log.error(
                    f"Ollama API error: {r.status_code} - {error_detail} "
                    f"(endpoint: {endpoint}, model: {self.model})"
                )
                if r.status_code == 404:
                    return (
                        f"AI model '{self.model}' not found. "
                        f"Please pull it with: ollama pull {self.model}"
                    )
                if r.status_code >= 500:
                    return "AI server error. Please check if Ollama is running properly."
                return f"AI error: {error_detail}"
            if stream:
                return self._handle_stream_response(r, on_token)
            data = r.json()
            response_text = data.get("response", "")
            log.debug(f"Ollama response received: {len(response_text)} chars")
            return response_text if response_text else "No response generated."
        except requests.Timeout:
            log.error(f"Ollama request timed out after {self.timeout}s")
            return "AI request timed out. Please try again or check Ollama status."
        except requests.ConnectionError:
            log.error("Ollama connection failed")
            self.available = False
            return "AI is not available. Connection to Ollama lost."
        except Exception as e:
            log.error(f"Ollama request failed: {e}")
            return f"AI request failed: {e}"

    def _handle_stream_response(self, response: requests.Response, on_token: Callable = None) -> str:
        full_response = []
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        full_response.append(token)
                        if on_token:
                            on_token(token)
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log.error(f"Ollama stream failed: {e}")
            raise
        return "".join(full_response)

    def set_context_data(self, context_data: dict):
        command = context_data.pop("command", "")
        self.context.set_context(command, context_data)

    def get_context_stats(self) -> dict:
        return self.context.get_stats()

    def is_available(self) -> bool:
        return self.available

    def list_models(self) -> list:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            if r.status_code == 200:
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []
