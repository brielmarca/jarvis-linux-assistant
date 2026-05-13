from enum import Enum, auto


class EventType(Enum):
    COMMAND_RECEIVED = auto()
    COMMAND_PROCESSING = auto()
    COMMAND_COMPLETED = auto()
    COMMAND_FAILED = auto()
    SKILL_LOADED = auto()
    SKILL_UNLOADED = auto()
    SKILL_EXECUTED = auto()
    WAKE_WORD_DETECTED = auto()
    LISTENING_STARTED = auto()
    LISTENING_STOPPED = auto()
    TRANSCRIPTION_READY = auto()
    RESPONSE_READY = auto()
    TTS_STARTED = auto()
    TTS_COMPLETED = auto()
    AI_THINKING_STARTED = auto()
    AI_THINKING_COMPLETED = auto()
    MICROPHONE_STATE_CHANGED = auto()
    ASSISTANT_STATE_CHANGED = auto()
    SETTINGS_CHANGED = auto()
    ERROR = auto()
    MEMORY_STORED = auto()
    MEMORY_RECALLED = auto()
    MEMORY_PINNED = auto()
    CONTEXT_BUILT = auto()
    INTERRUPTION_DETECTED = auto()
    WORKFLOW_STARTED = auto()
    WORKFLOW_STEP_COMPLETED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_FAILED = auto()
    DESKTOP_STATE_CHANGED = auto()
    METRICS_UPDATED = auto()


class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
        return cls._instance

    def on(self, event_type, handler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type, handler):
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    def emit(self, event_type, data=None):
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception:
                pass
