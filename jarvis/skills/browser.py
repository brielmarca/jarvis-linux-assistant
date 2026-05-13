from jarvis.skills.base import BaseSkill
from jarvis.automation.apps import launch_app
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class BrowserSkill(BaseSkill):
    def patterns(self):
        return [
            r"\b(pesquis[ae]?|search|look up|google|find)\s+(.+)$",
            r"\b(search|pesquis[ae]?)\s+(?:for|por|the web for)\s+(.+)$",
            r"\b(abre?|open)\s+(site|website|url|página)\s+(.+)$",
            r"\b(go to|navega?|navigate|visit)\s+(.+)$",
        ]

    def _search_web(self, query: str) -> str:
        import urllib.parse
        import subprocess
        encoded = urllib.parse.quote(query)
        url = f"https://google.com/search?q={encoded}"
        try:
            subprocess.Popen(["firefox", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Searching for '{query}' in Firefox"
        except FileNotFoundError:
            return "Firefox not found. Please install Firefox."

    def _open_url(self, url: str) -> str:
        import subprocess
        if not url.startswith("http"):
            url = f"https://{url}"
        try:
            subprocess.Popen(["firefox", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opening {url}"
        except FileNotFoundError:
            return "Firefox not found."

    def execute(self, command: str, match) -> str:
        if not match:
            for p in self._patterns:
                match = p.search(command)
                if match:
                    break

        cmd_lower = command.lower()
        lastindex = match.lastindex if match and match.lastindex else 0

        if "search" in cmd_lower or "pesquis" in cmd_lower or "google" in cmd_lower or "find" in cmd_lower or "look up" in cmd_lower:
            query = match.group(lastindex).strip() if match and lastindex >= 2 else command
            prefixes = ["for ", "por ", "the web for ", "na web por ", "na internet por "]
            for p in prefixes:
                if query.lower().startswith(p):
                    query = query[len(p):].strip()
                    break
            if query:
                return self._search_web(query)

        if "site" in cmd_lower or "website" in cmd_lower or "url" in cmd_lower:
            url = match.group(3).strip() if match and lastindex >= 3 else ""
            if url:
                return self._open_url(url)

        if "go to" in cmd_lower or "navega" in cmd_lower or "navigate" in cmd_lower or "visit" in cmd_lower:
            url = match.group(4).strip() if match and lastindex >= 4 else ""
            if url:
                return self._open_url(url)

        return "I didn't understand the browser command."

        return launch_app("firefox")
