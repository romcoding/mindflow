import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../lib/api.js';
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext();

export const useAuth = () => {
  return {
    user: {
      id: 1,
      username: "demo",
      email: "demo@example.com",
      first_name: "Demo",
      last_name: "User",
      is_active: true
    },
    loading: false,
    isAuthenticated: true,
    login: async () => ({ success: true, user: {
      id: 1, username:"demo", email: "demo@example.com", first_name: "Demo", last_name: "User", is_active: true
    }}),
    register: async () => ({ success: true, user: {
      id: 1, username:"demo", email: "demo@example.com", first_name: "Demo", last_name: "User", is_active: true
    }}),
    logout: () => {},
    updateProfile: async () => ({ success: true, user: {
      id: 1, username:"demo", email: "demo@example.com", first_name: "Demo", last_name: "User", is_active: true
    }}),
    changePassword: async () => ({ success: true }),
    refreshToken: async () => ({ success: true })
  }
};

export const AuthProvider = ({ children }) => children;
