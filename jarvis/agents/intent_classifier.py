import re
from typing import Any


AUTOMATION_CATEGORIES = {"system", "automation", "media_control", "browser", "coding", "workflow"}
CONVERSATION_CATEGORIES = {"conversation", "greeting", "query"}
CONFIDENCE_HIGH = 0.6
CONFIDENCE_MEDIUM = 0.3


class IntentClassifier:
    def __init__(self):
        self._intents: dict[str, list[tuple[str, float]]] = {
            "conversation": [
                (r"^(oi|ol[áa]|hey|hello|hi|bom dia|boa tarde|boa noite|e a[ií]|falae?|saudaç[ão]es)\b", 0.95),
                (r"^(who are you|quem [eé] voc[êe]|what are you|o que [eé] voc[êe]|qual [eé] seu nome)\b", 0.92),
                (r"^(what can you do|o que voc[êe] (pode|sabe|faz)|help|ajuda|comandos|o que faz)\b", 0.9),
                (r"^(how are you|como voc[êe] est[áa]|tudo bem|como vai|beleza)\b", 0.92),
                (r"^(thanks|obrigado|valeu|brigad[ao]|muito obrigado|grato)\b", 0.85),
                (r"^(good morning|good afternoon|good evening)\b", 0.92),
                (r"^(tell me a joke|conta uma piada|make me laugh|me faz rir)\b", 0.88),
                (r"^(tell me a story|conta uma hist[óo]ria)\b", 0.85),
                (r"^(what[‘']?s up|e a[ií]|suave|de boa)\b", 0.85),
                (r"^(nothing|nada|tudo bem|ok|okay|legal)\b", 0.7),
                (r"^(eu s[oa]?u|my name is|me chamo)\b", 0.7),
                (r"^[^a-z0-9]*$", 0.4),
            ],
            "system": [
                (r"\b(time|hora|date|data|shutdown|deslig|reboot|reinici|system info|status|uptime|cpu|memory|disk|kernel)\b", 0.8),
                (r"\binformaçõ[eê]s?\b.*\bsistema\b", 0.9),
                (r"\b(systemctl|service|daemon)\b", 0.7),
            ],
            "coding": [
                (r"\b(git|commit|push|pull|branch|merge|clone|status|diff)\b", 0.9),
                (r"\b(code|vscode|programming|dev|modo programador|coding mode|modo código)\b", 0.8),
                (r"\b(open project|abre projeto|open projeto)\b", 0.7),
                (r"\b(opencode|code assistant)\b", 0.9),
                (r"\b(change|modify|update|fix|refactor|implement|create|write)\s+(.+)", 0.6),
            ],
            "browser": [
                (r"\b(search|pesquis|google|find|look up)\s+(.+)$", 0.9),
                (r"\b(open|abre?)\s+(site|website|url|página)\b", 0.85),
                (r"\b(go to|navega|navigate|visit)\s+(.+)$", 0.75),
                (r"\b(abre?|open)\s+(firefox|chrome|browser|navegador)\b", 0.85),
            ],
            "media_control": [
                (r"\b(volume|som)\s+(aumenta|increase|sobe|raise|diminui|decrease|baixa|lower|reduce|muda|set|define|mute|unmute|silencia)\b", 0.95),
                (r"^(aumenta|increase|sobe|raise|diminui|decrease|baixa|lower|reduce)\s+(o\s+)?(volume|som)", 0.9),
                (r"^(mute|silencia|mutar|mudo|unmute|unmudo|ativar som|som on)", 0.85),
                (r"^(play|pause|tocar|pausar|play pause)\s*$", 0.85),
                (r"^(next|próxim[ao]|skip|pular|previous|anterior|voltar)\s*$", 0.85),
                (r"^(stop|parar)\s*$", 0.85),
                (r"\b(now playing|tocando|current track|what's playing|what.s playing)\b", 0.85),
                (r"\b(playerctl|spotify|music|música|media)\s+(play|pause|next|prev|stop)\b", 0.9),
                (r"^(volume|som)\s*\d+", 0.8),
                (r"\b(play|pause|tocar|pausar)\s+(\w+\s+)?(music|música|media|song|som|audio|player|playback|track|album|playlist|filme|video|episódio)\b", 0.85),
                (r"\b(stop|parar)\s+(\w+\s+)?(music|música|media|playing|player|playback|tocando|song|som|audio|track)\b", 0.85),
            ],
            "automation": [
                (r"\b(docker|container)\b", 0.9),
                (r"^(abre?|open|launch|iniciar)\s+(firefox|chrome|terminal|code|vscode|spotify|slack|discord|telegram|whatsapp|obsidian|notion|gimp|blender|libreoffice|thunderbird|evolution|nautilus|nemo|thunar|pencil|kitty|alacritty|wezterm)\b", 0.9),
                (r"^(open|launch)\s+(.+)$", 0.55),
                (r"\b(terminal|bluetooth|wifi|network|nmcli|bluetoothctl)\b", 0.8),
                (r"\b(shutdown|reboot|power off|desligar|reiniciar)\b", 0.85),
                (r"^(run|execute|start)\s+(.+)$", 0.75),
            ],
            "workflow": [
                (r"^(run|execute|start|ativar|iniciar)\s+(workflow|workflows|fluxo|rotina)\b", 0.9),
                (r"\b(workflow|workflows|fluxo|rotina)\s+(run|execute|start|ativar|iniciar)\b", 0.85),
                (r"^(morning routine|rotina matinal|programming mode|modo programador)\b", 0.85),
            ],
            "memory": [
                (r"^(remember|lembrar|remember that|guarda|memorize)\b", 0.9),
                (r"^(recall|lembra|what do you know|o que sabe)\b", 0.85),
                (r"^(forget|esquece|delete memory|apaga)\b", 0.85),
                (r"\b(main project|projeto principal|my project)\b", 0.7),
                (r"\breload skills\b", 0.9),
                (r"\b(search|recall|find|remember|look up)\s+(my\s+)?(memory|memories|memórias|lembranças)\b", 0.92),
                (r"^(o que (você|tu) (sabe|lembra|guarda))\b", 0.85),
            ],
            "query": [
                (r"\b(what is|who is|tell me about|o que é|quem é|explain|explique|how to|como)\b", 0.6),
                (r"\?$", 0.5),
            ],
        }

    def classify(self, command: str, context: dict | None = None) -> list[tuple[str, float]]:
        cmd_lower = command.lower().strip()
        scores: dict[str, float] = {}

        for intent, patterns in self._intents.items():
            score = 0.0
            for pattern, weight in patterns:
                if re.search(pattern, cmd_lower, re.IGNORECASE):
                    score = max(score, weight)
            if score > 0:
                scores[intent] = score

        if context and not scores:
            last_intent = context.get("last_intent")
            if last_intent and last_intent in self._intents:
                scores[last_intent] = 0.2

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

    def best_intent(self, command: str, context: dict | None = None) -> tuple[str | None, float]:
        ranked = self.classify(command, context)
        if ranked:
            return ranked[0]
        return None, 0.0

    def is_automation(self, intent_name: str | None) -> bool:
        return intent_name in AUTOMATION_CATEGORIES

    def is_conversation(self, intent_name: str | None) -> bool:
        return intent_name in CONVERSATION_CATEGORIES

    def get_routing_decision(self, command: str, context: dict | None = None) -> dict:
        intent, confidence = self.best_intent(command, context)

        decision = {
            "intent": intent,
            "confidence": confidence,
            "action": "ai",
            "reason": "default_ai",
        }

        if intent is None:
            decision["reason"] = "no_intent_detected"
            return decision

        if self.is_conversation(intent):
            if confidence >= 0.4:
                decision["action"] = "ai"
                decision["reason"] = f"conversational_intent_{intent}_{confidence}"
                return decision
            decision["action"] = "ai"
            decision["reason"] = f"low_confidence_conversation_{confidence}"
            return decision

        if self.is_automation(intent):
            if confidence >= CONFIDENCE_HIGH:
                decision["action"] = "execute"
                decision["reason"] = f"high_confidence_automation_{intent}_{confidence}"
            elif confidence >= CONFIDENCE_MEDIUM:
                decision["action"] = "confirm"
                decision["reason"] = f"medium_confidence_automation_{intent}_{confidence}"
            else:
                decision["action"] = "ai"
                decision["reason"] = f"low_confidence_automation_{intent}_{confidence}"
            return decision

        if intent == "query":
            decision["action"] = "ai"
            decision["reason"] = f"query_intent_{confidence}"
            return decision

        if intent == "memory":
            decision["action"] = "ai"
            decision["reason"] = f"memory_intent_{confidence}"
            return decision

        if intent == "workflow":
            decision["action"] = "ai"
            decision["reason"] = f"workflow_intent_{confidence}"
            return decision

        if confidence >= CONFIDENCE_HIGH:
            decision["action"] = "execute"
        elif confidence >= CONFIDENCE_MEDIUM:
            decision["action"] = "confirm"
        else:
            decision["action"] = "ai"

        decision["reason"] = f"fallback_{intent}_{confidence}"
        return decision
