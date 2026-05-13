import sys
import argparse
from pathlib import Path

from jarvis.core.logger import JarvisLogger
from jarvis.i18n import t


log = JarvisLogger()


_FIRST_RUN_FLAG = Path.home() / ".jarvis" / ".configured"
_FIRST_RUN_MARKER = Path.home() / ".jarvis" / ".onboarding_done"


def is_first_run() -> bool:
    return not _FIRST_RUN_MARKER.exists()


def mark_onboarding_done():
    _FIRST_RUN_MARKER.parent.mkdir(parents=True, exist_ok=True)
    _FIRST_RUN_MARKER.touch()


def run_cli():
    from jarvis.core.assistant import Assistant
    from jarvis.i18n import tr
    import yaml
    cfg_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    try:
        cfg = yaml.safe_load(cfg_path.read_text()) or {}
    except Exception:
        cfg = {}
    lang_map = {"en-US": "en", "es-ES": "es", "fr-FR": "fr", "de-DE": "de", "pt-PT": "pt_BR"}
    tr.set_language(lang_map.get(cfg.get("language", "en-US"), "en"))

    assistant = Assistant()
    print(f"\n  {assistant.name} " + t("cli.title"))
    print("  " + "=" * 40)
    print("  " + t("cli.help_quit") + "\n")

    while True:
        try:
            cmd = input("  " + t("cli.you") + " ").strip()
            if cmd.lower() in ("quit", "exit", "sair"):
                print(f"  {assistant.name}: " + t("cli.goodbye"))
                break
            if not cmd:
                continue

            result = assistant.process(cmd)

            if result.get("requires_confirmation"):
                confirm = input("  " + t("cli.confirm")).strip().lower()
                if confirm in ("yes", "y", "sim", "s"):
                    result = assistant.process(f"confirmed: {cmd}")
                else:
                    print(f"  {assistant.name}: " + t("cli.cancelled"))
                    continue

            response = result.get("response", t("cli.no_response"))
            skill = result.get("skill")
            elapsed = result.get("execution_time", 0)
            skill_info = f" [{skill}]" if skill else ""
            print(f"  {assistant.name}{skill_info}: {response}")
            if elapsed:
                print(f"  ({elapsed:.2f}s)")

        except KeyboardInterrupt:
            print(f"\n  {assistant.name}: " + t("cli.goodbye"))
            break
        except EOFError:
            print(f"\n  {assistant.name}: " + t("cli.goodbye"))
            break


def run_gui():
    import sys
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    from jarvis.ui.main_window import MainWindow
    from jarvis.ui.components.splash import SplashScreen
    from jarvis.ui.components.onboarding import OnboardingWizard

    app = QApplication(sys.argv)
    app.setApplicationName(t("app.title"))
    from jarvis.i18n import tr
    cfg_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    try:
        _cfg = yaml.safe_load(cfg_path.read_text()) or {}
    except Exception:
        _cfg = {}
    _lang_map = {"en-US": "en", "es-ES": "es", "fr-FR": "fr", "de-DE": "de", "pt-PT": "pt_BR"}
    tr.set_language(_lang_map.get(_cfg.get("language", "en-US"), "en"))

    splash = SplashScreen()
    splash.show()
    splash.set_status("Loading assistant...")
    app.processEvents()

    splash.set_status("Loading UI...")
    window = MainWindow()
    app.processEvents()

    splash.set_status("Ready")

    def finish():
        splash.finish_with(window)
        window.show()
        window.raise_()
        window.activateWindow()

        if is_first_run():
            QTimer.singleShot(300, lambda: _show_onboarding(window))

    QTimer.singleShot(400, finish)
    sys.exit(app.exec())


def _show_onboarding(window):
    from PyQt6.QtWidgets import QMessageBox
    from jarvis.ui.components.onboarding import OnboardingWizard
    wizard = OnboardingWizard(window)
    if wizard.exec() == OnboardingWizard.DialogCode.Accepted:
        config = wizard.get_config()

        from jarvis.ui.main_window import _load_config, _save_config, CONFIG_CACHE
        settings = dict(CONFIG_CACHE)
        settings.update({k: v for k, v in config.items() if v})
        _save_config(settings)
        CONFIG_CACHE.update(settings)
        mark_onboarding_done()

        if config.get("run_health_check"):
            window.tabs.setCurrentIndex(11)
            window.diagnostics_tab._run_health_check()


def main():
    parser = argparse.ArgumentParser(description="Jarvis Linux Assistant")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    parser.add_argument("command", nargs="*", help="Single command to execute")
    args = parser.parse_args()

    if args.command:
        from jarvis.core.assistant import Assistant
        assistant = Assistant()
        cmd = " ".join(args.command)
        result = assistant.process(cmd)
        print(result.get("response", ""))
    elif args.cli:
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
