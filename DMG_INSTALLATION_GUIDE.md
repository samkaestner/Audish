# macOS DMG Installation Guide

## If You See "Damaged" or "Can't Open" Error

If macOS shows a message that the application is "damaged" or "can't be opened," this is because the app isn't code-signed. This is a security feature in macOS called Gatekeeper.

### Quick Fix (Recommended)

**Option 1: Right-Click to Open**
1. Right-click (or Control-click) on the `.dmg` file
2. Select **"Open"** from the context menu
3. Click **"Open"** in the security dialog
4. The DMG will mount and you can install the app

**Option 2: Remove Quarantine Attribute**
1. Open Terminal
2. Run this command (replace with your actual path):
   ```bash
   xattr -cr ~/Downloads/Audition\ Scheduler.dmg
   ```
3. Then double-click the DMG to open it

**Option 3: System Preferences**
1. Go to **System Preferences** → **Security & Privacy**
2. Click **"Open Anyway"** if you see a message about the app
3. Or temporarily allow apps from "Anywhere" (not recommended for security)

### After Installation

If you see a similar warning when trying to run the app:

1. Right-click the app in Applications folder
2. Select **"Open"**
3. Click **"Open"** in the security dialog
4. The app will be added to your security exceptions and will open normally in the future

### Why This Happens

macOS Gatekeeper blocks unsigned applications by default. To properly sign and notarize the app requires:
- Apple Developer account ($99/year)
- Code signing certificate
- Notarization credentials

For internal/testing use, the workarounds above are safe and commonly used.

### Alternative: Use the ZIP File

If you prefer, you can use the `.zip` file instead of the `.dmg`:
1. Extract the ZIP file
2. Move the app to your Applications folder
3. Use the same right-click method to open it the first time
