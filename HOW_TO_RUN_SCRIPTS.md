# HOW TO RUN POWERSHELL SCRIPTS IN VS CODE

## ✅ FIXED! Your PowerShell is now working

## 🚀 THREE WAYS TO START THE LIVE DATA:

### **Option 1: Automated Start (Recommended)**
```powershell
.\START_LIVE_DATA.ps1
```
- Starts backend and frontend
- Waits for everything to load
- Opens browser automatically
- Shows progress and status

### **Option 2: Simple Start (Faster)**
```powershell
.\START_SIMPLE.ps1
```
- Just starts both servers
- No fancy progress bars
- Opens browser after 65 seconds

### **Option 3: Manual Start (Full Control)**
```powershell
# Terminal 1 - Backend
.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 - Frontend (in a new terminal)
cd frontend
npm run dev

# Then open: http://localhost:3000
```

---

## 🔧 IF YOU GET "EXECUTION POLICY" ERRORS:

Run this command once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try again:
```powershell
.\START_LIVE_DATA.ps1
```

---

## 📝 COMMON ISSUES & FIXES:

### ❌ "File not found"
**Fix:** Make sure you're in the project root folder
```powershell
cd c:\Users\hp\Desktop\EnerSight
.\START_LIVE_DATA.ps1
```

### ❌ "Cannot be loaded because running scripts is disabled"
**Fix:** Change execution policy (run as admin if needed)
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\START_LIVE_DATA.ps1
```

### ❌ Script runs but nothing happens
**Fix:** Check if ports are already in use
```powershell
# Kill any existing processes
Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
Get-Process node | Stop-Process -Force

# Then start again
.\START_LIVE_DATA.ps1
```

---

## 🎯 QUICKEST WAY TO TEST:

Just copy-paste this into your VS Code terminal:
```powershell
.\START_SIMPLE.ps1
```

Wait 60 seconds, then go to: http://localhost:3000

You should see the purple "Real-time Consumption" card with numbers updating every 5 seconds!

---

## 💡 PRO TIP - Use VS Code Terminal:

1. Press **Ctrl + `** (backtick) to open terminal in VS Code
2. Make sure it says "PowerShell" at the top right
3. Run: `.\START_SIMPLE.ps1`
4. Done!

---

## ✅ YOUR SCRIPTS ARE NOW FIXED AND READY TO USE!
