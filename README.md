# ARIA Assistant

A Python-based intelligent voice assistant for Windows that enables hands-free system control, automation, and voice-driven interaction.

## Features
- **Voice Interaction**: Natural speech-based command handling  
- **Intelligent Assistant**: Performs system-level tasks efficiently  
- **Windows Automation**: Launch apps, lock PC, and control system functions  
- **Hotkey Activation**: Trigger assistant using Ctrl + Space  
- **Wake Word Support**: Activate using "ARIA" (optional mode)  
- **Modern UI Overlay**: Fullscreen Siri-like interactive interface  
- **Background Mode**: Runs silently in system tray  

## Installation

Option 1: Run from Source (Recommended)

Clone repository:
git clone https://github.com/v-aibha-v/ARIA-Assistant.git && cd ARIA-Assistant

Install dependencies:
pip install -r requirements.txt

Set API key:
SARVAM_API_KEY=your_key_here

Run project:
python main.py

## Building the Installer

1. Install PyInstaller: pip install pyinstaller  
2. Install Inno Setup 6: https://jrsoftware.org/isdl.php  
3. Run build script (Admin): build.bat  

Output:
dist/ARIASetup.exe

## Skills

Wake Word: ARIA  
Hotkey: Ctrl + Space  

Commands:
- Open App (VS Code, Discord, etc.)
- Lock PC
- Set timer X minutes
- What time is it
- Sleep system