# Building RWS Research Bot as a Desktop App

This guide shows you how to create a standalone Windows `.exe` file that runs the bot without needing to open a terminal.

## Quick Build

1. **Run the build script:**
   ```powershell
   python build_exe.py
   ```

2. **Wait for it to finish** (takes 1-2 minutes)

3. **Find your .exe:**
   - Location: `dist\RWS_Research_Bot.exe`
   - Double-click to run!

## What Gets Built

- **Single .exe file** - No Python installation needed
- **Includes everything** - All scripts, templates, assets bundled
- **Auto-opens browser** - Launches at http://127.0.0.1:7842
- **Uses your study folders** - Reads/writes to the same folders

## First-Time Setup

If you don't have PyInstaller installed, the build script will install it automatically.

Or install manually:
```powershell
pip install pyinstaller
```

## Distribution

**To share with others:**

1. Copy the entire `RWS_RESEARCH_BOT` folder to their computer
2. They only need to run `dist\RWS_Research_Bot.exe`
3. No Python installation required on their machine!

**Important:** The .exe needs to stay in the same folder structure because it reads study folders, templates, etc.

## Troubleshooting

### Build fails with "module not found"
```powershell
pip install -r requirements.txt
pip install pyinstaller
python build_exe.py
```

### .exe won't start
- Check Windows Defender didn't block it
- Right-click → Properties → Unblock
- Run as Administrator if needed

### Browser doesn't open automatically
- Manually open: http://127.0.0.1:7842
- Check if port 7842 is already in use

## Advanced: Custom Icon

The .exe uses `assets/genie-mascot.ico` as its icon. To change it:

1. Replace `assets/genie-mascot.ico` with your icon
2. Rebuild: `python build_exe.py`

## File Size

The .exe will be ~15-25 MB because it includes:
- Python interpreter
- All required libraries
- Your bot code
- Assets and templates

This is normal for PyInstaller builds!
