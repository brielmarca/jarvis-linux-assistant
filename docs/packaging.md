# Packaging

## Desktop Integration

### Manual Install
```bash
bash scripts/install_desktop.sh
```

This script:
1. Copies `.desktop` file to `~/.local/share/applications/jarvis.desktop`
2. Copies icons to `~/.local/share/icons/hicolor/{64,256}x{64,256}/apps/jarvis.png`
3. Creates launcher script at `~/.local/bin/jarvis`
4. Creates config directory at `~/.jarvis/`

### Manual Uninstall
```bash
bash scripts/uninstall_desktop.sh
```

### Desktop File
Located at `packaging/jarvis.desktop`, follows [FreeDesktop.org standards](https://specifications.freedesktop.org/desktop-entry-spec/latest/):
- `Name`: Jarvis Linux Assistant
- `Exec`: Python entry point
- `Icon`: jarvis
- `Categories`: Utility;AI;Assistant;
- `Terminal`: false

## Icons

| Size | File | Use |
|------|------|-----|
| 64×64 | `packaging/icons/jarvis-64.png` | Tray icon, small menu |
| 256×256 | `packaging/icons/jarvis-256.png` | Desktop icon, about dialog |
| SVG | `packaging/icons/jarvis.svg` | Scalable vector source |

## AppImage

### Prerequisites
- [appimagetool](https://github.com/AppImage/AppImageKit/releases) (optional — script will download if needed)

### Build
```bash
bash scripts/build_appimage.sh
```

This creates `Jarvis.AppDir/` with the full AppDir structure and, if appimagetool is available, builds `Jarvis-x86_64.AppImage`.

### AppDir Structure
```
Jarvis.AppDir/
├── AppRun                          # Entry point script
├── jarvis.desktop                  # Desktop file
├── jarvis.png                      # Icon
└── usr/
    ├── bin/
    ├── share/
    │   ├── applications/
    │   │   └── jarvis.desktop
    │   ├── icons/
    │   │   └── hicolor/
    │   │       └── {64,256}x{64,256}/
    │   │           └── apps/
    │   │               └── jarvis.png
    │   └── jarvis/
    │       └── jarvis-linux-assistant/   # Full project copy
    └── ...
```

## User Data

| Path | Purpose |
|------|---------|
| `~/.jarvis/` | Config directory |
| `~/.jarvis/.onboarding_done` | First-run marker |
| `~/.jarvis/workflows/` | Workflow storage |

## Logs

Logs are emitted via `JarvisLogger` and appear in the Logs tab. No persistent log file by default.
