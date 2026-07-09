# Bypassing Windows SmartScreen for RWS Research Bot

When you double-click `RWS Research Bot.lnk` on your desktop, Windows SmartScreen may block it because the .exe is not digitally signed.

## ✅ EASIEST METHOD: Use Python Version (Recommended)

**No SmartScreen warning, works immediately:**

```powershell
cd "C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT"
python scripts/rws_web.py
```

Opens browser at http://127.0.0.1:7842 - identical interface and features!

## Method 2: Add Windows Defender Exception

1. Open **Windows Security** (search in Start menu)
2. Go to **Virus & threat protection**
3. Click **Manage settings**
4. Scroll to **Exclusions** → Click **Add or remove exclusions**
5. Click **Add an exclusion** → **Folder**
6. Browse to: `C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\dist`
7. Click **Select Folder**
8. ✅ Now the .exe will run without warnings!

## Method 3: Run from PowerShell (Bypasses SmartScreen)

```powershell
cd "C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\dist"
Start-Process .\RWS_Research_Bot.exe
```

## Method 4: Disable SmartScreen Temporarily (Not Recommended)

**Only if you trust the file completely:**

1. Open **Windows Security**
2. Go to **App & browser control**
3. Click **Reputation-based protection settings**
4. Turn OFF **Check apps and files**
5. Run the .exe
6. Turn it back ON afterwards

## Why This Happens

- The .exe is not digitally signed (code signing certificates cost $300+/year)
- Windows blocks unsigned apps by default
- This is normal for open-source software
- **The code is safe** - you built it yourself from your own repository!
- Files created locally (not downloaded) don't have an "Unblock" checkbox

## Best Solution

**Just use the Python version** - it's the same bot, same features, no warnings:

```powershell
python scripts/rws_web.py
```

You can even create a `.bat` file on your desktop:
```batch
@echo off
cd "C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT"
python scripts/rws_web.py
```

Save as `Launch_RWS_Bot.bat` on your desktop and double-click it!
