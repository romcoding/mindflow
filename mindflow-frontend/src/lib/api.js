import axios from 'axios';

// Base URL for the backend API. Configure in Vercel as VITE_API_BASE_URL.
const baseURL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL)
  ? import.meta.env.VITE_API_BASE_URL
  : '/api';

const api = axios.create({ baseURL });

// Attach access token to all requests by default
api.interceptors.request.use((config) => {
  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  if (accessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

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
  toggleTask: (taskId) => api.patch(`/tasks/${taskId}/toggle`),
};

export const stakeholdersAPI = {
  getStakeholders: () => api.get('/stakeholders'),
  createStakeholder: (stakeholder) => api.post('/stakeholders', stakeholder),
};

export const notesAPI = {
  getNotes: () => api.get('/notes'),
  createNote: (note) => api.post('/notes', note),
};

export default api;


