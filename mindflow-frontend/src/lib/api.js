import axios from 'axios';

// Sanitize request data to remove sensitive information
function sanitizeRequestData(data) {
  if (!data || typeof data !== 'object') return data;
  
  const sensitiveFields = ['password', 'old_password', 'new_password', 'confirmPassword', 'currentPassword'];
  const sanitized = { ...data };
  
  sensitiveFields.forEach(field => {
    if (sanitized[field]) {
      sanitized[field] = '***REDACTED***';
    }
  });
  
  return sanitized;
}

// Base URL for the backend API. Configure in Vercel as VITE_API_URL.
const getBaseURL = () => {
  const envURL = import.meta.env?.VITE_API_URL;
  if (envURL && typeof envURL === 'string') {
    // Validate that baseURL is a valid HTTP/HTTPS URL (not a database connection string)
    if (envURL.startsWith('postgresql://') || envURL.startsWith('postgres://') || envURL.startsWith('mysql://')) {
      // Only log in dev - this check happens at build time too
      if (typeof window !== 'undefined' && import.meta.env?.DEV) {
        console.error('❌ ERROR: VITE_API_URL is set to a database connection string instead of the backend API URL!');
        console.error('Current value:', envURL);
        console.error('Please set VITE_API_URL in Vercel to: https://mindflow-backend-9ec8.onrender.com/api');
      }
      return 'https://mindflow-backend-9ec8.onrender.com/api';
    }
    return envURL;
  }
  return 'https://mindflow-backend-9ec8.onrender.com/api';
};

const baseURL = getBaseURL();

// Only log in development to avoid build issues
if (import.meta.env?.DEV) {
  console.log('🔗 API Base URL:', baseURL);
  console.log('🌍 Environment:', import.meta.env?.MODE || 'unknown');
}

const api = axios.create({ 
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach access token to all requests by default
api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) {
    config.headers = config.headers || {};
    // Ensure Authorization header is set correctly
    config.headers.Authorization = `Bearer ${token.trim()}`;
    // Log token presence for debugging (not the actual token) - only in dev
    if (import.meta.env?.DEV && config.url && !config.url.includes('/auth/')) {
      console.log(`🔑 Token attached to request: ${config.method?.toUpperCase()} ${config.url}`);
      console.log(`🔑 Token length: ${token.length}, starts with: ${token.substring(0, 20)}...`);
    }
  } else {
    // Warn if token is missing for protected endpoints - only in dev
    if (import.meta.env?.DEV && config.url && !config.url.includes('/auth/')) {
      console.warn(`⚠️ No token available for request: ${config.method?.toUpperCase()} ${config.url}`);
    }
  }
  // Log request for debugging (sanitize sensitive data) - only in dev
  const sanitizedData = config.data ? sanitizeRequestData(config.data) : '';
  if (import.meta.env?.DEV) {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, sanitizedData);
  }
  return config;
});

// Better error handling interceptor with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response) {
      // Server responded with error
      const status = error.response.status;
      const data = error.response.data;
      
      if (import.meta.env?.DEV) {
        console.error(`API Error [${status}]:`, data);
      }
      
      // Handle 401 - Unauthorized (token expired/invalid)
      // Don't handle 401 for auth endpoints (login, register, refresh) - those are expected
      if (status === 401 && !error.config.url.includes('/auth/')) {
        // Try to refresh token if we have a refresh token
        const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
        if (refreshToken && !error.config._retry) {
          error.config._retry = true;
          try {
            if (import.meta.env?.DEV) {
              console.log('🔄 Attempting token refresh due to 401 error');
            }
            const refreshResponse = await api.post('/auth/refresh', {}, {
              headers: { Authorization: `Bearer ${refreshToken}` }
            });
            const newToken = refreshResponse.data.access_token;
            if (newToken || refreshResponse.data.success) {
              if (newToken) {
                localStorage.setItem('token', newToken);
                if (refreshResponse.data.user) {
                  localStorage.setItem('user', JSON.stringify(refreshResponse.data.user));
                }
                if (import.meta.env?.DEV) {
                  console.log('✅ Token refreshed successfully');
                }
                // Retry original request with new token
                error.config.headers.Authorization = `Bearer ${newToken}`;
                return api(error.config);
              }
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            if (import.meta.env?.DEV) {
              console.error('❌ Token refresh failed:', refreshError);
            }
            if (typeof window !== 'undefined') {
              // Only clear tokens if refresh actually failed, not on network errors
              if (refreshError.response && refreshError.response.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                // Don't reload immediately - let the auth hook handle it
                if (import.meta.env?.DEV) {
                  console.log('🔒 Tokens cleared due to refresh failure');
                }
              }
            }
          }
        } else if (!refreshToken && import.meta.env?.DEV) {
          console.warn('⚠️ No refresh token available for 401 error');
        }
      }
    } else if (error.request) {
      // Request made but no response
      if (import.meta.env?.DEV) {
        console.error('No response from server:', error.request);
        console.error('Request URL:', error.config?.url);
        console.error('Request method:', error.config?.method);
        console.error('Request baseURL:', error.config?.baseURL);
      }
      error.response = {
        data: { error: 'Network error. Please check your connection and try again.' }
      };
    } else {
      // Error in request setup
      if (import.meta.env?.DEV) {
        console.error('Request error:', error.message);
        console.error('Error config:', error.config);
        console.error('Full error:', error);
      }
      error.response = {
        data: { error: error.message || 'Request failed. Please try again.' }
      };
    }
    
    return Promise.reject(error);
  }
);

// Auth API with explicit handling for refresh token usage
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  // Use refresh token explicitly for this call
  refreshToken: () => {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
    if (!refreshToken) {
      return Promise.reject(new Error('No refresh token available'));
    }
    return api.post('/auth/refresh', {}, {
      headers: { Authorization: `Bearer ${refreshToken}` }
    });
  },
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (profileData) => api.put('/auth/profile', profileData),
  changePassword: (passwordData) => api.put('/auth/change-password', passwordData),
};

export const tasksAPI = {
  getTasks: (params) => api.get('/tasks', { params }),
  createTask: (task) => api.post('/tasks', task),
  updateTask: (taskId, task) => api.put(`/tasks/${taskId}`, task),
  moveTask: (taskId, boardColumn, boardPosition) => api.post(`/tasks/${taskId}/move`, { board_column: boardColumn, board_position: boardPosition }),
  deleteTask: (taskId) => api.delete(`/tasks/${taskId}`),
  toggleTask: (taskId) => api.patch(`/tasks/${taskId}/toggle`),
};

export const stakeholdersAPI = {
  getStakeholders: () => api.get('/stakeholders'),
  createStakeholder: (stakeholder) => api.post('/stakeholders', stakeholder),
  updateStakeholder: (stakeholderId, stakeholder) => api.put(`/stakeholders/${stakeholderId}`, stakeholder),
  deleteStakeholder: (stakeholderId) => api.delete(`/stakeholders/${stakeholderId}`),
};

export const notesAPI = {
  getNotes: () => api.get('/notes'),
  createNote: (note) => api.post('/notes', note),
  updateNote: (noteId, note) => api.put(`/notes/${noteId}`, note),
  deleteNote: (noteId) => api.delete(`/notes/${noteId}`),
};

export const aiAPI = {
  parseContent: (text) => api.post('/ai/parse-content', { text }),
};

export const linkedinAPI = {
  fetchProfile: (data) => api.post('/linkedin/fetch-profile', data),
};

export default api;
