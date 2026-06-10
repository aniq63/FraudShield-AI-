/**
 * FraudShield AI Frontend Configuration
 * Production API URL is configured here
 */

// Production backend URL
export const API_CONFIG = {
  // Main production backend
  PRODUCTION_URL: 'https://fraudshield-ai-production-78c0.up.railway.app',
  
  // Development (for local testing)
  DEVELOPMENT_URL: 'http://localhost:8000',
  
  // Get appropriate URL based on environment
  getBaseURL() {
    // Use environment variable if available (Vercel, other hosting)
    const envUrl = import.meta.env.VITE_API_URL;
    if (envUrl) {
      return envUrl;
    }
    
    // Use development URL if running locally
    if (import.meta.env.DEV) {
      return this.DEVELOPMENT_URL;
    }
    
    // Default to production URL
    return this.PRODUCTION_URL;
  }
};

// Export the API URL
export const API_URL = API_CONFIG.getBaseURL();

export default API_CONFIG;
