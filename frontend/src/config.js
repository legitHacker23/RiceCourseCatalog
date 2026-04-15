// Configuration for the Rice Course Assistant Frontend
const config = {
  // Backend API URL - change this to switch between environments
  BACKEND_URL: process.env.REACT_APP_API_BASE_URL || 'https://ricecoursecatalog.onrender.com',
  //BACKEND_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',

  
  // Alternative configurations for different environments:
  // BACKEND_URL: 'http://localhost:8000',  // Local development
  // BACKEND_URL: 'https://ricecatalog.onrender.com',  // Production (Render)
  // BACKEND_URL: 'http://192.168.1.100:8000',  // Local network
  
  // API endpoints
  API_ENDPOINTS: {
    HEALTH: '/api/health',
    ADVISORS: '/api/advisors',
    DEPARTMENTS: '/api/departments',
    ASK: '/api/ask',
    CATALOG_SEARCH: '/api/catalog/search',
    CATALOG_STATS: '/api/catalog/stats',
    SCHEDULE_BUILD: '/api/schedule/build',
    SCHEDULE_GUIDELINES: '/api/schedule/guidelines'
  }
};

export default config; 