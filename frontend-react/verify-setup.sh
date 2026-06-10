#!/bin/bash

# FraudShield AI Frontend Setup Verification Script (Bash version)
# Run: chmod +x verify-setup.sh && ./verify-setup.sh

echo ""
echo "🔧 FraudShield AI Frontend Setup Verification"
echo ""
echo "============================================================"

# Check Node version
echo "✓ Node.js version: $(node --version)"

# Check if package.json exists
if [ -f "package.json" ]; then
    echo "✓ In correct directory (frontend-react)"
else
    echo "❌ Error: package.json not found. Run from frontend-react directory"
    exit 1
fi

# Check environment files
if [ -f ".env" ]; then
    echo "✓ .env file exists"
else
    echo "⚠ .env file not found - will use defaults"
fi

if [ -f ".env.local" ]; then
    echo "✓ .env.local file exists"
else
    echo "⚠ .env.local file not found"
fi

# Check config file
if [ -f "src/config/api.config.js" ]; then
    echo "✓ API configuration file exists"
    if grep -q "fraudshield-ai-production" src/config/api.config.js; then
        echo "  ✓ Production URL configured"
    fi
else
    echo "❌ API configuration file not found"
fi

# Check key files
echo ""
echo "📦 Checking project files:"
files=(
    "src/App.jsx"
    "src/main.jsx"
    "src/pages/HomePage.jsx"
    "src/pages/DashboardPage.jsx"
    "src/pages/SimulatorPage.jsx"
    "src/utils/api.js"
    "vite.config.js"
    "package.json"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ❌ $file"
    fi
done

echo ""
echo "============================================================"
echo ""
echo "✅ Setup verification complete!"
echo ""
echo "Next steps:"
echo "  1. npm install          (install dependencies)"
echo "  2. npm run dev          (start development server)"
echo "  3. For deployment: vercel  (use Vercel CLI)"
echo ""
