import sys
import argparse
from pathlib import Path

from jarvis.core.logger import JarvisLogger


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

    assistant = Assistant()
    print(f"\n  {assistant.name} Linux Assistant")
    print("  " + "=" * 40)
    print("  Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            cmd = input("  You: ").strip()
            if cmd.lower() in ("quit", "exit", "sair"):
                print(f"  {assistant.name}: Goodbye!")
                break
            if not cmd:
                continue

            result = assistant.process(cmd)

            if result.get("requires_confirmation"):
                confirm = input("  Confirm? (yes/no): ").strip().lower()
                if confirm in ("yes", "y", "sim", "s"):
                    result = assistant.process(f"confirmed: {cmd}")
                else:
                    print(f"  {assistant.name}: Command cancelled.")
                    continue

            response = result.get("response", "No response")
            skill = result.get("skill")
            elapsed = result.get("execution_time", 0)
            skill_info = f" [{skill}]" if skill else ""
            print(f"  {assistant.name}{skill_info}: {response}")
            if elapsed:
                print(f"  ({elapsed:.2f}s)")

        except KeyboardInterrupt:
            print(f"\n  {assistant.name}: Goodbye!")
            break
        except EOFError:
            print(f"\n  {assistant.name}: Goodbye!")
            break


def run_gui():
    import sys
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    from jarvis.ui.main_window import MainWindow
    from jarvis.ui.components.splash import SplashScreen
    from jarvis.ui.components.onboarding import OnboardingWizard

    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis Linux Assistant")

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
