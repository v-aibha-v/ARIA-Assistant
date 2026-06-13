# ARIA Assistant

A Python-based intelligent voice assistant for Windows that enables hands-free system control, automation, and voice-driven interaction.

---

## ✨ Features

- Voice Interaction using natural language
- Smart system automation
- Control Windows (apps, lock, system actions)
- Hotkey activation (Ctrl + Space)
- Wake word support ("ARIA")
- Runs in background tray mode
- Modern fullscreen UI overlay

---

## ⚙️ Installation

```bash
git clone https://github.com/v-aibha-v/ARIA-Assistant.git
cd ARIA-Assistant
pip install -r requirements.txt
```

### Set API Key

```bash
SARVAM_API_KEY=your_key_here
```

### Run Project

```bash
python main.py
```

---

## 🛠️ Build Executable

```bash
pip install pyinstaller
build.bat
```

Output:

```
dist/ARIASetup.exe
```

---

## 🎯 Commands

- Open apps (VS Code, Chrome, Discord)
- Lock PC
- Set timer
- System time
- Sleep system
