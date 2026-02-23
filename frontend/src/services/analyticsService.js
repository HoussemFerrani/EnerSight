import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const getAuthToken = () => {
  return localStorage.getItem('enersight_auth_token');
};

export const analyticsAPI = {
  // Get data by date range
  getDataByDateRange: async (startDate, endDate, aggregation = null) => {
    const response = await axios.post(
      `${API_BASE_URL}/analytics/date-range`,
      {
        start_date: startDate,
        end_date: endDate,
        aggregation: aggregation,
      },
      {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      }
    );
    return response.data;
  },

  // Get analytics summary
  getSummary: async (startDate, endDate, costPerKwh = null) => {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
    });
    if (costPerKwh) params.append('cost_per_kwh', costPerKwh.toString());

    const response = await axios.get(`${API_BASE_URL}/analytics/summary?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },

  // Get aggregated data
  getAggregated: async (startDate, endDate, period) => {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      period: period,
    });

    const response = await axios.get(`${API_BASE_URL}/analytics/aggregated?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },

  // Calculate cost
  calculateCost: async (startDate, endDate, costPerKwh = 0.12) => {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      cost_per_kwh: costPerKwh.toString(),
    });

    const response = await axios.get(`${API_BASE_URL}/analytics/cost?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },

  // Compare periods
  comparePeriods: async (currentStart, currentEnd, comparisonType = 'previous_period') => {
    const params = new URLSearchParams({
      current_start: currentStart,
      current_end: currentEnd,
      comparison_type: comparisonType,
    });

    const response = await axios.get(`${API_BASE_URL}/analytics/compare?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },

  // Export to CSV
  exportToCSV: async (startDate, endDate, aggregation = null) => {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
    });
    if (aggregation) params.append('aggregation', aggregation);

    const response = await axios.get(`${API_BASE_URL}/analytics/export/csv?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // Get quick stats
  getQuickStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/analytics/quick-stats`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },

  // Get trends
  getTrends: async (days = 30) => {
    const params = new URLSearchParams({
      days: days.toString(),
    });

    const response = await axios.get(`${API_BASE_URL}/analytics/trends?${params.toString()}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  },
};
