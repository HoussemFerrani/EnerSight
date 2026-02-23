import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Get authorization token
const getAuthToken = () => {
  return localStorage.getItem('enersight_auth_token');
};

// Alerts API
export const alertsAPI = {
  // Get all alerts
  getAlerts: async (status = null, severity = null, limit = 50, offset = 0) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await axios.get(
      `${API_BASE_URL}/alerts/?${params.toString()}`,
      {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      }
    );
    return response.data;
  },

  // Get alert summary
  getSummary: async () => {
    const response = await axios.get(`${API_BASE_URL}/alerts/summary`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },

  // Get specific alert
  getAlert: async (alertId) => {
    const response = await axios.get(`${API_BASE_URL}/alerts/${alertId}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },

  // Acknowledge alert
  acknowledgeAlert: async (alertId) => {
    const response = await axios.post(
      `${API_BASE_URL}/alerts/${alertId}/acknowledge`,
      {},
      {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      }
    );
    return response.data;
  },

  // Resolve alert
  resolveAlert: async (alertId) => {
    const response = await axios.post(
      `${API_BASE_URL}/alerts/${alertId}/resolve`,
      {},
      {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      }
    );
    return response.data;
  },

  // Delete alert
  deleteAlert: async (alertId) => {
    await axios.delete(`${API_BASE_URL}/alerts/${alertId}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
  },
};
