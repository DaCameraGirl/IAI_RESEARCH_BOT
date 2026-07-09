#!/usr/bin/env python3
"""Build RWS Research Bot as a standalone Windows .exe"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

def main():
    print("🧞 Building RWS Research Bot .exe...\n")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed\n")
    
    # Build command
    cmd = [
        "pyinstaller",
        "--name=RWS_Research_Bot",
        "--onefile",
        "--windowed",
        "--icon=assets/genie-mascot.ico",
        "--add-data=assets;assets",
        "--add-data=templates;templates",
        "--add-data=config;config",
        "--hidden-import=urllib.request",
        "--hidden-import=http.server",
        "--hidden-import=webbrowser",
        "--hidden-import=queue",
        "--hidden-import=threading",
        "--collect-all=ai_engine",
        "--collect-all=scripts",
        "scripts/rws_web.py"
    ]
    
    print("Running PyInstaller...")
    print(" ".join(cmd))
    print()
    
    try:
        subprocess.check_call(cmd, cwd=REPO)
        print("\n✅ Build complete!")
        print(f"\n📦 Executable location: {REPO / 'dist' / 'RWS_Research_Bot.exe'}")
        print("\n🚀 To run: Double-click RWS_Research_Bot.exe in the 'dist' folder")
        print("   The bot will open in your browser automatically.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
