import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../lib/api.js';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  // Initialize auth state from localStorage (blended approach)
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      const storedRefreshToken = localStorage.getItem('refresh_token');
      
      if (storedToken) {
        try {
          // Decode token to check validity
          let decoded;
          try {
            decoded = jwtDecode(storedToken);
          } catch (decodeError) {
            console.error('Failed to decode token:', decodeError);
            // If token can't be decoded, it's invalid - clear it
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            setToken(null);
            setUser(null);
            setLoading(false);
            return;
          }
          
          // Check if token is expired
          const expirationTime = decoded.exp ? decoded.exp * 1000 : null;
          if (expirationTime && expirationTime > Date.now()) {
            // Use stored user object if available, otherwise fall back to JWT claims
            if (storedUser) {
              try {
                const userData = JSON.parse(storedUser);
                setUser(userData);
              } catch (e) {
                // Fallback to JWT claims if stored user is invalid
                setUser({
                  id: decoded.sub || decoded.identity,
                  username: decoded.username,
                  email: decoded.email,
                  first_name: decoded.first_name,
                  last_name: decoded.last_name,
                  name: `${decoded.first_name || ''} ${decoded.last_name || ''}`.trim() || decoded.username
                });
              }
            } else {
              // Use JWT claims as fallback
              setUser({
                id: decoded.sub || decoded.identity,
                username: decoded.username,
                email: decoded.email,
                first_name: decoded.first_name,
                last_name: decoded.last_name,
                name: `${decoded.first_name || ''} ${decoded.last_name || ''}`.trim() || decoded.username
              });
            }
            setToken(storedToken);
          } else {
            // Token expired, try to refresh if refresh token exists
            if (storedRefreshToken) {
              try {
                const response = await authAPI.refreshToken();
                if (response.data.success && response.data.access_token) {
                  const { access_token: newToken, user: userData } = response.data;
                  localStorage.setItem('token', newToken);
                  if (userData) {
                    localStorage.setItem('user', JSON.stringify(userData));
                    setUser(userData);
                  }
                  setToken(newToken);
                } else {
                  throw new Error('Refresh failed');
                }
              } catch (refreshError) {
                // Refresh failed, clear everything
                console.error('Token refresh failed:', refreshError);
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                setToken(null);
                setUser(null);
              }
            } else {
              // No refresh token, clear everything
              localStorage.removeItem('token');
              localStorage.removeItem('user');
              setToken(null);
              setUser(null);
            }
          }
        } catch (error) {
          console.error('Invalid token:', error);
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };
    
    initializeAuth();
  }, []);

  const login = async (credentials) => {
    try {
      setLoading(true);
      console.log('🔐 Attempting login with:', { email: credentials.email, hasPassword: !!credentials.password });
      const response = await authAPI.login(credentials);
      
      console.log('📥 Login response received:', { 
        hasAccessToken: !!response.data.access_token,
        hasRefreshToken: !!response.data.refresh_token,
        hasUser: !!response.data.user,
        userEmail: response.data.user?.email
      });
      
      // Backend returns access_token, refresh_token, user, and message
      if (response.data.access_token && response.data.user) {
        const { access_token: newToken, refresh_token: newRefreshToken, user: userData } = response.data;
        
        // Store tokens and full user object (blended approach)
        localStorage.setItem('token', newToken);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }
        localStorage.setItem('user', JSON.stringify(userData));
        
        console.log('✅ Login successful, tokens stored');
        console.log('🔍 Token preview:', newToken.substring(0, 20) + '...');
        
        // Set state immediately
        setToken(newToken);
        setUser(userData);
        
        // Verify token was stored
        const verifyToken = localStorage.getItem('token');
        if (!verifyToken) {
          console.error('❌ Token was not stored in localStorage!');
        } else {
          console.log('✅ Token verified in localStorage');
        }
        
        return { success: true, user: userData };
      } else {
        console.error('❌ Login response missing required data:', response.data);
        return { success: false, error: response.data.error || response.data.message || 'Login failed' };
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      console.error('Login error response:', error.response);
      console.error('Login error request:', error.request);
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message || 
                          error.message || 
                          'Login failed. Please check your connection and try again.';
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      console.log("📝 Registering with:", { 
        email: userData.email, 
        name: userData.name,
        hasPassword: !!userData.password,
        first_name: userData.first_name,
        last_name: userData.last_name
        // Password is intentionally NOT logged
      });
      const response = await authAPI.register(userData);
      console.log("Registration response:", response);
      
      // Backend returns access_token, refresh_token, user, and message
      if (response.data.access_token && response.data.user) {
        const { access_token: newToken, refresh_token: newRefreshToken, user: newUser } = response.data;
        
        // Store tokens and full user object (blended approach)
        localStorage.setItem('token', newToken);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }
        localStorage.setItem('user', JSON.stringify(newUser));
        
        setToken(newToken);
        setUser(newUser);
        return { success: true, user: newUser };
      } else {
        // Handle error response from backend
        const errorMsg = response.data.error || response.data.message || response.data.details || 'Registration failed';
        console.error('Registration failed:', response.data);
        return { success: false, error: errorMsg };
      }
    } catch (error) {
      console.error('Registration error:', error);
      if (error.response) {
        console.error('Registration error response:', error.response);
        console.error('Registration error response data:', error.response.data);
        console.error('Registration error response status:', error.response.status);
        // Extract error message from response
        const errorMsg = error.response.data?.error || 
                        error.response.data?.message || 
                        error.response.data?.details || 
                        `Registration failed (${error.response.status})`;
        return { success: false, error: errorMsg };
      } else if (error.request) {
        console.error('Registration error request:', error.request);
        return { success: false, error: 'Network error. Please check your connection and try again.' };
      } else {
        console.error('Registration error message:', error.message);
        console.error('Registration full error:', error);
        const errorMessage = error.message || 
                           (error.response?.data?.error || 'Registration failed. Please check your connection and try again.');
        return { success: false, error: errorMessage };
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await authAPI.updateProfile(profileData);
      if (response.data.success && response.data.user) {
        // Update stored user object
        localStorage.setItem('user', JSON.stringify(response.data.user));
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      } else {
        return { success: false, error: response.data.message || response.data.error || 'Profile update failed' };
      }
    } catch (error) {
      console.error('Profile update error:', error);
      return { success: false, error: error.response?.data?.error || error.response?.data?.message || 'Profile update failed' };
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
      console.log('🔄 Refresh token response:', { 
        hasSuccess: !!response.data.success,
        hasAccessToken: !!response.data.access_token,
        hasUser: !!response.data.user
      });
      
      // Backend returns either {success: true, access_token: ...} or {access_token: ...}
      const newToken = response.data.access_token;
      if (newToken) {
        const userData = response.data.user;
        
        // Update stored token and user object
        localStorage.setItem('token', newToken);
        if (userData) {
          localStorage.setItem('user', JSON.stringify(userData));
          setUser(userData);
        }
        setToken(newToken);
        console.log('✅ Token refreshed successfully in useAuth');
        return { success: true };
      } else {
        console.error('❌ Refresh response missing access_token');
        logout();
        return { success: false };
      }
    } catch (error) {
      console.error('❌ Token refresh error:', error);
      console.error('Refresh error response:', error.response?.data);
      // Only logout if it's actually an auth error, not a network error
      if (error.response && error.response.status === 401) {
        logout();
      }
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
