# FraudShield AI - React Frontend

A modern React application for real-time fraud detection dashboard and simulator.

## Features

- **Real-time Dashboard**: Monitor fraud detection statistics and live transactions
- **Transaction Simulator**: Generate synthetic transactions across different attack modes
- **Interactive UI**: Beautiful dark-themed interface with smooth animations
- **API Integration**: Connected to FraudShield AI backend API
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Prerequisites

- Node.js 16+ and npm
- Backend API running at: `https://fraudshield-ai-production-78c0.up.railway.app`

## Installation

1. **Install dependencies**:
   ```bash
   cd frontend-react
   npm install
   ```

2. **Create environment file** (`.env`):
   ```
   VITE_API_URL=https://fraudshield-ai-production-78c0.up.railway.app
   ```

## Development

Run the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Building

Build for production:

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## Deployment to Vercel

### Method 1: Using Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Deploy**:
   ```bash
   cd frontend-react
   vercel
   ```

3. **Configure environment variables** in Vercel dashboard:
   - Set `VITE_API_URL` to your production backend URL

### Method 2: GitHub Integration (Recommended)

1. **Push to GitHub**:
   ```bash
   cd frontend-react
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Connect to Vercel**:
   - Visit https://vercel.com/dashboard
   - Click "Add New..." → "Project"
   - Import the GitHub repository
   - Select the `frontend-react` folder as the root directory
   - Set environment variables:
     - `VITE_API_URL`: `https://fraudshield-ai-production-78c0.up.railway.app`

3. **Deploy**:
   - Vercel will automatically deploy on every push to the main branch

### Vercel Dashboard Configuration

In the Vercel project settings:

**Build & Development Settings**:
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

**Environment Variables**:
- Key: `VITE_API_URL`
- Value: `https://fraudshield-ai-production-78c0.up.railway.app`

## Project Structure

```
frontend-react/
├── src/
│   ├── components/          # Reusable UI components
│   ├── pages/               # Page components (Home, Dashboard, Simulator)
│   ├── hooks/               # Custom React hooks
│   ├── utils/               # Utility functions and API client
│   ├── styles/              # CSS files
│   ├── App.jsx              # Main app component
│   └── main.jsx             # Entry point
├── public/                  # Static assets
├── package.json             # Dependencies
├── vite.config.js           # Vite configuration
├── vercel.json              # Vercel deployment config
├── index.html               # HTML template
├── .env                     # Environment variables
└── README.md                # This file
```

## Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build locally

## Environment Variables

### Development (.env)
```
VITE_API_URL=https://fraudshield-ai-production-78c0.up.railway.app
```

### Production (Vercel Dashboard)
Set via Vercel dashboard under Project Settings → Environment Variables

## Pages

### Home Page
Landing page with system information, feature highlights, and links to other sections.

### Dashboard
Real-time statistics including:
- Transaction counts
- Fraud rate percentage
- Blocked/Approved transactions
- Latency metrics
- Live transaction feed
- System health status
- Fraud alerts

### Simulator
Interactive transaction simulator with:
- Multiple attack modes (normal, stolen_card, geo_attack, velocity_burst)
- Configurable transaction count
- Real-time result streaming
- Fraud score visualization
- LLM reasoning display

## API Endpoints Used

- `GET /health` - System health check
- `GET /dashboard/stats` - Dashboard statistics
- `GET /dashboard/feed` - Live transaction feed
- `GET /dashboard/alerts` - Fraud alerts
- `POST /dashboard/reset` - Reset dashboard
- `POST /simulate` - Start simulation
- `GET /simulate/stream` - Stream simulation results (Server-Sent Events)

## Troubleshooting

### API Connection Issues
- Verify backend URL in `.env` is correct
- Check CORS settings on backend API
- Ensure backend server is running

### Build Errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf dist`

### Vercel Deployment Issues
- Check build logs in Vercel dashboard
- Verify environment variables are set
- Ensure root directory is set to `frontend-react` folder

## Technologies Used

- **React 18**: UI library
- **Vite**: Build tool
- **React Router**: Navigation
- **Axios**: HTTP client
- **CSS3**: Styling with CSS variables

## License

Same as parent FraudShield AI project

## Support

For issues or questions, refer to the main FraudShield AI repository documentation.
