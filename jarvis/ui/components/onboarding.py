from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QFrame, QWizard,
    QWizardPage, QFileDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr


class OnboardingWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("onboarding.welcome_title"))
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
                background-color: rgba(0, 122, 255, 0.08);
                border: 0.5px solid {Theme.ACCENT_PRIMARY}44;
                border-radius: 16px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: 400;
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: rgba(0, 122, 255, 0.15);
            }}
            QLineEdit {{
                background-color: rgba(28, 28, 30, 0.6);
                color: {Theme.TEXT_PRIMARY};
                border: 0.5px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QComboBox {{
                background-color: rgba(28, 28, 30, 0.6);
                color: {Theme.TEXT_PRIMARY};
                border: 0.5px solid {Theme.BORDER};
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
        self._title = None
        self._subtitle = None
        self._feature_labels = []
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self._title = QLabel(t("onboarding.welcome_title"))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(self._title)

        self._subtitle = QLabel(t("onboarding.welcome_subtitle"))
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setStyleSheet(f"font-size: 14px; color: {Theme.ACCENT_PRIMARY}; font-weight: 400; letter-spacing: 2px;")
        layout.addWidget(self._subtitle)

        layout.addSpacing(12)

        features = [
            "onboarding.feature_context",
            "onboarding.feature_voice",
            "onboarding.feature_desktop",
            "onboarding.feature_workflows",
            "onboarding.feature_code",
        ]
        for f_key in features:
            lbl = QLabel(t(f_key))
            lbl.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY}; padding: 2px 0;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._feature_labels.append(lbl)
            layout.addWidget(lbl)


class ConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle(t("onboarding.page_config"))
        self._info = None
        self._name_label = None
        self._lang_label = None
        self._model_label = None
        self.name_input = None
        self.lang_combo = None
        self.model_combo = None
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._info = QLabel(t("onboarding.config_info"))
        self._info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        self._info.setWordWrap(True)
        layout.addWidget(self._info)

        layout.addSpacing(8)

        row1 = QHBoxLayout()
        self._name_label = QLabel(t("onboarding.assistant_name"))
        row1.addWidget(self._name_label)
        self.name_input = QLineEdit("Jarvis")
        row1.addWidget(self.name_input)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self._lang_label = QLabel(t("onboarding.language"))
        row2.addWidget(self._lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["en-US", "pt-PT", "es-ES", "fr-FR", "de-DE"])
        row2.addWidget(self.lang_combo)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self._model_label = QLabel(t("onboarding.ollama_model"))
        row3.addWidget(self._model_label)
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
        self.setTitle(t("onboarding.page_voice"))
        self._info = None
        self.voice_check = None
        self.wake_check = None
        self.tts_check = None
        self.mic_combo = None
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._info = QLabel(t("onboarding.voice_info"))
        self._info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        self._info.setWordWrap(True)
        layout.addWidget(self._info)

        layout.addSpacing(8)

        self.voice_check = QCheckBox(t("onboarding.enable_voice"))
        self.voice_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; spacing: 8px;")
        layout.addWidget(self.voice_check)

        self.wake_check = QCheckBox(t("onboarding.enable_wake_word"))
        self.wake_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; spacing: 8px;")
        layout.addWidget(self.wake_check)

        self.tts_check = QCheckBox(t("onboarding.enable_tts"))
        self.tts_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; spacing: 8px;")
        layout.addWidget(self.tts_check)

        mic_row = QHBoxLayout()
        mic_row.addWidget(QLabel(t("onboarding.microphone")))
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
        self.setTitle(t("onboarding.page_project"))
        self._info = None
        self.path_input = None
        self._browse_btn = None
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._info = QLabel(t("onboarding.project_info"))
        self._info.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px;")
        self._info.setWordWrap(True)
        layout.addWidget(self._info)

        layout.addSpacing(8)

        row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(t("onboarding.project_placeholder"))
        row.addWidget(self.path_input)
        self._browse_btn = QPushButton(t("onboarding.browse"))
        self._browse_btn.clicked.connect(self._browse)
        row.addWidget(self._browse_btn)
        layout.addLayout(row)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, t("onboarding.select_folder"))
        if folder:
            self.path_input.setText(folder)

    def collect_config(self):
        return {"default_project_path": self.path_input.text()}


class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle(t("onboarding.page_ready"))
        self._title = None
        self._subtitle = None
        self._health = None
        self.health_check = None
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self._title = QLabel(t("onboarding.ready_title"))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {Theme.ACCENT_SUCCESS};")
        layout.addWidget(self._title)

        self._subtitle = QLabel(t("onboarding.ready_subtitle"))
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setWordWrap(True)
        self._subtitle.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(self._subtitle)

        self._health = QLabel(t("onboarding.ready_health"))
        self._health.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._health.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(self._health)

        self.health_check = QCheckBox(t("onboarding.run_health"))
        self.health_check.setChecked(True)
        self.health_check.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; spacing: 8px;")
        layout.addWidget(self.health_check)

    def collect_config(self):
        return {"run_health_check": self.health_check.isChecked()}
