import re
import subprocess
import urllib.parse
from typing import Any

from jarvis.agents.base_agent import BaseAgent
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class BrowserAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="browser", description="Web search and browsing")

    def can_handle(self, command: str, context: dict | None = None) -> tuple[bool, float]:
        cmd = command.lower()
        if any(kw in cmd for kw in ["search", "pesquis", "google", "find", "look up",
                                     "open site", "open website", "abre site",
                                     "go to", "navega", "navigate", "visit",
                                     "firefox", "browser"]):
            return True, 0.8
        return False, 0.0

    def execute(self, command: str, context: dict | None = None) -> dict[str, Any]:
        cmd = command.lower().strip()

        if "search" in cmd or "pesquis" in cmd or "google" in cmd or "find" in cmd or "look up" in cmd:
            match = re.search(r"(?:search|pesquis[ae]?|google|find|look up)\s+(?:for |por |the web for )?(.+)", cmd)
            if match:
                query = match.group(1).strip()
                encoded = urllib.parse.quote(query)
                url = f"https://google.com/search?q={encoded}"
                try:
                    subprocess.Popen(["firefox", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return {"response": f"Searching for '{query}' in Firefox", "agent": "browser"}
                except FileNotFoundError:
                    return {"response": "Firefox not found. Please install Firefox.", "agent": "browser"}
            return {"response": "What should I search for?", "agent": "browser"}

        if "open" in cmd and ("site" in cmd or "website" in cmd or "url" in cmd or "página" in cmd):
            match = re.search(r"(?:open|abre?)\s+(?:site|website|url|página)\s+(.+)", cmd)
            if match:
                url = match.group(1).strip()
                if not url.startswith("http"):
                    url = f"https://{url}"
                try:
                    subprocess.Popen(["firefox", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return {"response": f"Opening {url}", "agent": "browser"}
                except FileNotFoundError:
                    return {"response": "Firefox not found.", "agent": "browser"}

        if "go to" in cmd or "navega" in cmd or "navigate" in cmd or "visit" in cmd:
            match = re.search(r"(?:go to|navega|navigate|visit)\s+(.+)", cmd)
            if match:
                url = match.group(1).strip()
                if not url.startswith("http"):
                    url = f"https://{url}"
                try:
                    subprocess.Popen(["firefox", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return {"response": f"Opening {url}", "agent": "browser"}
                except FileNotFoundError:
                    return {"response": "Firefox not found.", "agent": "browser"}

        try:
            subprocess.Popen(["firefox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"response": "Opening Firefox", "agent": "browser"}
        except FileNotFoundError:
            return {"response": "Firefox not found.", "agent": "browser"}
