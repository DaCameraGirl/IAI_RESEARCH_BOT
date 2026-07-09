# Manual Windows Defender Fix

Windows Defender is blocking the bot. Follow these steps to allow it:

## Step-by-Step Instructions

1. **Open Windows Security**
   - Press Windows key
   - Type "Windows Security"
   - Click to open

2. **Go to Virus & threat protection**
   - Click "Virus & threat protection" in the left sidebar

3. **Open Protection settings**
   - Click "Manage settings" under "Virus & threat protection settings"

4. **Add Exclusion**
   - Scroll down to "Exclusions"
   - Click "Add or remove exclusions"
   - Click "Yes" if prompted by User Account Control

5. **Add the folder**
   - Click "+ Add an exclusion"
   - Select "Folder"
   - Browse to: `C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\dist`
   - Click "Select Folder"

6. **Also add the scripts folder**
   - Click "+ Add an exclusion" again
   - Select "Folder"
   - Browse to: `C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\scripts`
   - Click "Select Folder"

7. **Done!**
   - Close Windows Security
   - Now try running the bot again

## Quick Test

After adding exclusions, run:
```powershell
python scripts/rws_web.py
```

Browser should open at http://127.0.0.1:7842

## Still Not Working?

Try running PowerShell as Administrator:
1. Right-click PowerShell → Run as Administrator
2. Run:
```powershell
cd "C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT"
python scripts/rws_web.py
```
