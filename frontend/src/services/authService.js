/**
 * Authentication Service
 * Manages JWT tokens and authentication-related API calls
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const TOKEN_KEY = 'enersight_auth_token';
const USER_KEY = 'enersight_user';

// Create axios instance for auth
const authAPI = axios.create({
  baseURL: `${API_BASE_URL}/auth`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token Management
export const authService = {
  /**
   * Login user and store token
   */
  async login(username, password) {
    try {
      const response = await authAPI.post('/login', {
        username,
        password,
      });

      const { access_token, user_id, username: userName, email } = response.data;

      // Store token and user info
      localStorage.setItem(TOKEN_KEY, access_token);
      localStorage.setItem(USER_KEY, JSON.stringify({
        id: user_id,
        username: userName,
        email,
      }));

      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  /**
   * Logout user and clear token
   */
  async logout() {
    const token = this.getToken();

    if (token) {
      try {
        await authAPI.post('/logout', {}, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    // Clear local storage
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  /**
   * Get stored token
   */
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Get stored user info
   */
  getUser() {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.getToken();
  },

  /**
   * Get current user profile from API
   */
  async getCurrentUser() {
    const token = this.getToken();
    if (!token) {
      throw new Error('No token found');
    }

    try {
      const response = await authAPI.get('/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      // If token is invalid, clear it
      if (error.response?.status === 401) {
        this.logout();
      }
      throw error;
    }
  },

  /**
   * Refresh authentication token
   */
  async refreshToken() {
    const token = this.getToken();
    if (!token) {
      throw new Error('No token found');
    }

    try {
      const response = await authAPI.post('/refresh', {}, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const { access_token } = response.data;
      localStorage.setItem(TOKEN_KEY, access_token);

      return access_token;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.logout();
      throw error;
    }
  },

  /**
   * Verify if token is still valid
   */
  async verifyToken() {
    const token = this.getToken();
    if (!token) {
      return false;
    }

    try {
      const response = await authAPI.get('/verify', {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data.valid === true;
    } catch (error) {
      console.error('Token verification error:', error);
      return false;
    }
  },
};

export default authService;
