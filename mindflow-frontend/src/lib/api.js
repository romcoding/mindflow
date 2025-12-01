import axios from 'axios';

// Base URL for the backend API. Configure in Vercel as VITE_API_URL.
const baseURL = import.meta.env?.VITE_API_URL || 'https://mindflow-backend-9ec8.onrender.com/api';

console.log('🔗 API Base URL:', baseURL);
console.log('🌍 Environment:', import.meta.env?.MODE || 'unknown');

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
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Log request for debugging
  console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, config.data || '');
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
      
      console.error(`API Error [${status}]:`, data);
      
      // Handle 401 - Unauthorized (token expired/invalid)
      if (status === 401 && !error.config.url.includes('/auth/')) {
        // Try to refresh token if we have a refresh token
        const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
        if (refreshToken && !error.config._retry) {
          error.config._retry = true;
          try {
            const refreshResponse = await api.post('/auth/refresh', {}, {
              headers: { Authorization: `Bearer ${refreshToken}` }
            });
            if (refreshResponse.data.access_token) {
              const newToken = refreshResponse.data.access_token;
              localStorage.setItem('token', newToken);
              if (refreshResponse.data.user) {
                localStorage.setItem('user', JSON.stringify(refreshResponse.data.user));
              }
              // Retry original request with new token
              error.config.headers.Authorization = `Bearer ${newToken}`;
              return api(error.config);
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            if (typeof window !== 'undefined') {
              localStorage.removeItem('token');
              localStorage.removeItem('refresh_token');
              localStorage.removeItem('user');
              window.location.reload();
            }
          }
        }
      }
    } else if (error.request) {
      // Request made but no response
      console.error('No response from server:', error.request);
      console.error('Request URL:', error.config?.url);
      console.error('Request method:', error.config?.method);
      console.error('Request baseURL:', error.config?.baseURL);
      error.response = {
        data: { error: 'Network error. Please check your connection and try again.' }
      };
    } else {
      // Error in request setup
      console.error('Request error:', error.message);
      console.error('Error config:', error.config);
      console.error('Full error:', error);
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

export default api;
