# ⚡ Tweakify — Windows Performance Suite

<div align="center">

![Version](https://img.shields.io/badge/Tweakify-v2.0%20PRO-00d4ff?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-00ff88?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078d4?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/Python-3.10+-ffd43b?style=for-the-badge&logo=python&logoColor=white)
![Stars](https://img.shields.io/github/stars/abdllaouidjabere-cmyk/Tweakify?style=for-the-badge&color=ff8c00)

**A free, open-source, professional-grade Windows optimization suite.**  
Boost performance · Reclaim RAM · Kill telemetry · Tune your network  
All from one sleek, dark-themed dashboard.

[⬇️ Download Latest](https://github.com/abdllaouidjabere-cmyk/Tweakify/releases/latest) &nbsp;·&nbsp; [🌐 Website](https://abdllaouidjabere-cmyk.github.io/Tweakify) &nbsp;·&nbsp; [🐛 Report Bug](https://github.com/abdllaouidjabere-cmyk/Tweakify/issues/new) &nbsp;·&nbsp; [💡 Request Feature](https://github.com/abdllaouidjabere-cmyk/Tweakify/issues/new)

</div>

---

## 📸 Preview

> A sleek dark-themed dashboard with real-time hardware monitoring, one-click tweaks, and a live console log.

---

## 🧠 What is Tweakify?

Tweakify is a **professional Windows performance optimization tool** built entirely in Python using CustomTkinter. It was designed to give power users and enthusiasts full control over their Windows system — without needing to dig through the registry manually or run sketchy batch scripts.

Whether you're a **gamer** looking to cut latency, a **developer** who needs a clean and fast environment, or just someone tired of Windows slowing down over time — Tweakify gives you surgical-level control with a beautiful, modern interface.

Everything Tweakify does is **transparent, reversible, and safe**. Before applying any tweak, the tool takes a full system snapshot. You can restore your exact original settings at any time with a single click.

---

## ✨ Features

### 🏎️ Performance Optimization
- Disable Windows visual animations and transparency effects
- Apply the **High Performance** power plan automatically
- Disable unnecessary startup services draining CPU and RAM
- Kill background Xbox Game Bar and resource-heavy processes

### 🧹 Deep System Cleanup
- Remove temp files, browser cache, and Windows Update leftovers
- Clear prefetch, superfetch, and event logs
- Wipe diagnostic data and reclaim gigabytes of disk space in seconds

### 🛡️ Privacy & Telemetry Control
- Disable **DiagTrack** (Connected User Experiences and Telemetry)
- Block Microsoft data collection and activity history
- Disable advertising ID, location tracking, and Cortana
- Stop Windows Search indexing for extra performance

### 🌐 Network Optimization
- Tune **TCP/IP stack** for lower latency
- Adjust `TcpAckFrequency` for gaming and real-time apps
- Disable network throttling for maximum bandwidth

### 📸 Snapshot & Restore System
- Saves your **exact system state** before any change
- Captures registry values, service states, and power settings
- Full one-click restore — zero guesswork, zero risk

### 📊 Live Hardware Monitor
- Real-time **CPU**, **RAM**, and **disk** activity
- System info: OS version, architecture, uptime
- Live console log for every action with timestamps

---

## 🛠️ How It Works

Tweakify interacts with three core Windows subsystems:

| Layer | Method | Examples |
|---|---|---|
| **Registry** | `winreg` Python API | Visual effects, telemetry flags, game mode |
| **Services** | `sc` / `subprocess` | SysMain, DiagTrack, WSearch, XblAuthManager |
| **System Commands** | `subprocess` / `powercfg` | Power plans, disk cleanup, network reset |

All operations are logged in real time. The snapshot system records every registry key and service **before** modification, so a complete restore is always available.

---

## 📦 Download

| File | Description |
|---|---|
| `Tweakify_Setup_v2.0.exe` | Windows Installer (recommended) |
| `Tweakify.exe` | Standalone portable executable |

> ⚠️ **Administrator privileges are required.** Tweakify automatically prompts for UAC elevation on launch.

---

## 🖥️ Requirements

- Windows 10 or Windows 11 (64-bit)
- Administrator account
- **No Python installation required** — runs as a standalone `.exe`

---

## 🔨 Build From Source

```bash
# 1. Clone the repository
git clone https://github.com/abdllaouidjabere-cmyk/Tweakify.git
cd Tweakify

# 2. Install dependencies
pip install customtkinter psutil pyinstaller

# 3. Run directly
python main.py

# 4. Build standalone executable
pyinstaller --noconfirm --onefile --windowed --name "Tweakify" --icon "icon.ico" --collect-all customtkinter main.py
```

The compiled `.exe` will be in the `dist/` folder.

---

## 📁 Project Structure

```
Tweakify/
├── main.py              # Main application source
├── icon.ico             # Application icon
├── setup.iss            # Inno Setup installer script
├── README.md            # This file
├── website/             # Landing page (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── script.js

```

---

## 🤝 Contributing

Contributions are welcome and appreciated!

1. **Fork** the repository
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes and test on Windows 10 and 11
4. Commit: `git commit -m "Add: your feature description"`
5. Push: `git push origin feature/your-feature-name`
6. Open a **Pull Request**

**Guidelines for new tweaks:**
- Must be reversible (add to snapshot system)
- Must be logged in the console
- Must be tested on both Windows 10 and 11

---

## ⚖️ License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software for any purpose — commercial or personal — as long as the original license is included.

---

## ⚠️ Disclaimer

Tweakify modifies Windows system settings, registry values, and service configurations. While the snapshot and restore system is designed to keep things safe, **always back up your important data** before running any system optimization tool. The author is not responsible for any unintended system behavior resulting from the use of this software.

---

<div align="center">

Made with ⚡ by **Jaber** &nbsp;·&nbsp; MIT License &nbsp;·&nbsp; Free Forever

</div>
