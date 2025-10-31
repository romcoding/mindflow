import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../lib/api.js';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 > Date.now()) {
          setUser(decoded);
        } else {
          localStorage.removeItem('token');
          setToken(null);
        }
      } catch (error) {
        console.error('Invalid token:', error);
        localStorage.removeItem('token');
        setToken(null);
      }
    }
    setLoading(false);
  }, [token]);

  const login = async (credentials) => {
    try {
      setLoading(true);
      const response = await authAPI.login(credentials);
      
      if (response.data.success) {
        const { token: newToken, user: userData } = response.data;
        localStorage.setItem('token', newToken);
        setToken(newToken);
        setUser(userData);
        return { success: true, user: userData };
      } else {
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.response?.data?.message || 'Login failed' };
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      const response = await authAPI.register(userData);
      
      if (response.data.success) {
        const { token: newToken, user: newUser } = response.data;
        localStorage.setItem('token', newToken);
        setToken(newToken);
        setUser(newUser);
        return { success: true, user: newUser };
      } else {
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.response?.data?.message || 'Registration failed' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await authAPI.updateProfile(profileData);
      if (response.data.success) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      } else {
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      console.error('Profile update error:', error);
      return { success: false, error: error.response?.data?.message || 'Profile update failed' };
    }
  };

  const changePassword = async (passwordData) => {
    try {
      const response = await authAPI.changePassword(passwordData);
      return { success: response.data.success, message: response.data.message };
    } catch (error) {
      console.error('Password change error:', error);
      return { success: false, error: error.response?.data?.message || 'Password change failed' };
    }
  };

  const refreshToken = async () => {
    try {
      const response = await authAPI.refreshToken();
      if (response.data.success) {
        const { token: newToken } = response.data;
        localStorage.setItem('token', newToken);
        setToken(newToken);
        return { success: true };
      } else {
        logout();
        return { success: false };
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      logout();
      return { success: false };
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    refreshToken,
    token
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
