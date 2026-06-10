# FraudShield AI - Frontend Deployment Guide

## Summary

Your FraudShield AI frontend has been successfully converted to a modern React application with the backend URL configured. You now have two versions of the frontend:

### Version 1: HTML Static Files (Quick Deployment)
- **Location**: `frontend/` directory
- **Updated API URLs**: All HTML files now point to production backend
- **Deploy To**: 
  - GitHub Pages (static hosting)
  - Vercel (static files)
  - Netlify
  - Any static hosting service

**Files Updated**:
- `frontend/dashboard.html` - API endpoint updated
- `frontend/simulator.html` - API endpoint updated
- `frontend/index.html` - Ready to deploy

---

### Version 2: React Application (Recommended for Production)
- **Location**: `frontend-react/` directory
- **Framework**: React 18 + Vite
- **Environment Configured**: Backend URL set in `.env`
- **Deploy To**: **Vercel** (recommended), Netlify, or other platforms

---

## Quick Deploy to Vercel

### Option A: Deploy via Vercel CLI (Fastest)

```bash
# 1. Install Vercel CLI globally
npm install -g vercel

# 2. Navigate to React frontend
cd frontend-react

# 3. Deploy
vercel

# 4. Follow prompts and confirm

# 5. Set environment variable when asked:
# VITE_API_URL = https://fraudshield-ai-production-78c0.up.railway.app
```

Your site will be live in seconds! ✅

---

### Option B: Deploy via GitHub (Continuous Deployment)

#### Step 1: Push to GitHub
```bash
cd frontend-react

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial React frontend commit"
git remote add origin https://github.com/YOUR_USERNAME/fraudshield-frontend.git
git branch -M main
git push -u origin main
```

#### Step 2: Connect to Vercel
1. Go to https://vercel.com
2. Click "Add New..." → "Project"
3. Select "Import Git Repository"
4. Paste your GitHub repo URL
5. Click "Import"

#### Step 3: Configure Project Settings
1. **Framework**: Select "Vite" (Vercel should auto-detect)
2. **Root Directory**: Make sure it's set to `./frontend-react`
3. **Build Command**: `npm run build` (should be default)
4. **Output Directory**: `dist` (should be default)

#### Step 4: Add Environment Variables
1. In Vercel Dashboard → Project Settings → Environment Variables
2. Add:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://fraudshield-ai-production-78c0.up.railway.app`
3. Click "Save"

#### Step 5: Deploy
Click "Deploy" and wait for build to complete. Your React app will be live!

---

## Deployment URLs

After deployment, you'll get:
- **Vercel URL**: `https://your-project-name.vercel.app`
- **Custom Domain**: Set up in Vercel dashboard (optional)

Example: `https://fraudshield-frontend.vercel.app`

---

## Testing Deployment

Once deployed:

1. **Test Home Page**: 
   - Should see landing page with system info

2. **Test Dashboard**: 
   - Should display real-time fraud statistics
   - API status should show ONLINE (green dot)

3. **Test Simulator**:
   - Select attack mode
   - Click "Run Simulation"
   - Should see live transaction results with fraud scores

---

## What's Configured

### Backend URL
- **Production**: `https://fraudshield-ai-production-78c0.up.railway.app`
- **Environment Variable**: `VITE_API_URL`
- **Location**: `.env` file (can be overridden in Vercel dashboard)

### API Endpoints Connected
```
✓ GET  /health               → System health check
✓ GET  /dashboard/stats      → Real-time statistics
✓ GET  /dashboard/feed       → Live transactions
✓ GET  /dashboard/alerts     → Fraud alerts
✓ POST /dashboard/reset      → Reset simulator
✓ POST /simulate             → Start simulation
✓ GET  /simulate/stream      → SSE for results
```

---

## Project Structure

```
frontend-react/
├── src/
│   ├── pages/
│   │   ├── HomePage.jsx          → Landing page
│   │   ├── DashboardPage.jsx      → Real-time dashboard
│   │   └── SimulatorPage.jsx      → Transaction simulator
│   ├── utils/
│   │   └── api.js                 → API client configuration
│   ├── styles/
│   │   ├── global.css
│   │   ├── HomePage.css
│   │   ├── DashboardPage.css
│   │   └── SimulatorPage.css
│   ├── App.jsx                    → Main component with routing
│   └── main.jsx                   → React entry point
├── index.html
├── vite.config.js
├── vercel.json                    → Vercel deployment config
├── package.json                   → Dependencies
├── .env                           → Environment variables
└── README.md                      → Documentation
```

---

## Development Commands

```bash
# Install dependencies
npm install

# Start development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Environment Variable Management

### Development (.env file)
```
VITE_API_URL=https://fraudshield-ai-production-78c0.up.railway.app
```

### Production (Vercel Dashboard)
- Set via Project Settings → Environment Variables
- Can be different from development
- Automatically injected into build

---

## Troubleshooting

### API Connection Failing
- Verify backend URL is correct and server is running
- Check CORS headers on backend
- Test endpoint directly: `https://fraudshield-ai-production-78c0.up.railway.app/health`

### Build Fails on Vercel
- Check Vercel build logs
- Ensure `VITE_API_URL` is set in environment variables
- Try clearing cache: In Vercel dashboard → Settings → Clear Build Cache

### Dashboard Shows "API OFFLINE"
- Check if backend server is running
- Verify `VITE_API_URL` in environment variables
- Test backend health: `curl https://fraudshield-ai-production-78c0.up.railway.app/health`

### Simulator Not Streaming Results
- Check browser console for errors
- Verify backend `/simulate/stream` endpoint
- Check that EventSource is working (CORS must allow)

---

## Next Steps

1. ✅ **Choose Deployment Method**
   - Quick: Use Vercel CLI (Option A)
   - Continuous: Use GitHub Integration (Option B)

2. **Deploy React Frontend**
   - Follow Option A or B above

3. **Test All Features**
   - Home page loads
   - Dashboard shows live data
   - Simulator generates transactions

4. **Set Custom Domain** (Optional)
   - In Vercel dashboard → Domains
   - Point your domain to Vercel

5. **Monitor Performance**
   - Use Vercel Analytics
   - Monitor API response times

---

## Static HTML Deployment (Alternative)

If you prefer to use the static HTML files:

1. All three HTML files have been updated with production API URL
2. Deploy the `frontend/` directory to:
   - GitHub Pages
   - Vercel (drag & drop)
   - Netlify
   - AWS S3 + CloudFront

Commands for GitHub Pages:
```bash
cd frontend
git add .
git commit -m "Update API endpoints"
git push
```

---

## Support & Documentation

- **React Frontend README**: `frontend-react/README.md`
- **Vercel Documentation**: https://vercel.com/docs
- **Vite Documentation**: https://vitejs.dev
- **React Router**: https://reactrouter.com

---

## Key Benefits of React Version

✅ Component-based architecture  
✅ Automatic updates and hot reload  
✅ Better performance optimization  
✅ Easy to extend and maintain  
✅ Built-in environment variable management  
✅ Optimized production builds  
✅ Better SEO potential  
✅ Easier testing and debugging  

---

**You're all set! Your FraudShield AI frontend is ready to deploy! 🚀**
