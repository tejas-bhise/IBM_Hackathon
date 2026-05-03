# 🚀 Quick Start Guide - Backend + Frontend Integration

## ⚡ Easiest Way to Start (One Click!)

**Double-click this file:**
```
START_SERVERS.bat
```

This will automatically:
1. ✅ Start the Backend Server (port 8000)
2. ✅ Start the Frontend Server (port 3000)
3. ✅ Open two terminal windows

**Then open your browser and go to:**
```
http://localhost:3000
```

---

## 📁 Project Structure

```
c:/Users/hp/ibm/
├── bobbackend/          ← Backend (FastAPI + Python)
├── frontend/            ← Frontend (Next.js + TypeScript) - Located at C:/Users/hp/frontend
├── START_SERVERS.bat    ← Double-click this to start both servers!
└── README_START_HERE.md ← You are here
```

**Note:** The frontend is located at `C:/Users/hp/frontend` (separate location)

---

## 🎯 What You'll See

1. **Two terminal windows will open:**
   - Window 1: Backend Server (FastAPI)
   - Window 2: Frontend Server (Next.js)

2. **Wait for both to show "Ready":**
   - Backend: `Uvicorn running on http://127.0.0.1:8000`
   - Frontend: `Ready in X.Xs`

3. **Open browser:**
   - Go to: `http://localhost:3000`
   - You'll see the SecureAI landing page

---

## 🧪 Test the Integration

### 1. Upload a Repository
- Click "Dashboard" or "Get Started"
- Enter a GitHub URL: `https://github.com/vercel/next.js`
- Click "Connect"
- Wait 30-60 seconds for analysis

### 2. View Results
- **Dashboard:** Real security score and findings
- **Chat:** AI-powered responses with sources
- **Memory:** Project timeline from Git history
- **Auditor:** Detailed security findings

---

## 🛑 How to Stop

**Close both terminal windows** or press `Ctrl + C` in each window.

---

## 🔧 Manual Start (Alternative Method)

If the batch file doesn't work, start manually:

### Terminal 1 - Backend:
```bash
cd c:\Users\hp\ibm\bobbackend
uvicorn main:app --reload --port 8000
```

### Terminal 2 - Frontend:
```bash
cd C:\Users\hp\frontend
npm run dev
```

---

## ❓ Troubleshooting

### Backend won't start?
- Check MongoDB is running
- Verify `.env` file in `bobbackend/` has API keys

### Frontend won't start?
- Run `npm install` first in the frontend directory
- Check Node.js is installed (v18+)

### Can't see the website?
- Make sure both servers show "Ready"
- Try refreshing the browser
- Check http://localhost:8000 shows API status

### Analysis stuck?
- Check backend terminal for errors
- Verify LLM API keys are configured
- Try a smaller repository first

---

## 📊 What's Integrated

✅ **Upload:** GitHub URL & ZIP file upload  
✅ **Analysis:** Real-time security scanning  
✅ **Dashboard:** Live security scores and findings  
✅ **Chat:** AI-powered Q&A with project context  
✅ **Memory:** Git history timeline  
✅ **Auditor:** Detailed security reports  

All features are connected to the real backend API!

---

## 📚 More Documentation

- `frontend/INTEGRATION_GUIDE.md` - Complete technical guide
- `frontend/INTEGRATION_SUMMARY.md` - Integration details

---

## 🎉 Success!

If you see the landing page at http://localhost:3000, you're all set!

**Your integrated application is running!** 🚀

---

**Quick Reference:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Start: Double-click `START_SERVERS.bat`
- Stop: Close terminal windows