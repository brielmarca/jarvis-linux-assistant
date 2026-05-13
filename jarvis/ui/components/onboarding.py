from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QFrame, QWizard,
    QWizardPage, QFileDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from jarvis.ui.theme import Theme


class OnboardingWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Jarvis")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(520, 440)
        self.setStyleSheet(f"""
            QWizard {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
            }}
            QWizardPage {{
                background-color: {Theme.BG_PRIMARY};
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                background: transparent;
            }}
            QPushButton {{
                background-color: rgba(124, 106, 255, 0.1);
                border: 1px solid {Theme.ACCENT_PRIMARY}44;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 500;
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: rgba(124, 106, 255, 0.2);
            }}
            QLineEdit {{
                background-color: rgba(12, 12, 22, 0.6);
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QComboBox {{
                background-color: rgba(12, 12, 22, 0.6);
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
        """)

        self.setPage(0, WelcomePage())
        self.setPage(1, ConfigPage())
        self.setPage(2, VoicePage())
        self.setPage(3, ProjectPage())
        self.setPage(4, FinishPage())

        self.setStartId(0)
        self.button(QWizard.WizardButton.FinishButton).clicked.connect(self._on_finish)

    def _on_finish(self):
        config = {}
        for page_id in range(self.pageIds()):
            page = self.page(page_id)
            if hasattr(page, 'collect_config'):
                config.update(page.collect_config())
        self._config = config
        self.accept()

    def get_config(self) -> dict:
        return getattr(self, '_config', {})


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        title = QLabel("Welcome to Jarvis")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {Theme.TEXT_PRIMARY}; letter-spacing: -0.5px;")
        layout.addWidget(title)

        subtitle = QLabel("Your AI-powered Linux Desktop Assistant")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 14px; color: {Theme.ACCENT_PRIMARY}; font-weight: 500; letter-spacing: 2px;")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        features = [
            "◉  Contextual AI with semantic memory",
            "◉  Voice control with wake word",
            "◉  Desktop awareness & automation",
            "◉  Workflow orchestration",
            "◉  Code & terminal integration",
        ]
        for f in features:
            lbl = QLabel(f)
            lbl.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY}; padding: 2px 0;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)


class ConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Basic Configuration")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel("Choose your assistant name, language, and AI model.")
        info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addSpacing(8)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Assistant Name:"))
        self.name_input = QLineEdit("Jarvis")
        row1.addWidget(self.name_input)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["en-US", "pt-PT", "es-ES", "fr-FR", "de-DE"])
        row2.addWidget(self.lang_combo)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Ollama Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3:latest", "llama3.1:8b", "mistral", "phi3:mini", "llama3.2:3b"])
        self.model_combo.setCurrentText("llama3:latest")
        row3.addWidget(self.model_combo)
        layout.addLayout(row3)

        self.registerField("assistant_name*", self.name_input)

    def collect_config(self):
        return {
            "assistant_name": self.name_input.text(),
            "language": self.lang_combo.currentText(),
            "ollama_model": self.model_combo.currentText(),
        }


class VoicePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Voice Settings")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel("Configure voice features. You can change these later in Settings.")
        info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addSpacing(8)

        self.voice_check = QCheckBox("Enable Voice Assistant")
        self.voice_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; spacing: 8px;")
        layout.addWidget(self.voice_check)

        self.wake_check = QCheckBox("Enable Wake Word ('Jarvis')")
        self.wake_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; spacing: 8px;")
        layout.addWidget(self.wake_check)

        self.tts_check = QCheckBox("Enable Text-to-Speech")
        self.tts_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; spacing: 8px;")
        layout.addWidget(self.tts_check)

        mic_row = QHBoxLayout()
        mic_row.addWidget(QLabel("Microphone:"))
        self.mic_combo = QComboBox()
        self.mic_combo.addItems(["default", "sysdefault", "hw:0,0", "hw:1,0"])
        mic_row.addWidget(self.mic_combo)
        layout.addLayout(mic_row)

    def collect_config(self):
        return {
            "enable_voice": self.voice_check.isChecked(),
            "enable_wake_word": self.wake_check.isChecked(),
            "enable_tts": self.tts_check.isChecked(),
            "whisper_device": self.mic_combo.currentText(),
        }


class ProjectPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Project Folder")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel("Choose a default folder for your projects. Jarvis will use this context when helping with code.")
        info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addSpacing(8)

        row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select default project folder...")
        row.addWidget(self.path_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse)
        row.addWidget(browse_btn)
        layout.addLayout(row)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.path_input.setText(folder)

    def collect_config(self):
        return {"default_project_path": self.path_input.text()}


class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Ready")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        title = QLabel("You're all set!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {Theme.ACCENT_SUCCESS};")
        layout.addWidget(title)

        subtitle = QLabel("Jarvis is ready to help you manage your Linux desktop.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(subtitle)

        health = QLabel("Run a health check to ensure everything is working.")
        health.setAlignment(Qt.AlignmentFlag.AlignCenter)
        health.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(health)

        self.health_check = QCheckBox("Run health check on finish")
        self.health_check.setChecked(True)
        self.health_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; spacing: 8px;")
        layout.addWidget(self.health_check)

    def collect_config(self):
        return {"run_health_check": self.health_check.isChecked()}
