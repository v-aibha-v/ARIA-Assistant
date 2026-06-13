# ARIA Assistant

![GitHub repo size](https://img.shields.io/github/repo-size/v-aibha-v/ARIA-Assistant)
![GitHub last commit](https://img.shields.io/github/last-commit/v-aibha-v/ARIA-Assistant)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 🎤 ARIA Assistant

A Python-based intelligent voice assistant for Windows that enables hands-free system control, automation, and voice-driven interaction.

---

## ✨ Features

- 🎤 Voice Interaction using natural language  
- 🧠 Smart system automation  
- 🪟 Control Windows (apps, lock, system actions)  
- ⌨️ Hotkey activation (Ctrl + Space)  
- 🔊 Wake word support ("ARIA")  
- 🧩 Runs in background tray mode  
- 🎨 Modern fullscreen UI overlay  

---

## 🎬 Demo

![ARIA Demo](assets/demo.gif)

> Replace this with your screen recording GIF for maximum impact

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

### Run
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

---

## 📌 Tech Stack

- Python  
- PyQt  
- SpeechRecognition  
- PyAutoGUI  
- Sounddevice  

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub
