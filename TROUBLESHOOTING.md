# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 🚫 Issue: START_SERVERS.bat doesn't work

**Solution 1: Run as Administrator**
- Right-click `START_SERVERS.bat`
- Select "Run as administrator"

**Solution 2: Start Manually**
Open two separate terminals:

**Terminal 1 (Backend):**
```bash
cd c:\Users\hp\ibm\bobbackend
uvicorn main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd C:\Users\hp\frontend
npm run dev
```

---

### 🚫 Issue: Backend shows "ModuleNotFoundError"

**Solution: Install Python dependencies**
```bash
cd c:\Users\hp\ibm\bobbackend
pip install -r requirements.txt
```

---

### 🚫 Issue: Frontend shows "command not found: npm"

**Solution: Install Node.js**
1. Download from: https://nodejs.org/
2. Install LTS version (v18 or higher)
3. Restart terminal
4. Try again

---

### 🚫 Issue: Frontend shows "Cannot find module"

**Solution: Install dependencies**
```bash
cd C:\Users\hp\frontend
npm install
```

---

### 🚫 Issue: Backend shows "Connection refused" or MongoDB error

**Solution: Start MongoDB**

**If using local MongoDB:**
```bash
# Windows - Start MongoDB service
net start MongoDB
```

**If using MongoDB Atlas:**
- Check your `.env` file has correct `MONGODB_URI`
- Verify your IP is whitelisted in Atlas

---

### 🚫 Issue: Port 8000 or 3000 already in use

**Solution: Kill existing processes**

**Windows:**
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

**Or change ports:**

Backend (edit `START_SERVERS.bat`):
```bash
uvicorn main:app --reload --port 8001
```

Frontend (edit `package.json`):
```json
"dev": "next dev -p 3001"
```

---

### 🚫 Issue: Analysis gets stuck at "Analyzing..."

**Possible Causes:**

1. **LLM API Keys not configured**
   - Check `bobbackend/.env` has valid keys:
     - `GEMINI_API_KEY=your_key`
     - `GROQ_API_KEY=your_key`

2. **Repository too large**
   - Try a smaller repository first
   - Example: `https://github.com/vercel/next.js`

3. **Backend error**
   - Check backend terminal for error messages
   - Look for red error text

4. **MongoDB not running**
   - Verify MongoDB is accessible
   - Check connection string in `.env`

---

### 🚫 Issue: Chat doesn't respond

**Solution: Check analysis is complete**
1. Make sure you uploaded a project first
2. Wait for analysis to complete (status: "completed")
3. Check backend terminal for LLM errors
4. Verify API keys are valid

---

### 🚫 Issue: "CORS error" in browser console

**Solution: Backend CORS is already configured**
- This shouldn't happen with the integrated setup
- If it does, check backend is running on port 8000
- Verify frontend `.env.local` has: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

---

### 🚫 Issue: Page shows "No Project Selected"

**Solution: Upload a project first**
1. Go to Upload page
2. Enter a GitHub URL
3. Wait for analysis to complete
4. Then navigate to other pages

---

### 🚫 Issue: "Failed to fetch" errors

**Checklist:**
- [ ] Backend is running (check terminal)
- [ ] Backend shows "Uvicorn running on http://127.0.0.1:8000"
- [ ] Frontend is running (check terminal)
- [ ] No firewall blocking localhost
- [ ] Try opening http://localhost:8000 in browser (should show API status)

---

### 🚫 Issue: Blank page or white screen

**Solution: Check browser console**
1. Press F12 to open DevTools
2. Go to Console tab
3. Look for error messages
4. Common fixes:
   - Clear browser cache (Ctrl + Shift + Delete)
   - Try incognito/private mode
   - Check for JavaScript errors

---

### 🚫 Issue: "Network Error" or "Timeout"

**Solution: Increase timeout**
Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_API_TIMEOUT=60000  # 60 seconds
```

---

## 🔍 Debugging Tips

### Check Backend Status
Open in browser: http://localhost:8000
Should show:
```json
{
  "status": "API RUNNING",
  "message": "AI Project Intelligence Platform"
}
```

### Check Frontend Status
Open in browser: http://localhost:3000
Should show the landing page with SecureAI branding

### View Backend Logs
Look at the backend terminal window for:
- API requests
- Error messages
- LLM responses
- Database operations

### View Frontend Logs
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors or warnings
4. Check Network tab for failed requests

---

## 📞 Still Having Issues?

### Collect Information:
1. **Backend terminal output** (copy error messages)
2. **Frontend terminal output** (copy error messages)
3. **Browser console errors** (F12 → Console tab)
4. **Network tab** (F12 → Network tab, check failed requests)

### Check Configuration:
- `bobbackend/.env` - API keys configured?
- `frontend/.env.local` - API URL correct?
- MongoDB running and accessible?
- Node.js version (run `node --version`)
- Python version (run `python --version`)

---

## ✅ Quick Health Check

Run these commands to verify everything is set up:

```bash
# Check Node.js
node --version
# Should show v18 or higher

# Check Python
python --version
# Should show 3.8 or higher

# Check npm
npm --version
# Should show 8 or higher

# Check backend dependencies
cd c:\Users\hp\ibm\bobbackend
pip list | findstr fastapi
# Should show fastapi installed

# Check frontend dependencies
cd C:\Users\hp\frontend
npm list next
# Should show next.js installed
```

---

## 🎯 Success Indicators

You know everything is working when:
- ✅ Backend terminal shows: "Uvicorn running on http://127.0.0.1:8000"
- ✅ Frontend terminal shows: "Ready in X.Xs"
- ✅ http://localhost:8000 shows API status
- ✅ http://localhost:3000 shows landing page
- ✅ Can upload a GitHub URL
- ✅ Analysis completes successfully
- ✅ Dashboard shows real data
- ✅ Chat responds with AI answers

---

## 📚 Additional Resources

- `README_START_HERE.md` - Quick start guide
- `frontend/INTEGRATION_GUIDE.md` - Technical documentation
- `frontend/INTEGRATION_SUMMARY.md` - Integration details

---

**Remember:** Keep both terminal windows open while using the application!