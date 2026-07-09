# Bypassing Windows SmartScreen for RWS Research Bot

When you double-click `RWS Research Bot.lnk` on your desktop, Windows SmartScreen may block it because the .exe is not digitally signed.

## Method 1: Right-Click Properties (Most Reliable)

1. **Right-click** the desktop shortcut "RWS Research Bot.lnk"
2. Select **Properties**
3. Click the **"Open File Location"** button (opens the dist folder)
4. **Right-click** `RWS_Research_Bot.exe`
5. Select **Properties**
6. At the bottom, check the box: **"Unblock"**
7. Click **Apply** → **OK**
8. Now double-click the desktop shortcut - it will work!

## Method 2: Run from PowerShell

```powershell
cd "C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\dist"
.\RWS_Research_Bot.exe
```

## Method 3: Add Windows Defender Exception

1. Open **Windows Security**
2. Go to **Virus & threat protection**
3. Click **Manage settings**
4. Scroll to **Exclusions** → Click **Add or remove exclusions**
5. Click **Add an exclusion** → **Folder**
6. Select: `C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\dist`
7. Click **Select Folder**

## Method 4: Use Python Version (No SmartScreen)

The Python version works identically with no warnings:

```powershell
cd "C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT"
python scripts/rws_web.py
```

Opens browser at http://127.0.0.1:7842 - same interface, same features!

## Why This Happens

- The .exe is not digitally signed (code signing certificates cost $300+/year)
- Windows blocks unsigned apps by default
- This is normal for open-source software
- **The code is safe** - you built it yourself from your own repository!

## Recommended Solution

**Use Method 1 (Unblock in Properties)** - it's permanent and only takes 30 seconds.

After unblocking once, Windows will never block it again.

## Still Having Issues?

Just use the Python version - it's identical functionality without any SmartScreen warnings!