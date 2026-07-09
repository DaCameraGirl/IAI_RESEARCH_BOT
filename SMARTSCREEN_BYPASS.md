# Bypassing Windows SmartScreen for RWS Research Bot

When you double-click `RWS Research Bot.lnk` on your desktop, Windows SmartScreen may show a warning because the .exe is not digitally signed.

## Step-by-Step: Click "Run Anyway"

### What You'll See:
```
┌─────────────────────────────────────────┐
│  Windows protected your PC              │
│                                         │
│  Windows Defender SmartScreen prevented │
│  an unrecognized app from starting.     │
│  Running this app might put your PC     │
│  at risk.                               │
│                                         │
│  App: RWS_Research_Bot.exe              │
│  Publisher: Unknown publisher           │
│                                         │
│  [ More info ]                          │
│                                         │
│  [ Don't run ]                          │
└─────────────────────────────────────────┘
```

### Steps:
1. **Click "More info"** (small link at bottom left)
2. A new button appears: **"Run anyway"**
3. **Click "Run anyway"**
4. ✅ The bot launches!

## Alternative: Run Python Version

If SmartScreen keeps blocking, just run the Python version instead:

```powershell
python scripts/rws_web.py
```

This works exactly the same - opens browser at http://127.0.0.1:7842

## Why This Happens

- The .exe is not digitally signed (costs $300+/year)
- Windows blocks unsigned apps by default
- This is normal for open-source software
- The code is safe - you built it yourself!

## One-Time Fix

After clicking "Run anyway" once, Windows usually remembers and won't block it again.

## Still Having Issues?

Try running from PowerShell:
```powershell
cd "C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\dist"
.\RWS_Research_Bot.exe
```

Or just use the Python version - it's identical functionality!
