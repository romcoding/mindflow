import axios from 'axios';

// Base URL for the backend API. Configure in Vercel as VITE_API_BASE_URL.
const baseURL = import.meta.env?.VITE_API_BASE_URL || 'https://mindflow-backend-9ec8.onrender.com/api';

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
  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  if (accessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Better error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      const status = error.response.status;
      const data = error.response.data;
      
      console.error(`API Error [${status}]:`, data);
      
      // Handle 401 - Unauthorized (token expired/invalid)
      if (status === 401 && !error.config.url.includes('/auth/')) {
        // Don't handle auth endpoint errors here
      }
    } else if (error.request) {
      // Request made but no response
      console.error('No response from server:', error.request);
      error.response = {
        data: { error: 'Network error. Please check your connection and try again.' }
      };
    } else {
      // Error in request setup
      console.error('Request error:', error.message);
      error.response = {
        data: { error: 'Request failed. Please try again.' }
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
  refresh: () => {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
    return api.post('/auth/refresh', {}, {
      headers: refreshToken ? { Authorization: `Bearer ${refreshToken}` } : {}
    });
  },
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
