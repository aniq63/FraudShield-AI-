#!/usr/bin/env node

/**
 * FraudShield AI Frontend Setup Verification Script
 * Run this to verify all configuration is correct
 */

const path = require('path');
const fs = require('fs');

console.log('\n🔧 FraudShield AI Frontend Setup Verification\n');
console.log('=' . repeat(60));

// Check Node version
const nodeVersion = process.version;
console.log(`✓ Node.js version: ${nodeVersion}`);

// Check if we're in the right directory
const packageJsonPath = path.join(__dirname, '..', 'package.json');
if (!fs.existsSync(packageJsonPath)) {
  console.error('❌ Error: package.json not found. Run this from frontend-react directory');
  process.exit(1);
}
console.log('✓ In correct directory (frontend-react)');

// Check environment files
const envFile = path.join(__dirname, '..', '.env');
const envLocalFile = path.join(__dirname, '..', '.env.local');

if (fs.existsSync(envFile)) {
  console.log('✓ .env file exists');
} else {
  console.warn('⚠ .env file not found - will use defaults');
}

if (fs.existsSync(envLocalFile)) {
  console.log('✓ .env.local file exists');
} else {
  console.warn('⚠ .env.local file not found');
}

// Check config file
const configFile = path.join(__dirname, '..', 'src', 'config', 'api.config.js');
if (fs.existsSync(configFile)) {
  console.log('✓ API configuration file exists');
  const configContent = fs.readFileSync(configFile, 'utf-8');
  if (configContent.includes('fraudshield-ai-production')) {
    console.log('  ✓ Production URL configured: fraudshield-ai-production-78c0.up.railway.app');
  }
} else {
  console.error('❌ API configuration file not found');
}

// Check key files
const keyFiles = [
  'src/App.jsx',
  'src/main.jsx',
  'src/pages/HomePage.jsx',
  'src/pages/DashboardPage.jsx',
  'src/pages/SimulatorPage.jsx',
  'src/utils/api.js',
  'vite.config.js',
  'package.json'
];

console.log('\n📦 Checking project files:');
keyFiles.forEach(file => {
  const filePath = path.join(__dirname, '..', file);
  if (fs.existsSync(filePath)) {
    console.log(`  ✓ ${file}`);
  } else {
    console.error(`  ❌ ${file}`);
  }
});

console.log('\n' + '=' . repeat(60));
console.log('\n✅ Setup verification complete!\n');
console.log('Next steps:');
console.log('  1. npm install          (install dependencies)');
console.log('  2. npm run dev          (start development server)');
console.log('  3. For deployment: vercel  (use Vercel CLI)\n');
