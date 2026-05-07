import {
  Compare as CompareIcon,
  DateRange as DateRangeIcon,
  Download as DownloadIcon,
  AttachMoney as MoneyIcon,
  TrendingDown as TrendingDownIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Alert as MuiAlert,
  Paper,
  Select,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  XAxis,
  YAxis
} from 'recharts';
import { analyticsAPI } from '../services/analyticsService';

const AnalyticsEnhanced = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Date range state
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().slice(0, 16);
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().slice(0, 16));

  // Data state
  const [summary, setSummary] = useState(null);
  const [quickStats, setQuickStats] = useState(null);
  const [trends, setTrends] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [costData, setCostData] = useState(null);

  // Settings
  const [aggregation, setAggregation] = useState('day');
  const [costPerKwh, setCostPerKwh] = useState(0.12);
  const [comparisonType, setComparisonType] = useState('previous_period');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchSummary(),
        fetchQuickStats(),
        fetchTrends(),
        fetchCost(),
      ]);
    } catch (err) {
      setError('Failed to load analytics data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const data = await analyticsAPI.getSummary(startDate, endDate, costPerKwh);
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch summary:', err);
    }
  };

  const fetchQuickStats = async () => {
    try {
      const data = await analyticsAPI.getQuickStats();
      setQuickStats(data);
    } catch (err) {
      console.error('Failed to fetch quick stats:', err);
    }
  };

  const fetchTrends = async () => {
    try {
      const data = await analyticsAPI.getTrends(30);
      setTrends(data);
    } catch (err) {
      console.error('Failed to fetch trends:', err);
    }
  };

  const fetchCost = async () => {
    try {
      const data = await analyticsAPI.calculateCost(startDate, endDate, costPerKwh);
      setCostData(data);
    } catch (err) {
      console.error('Failed to calculate cost:', err);
    }
  };

  const fetchComparison = async () => {
    try {
      const data = await analyticsAPI.comparePeriods(startDate, endDate, comparisonType);
      setComparison(data);
    } catch (err) {
      setError('Failed to fetch comparison: ' + err.message);
    }
  };

  const handleExport = async () => {
    try {
      const blob = await analyticsAPI.exportToCSV(startDate, endDate, aggregation);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `energy_data_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export data: ' + err.message);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <DateRangeIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Enhanced Analytics
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExport}
          disabled={loading}
        >
          Export Data
        </Button>
      </Box>

      {error && (
        <MuiAlert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </MuiAlert>
      )}

      {/* Date Range and Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="Start Date"
              type="datetime-local"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              label="End Date"
              type="datetime-local"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Aggregation</InputLabel>
              <Select value={aggregation} onChange={(e) => setAggregation(e.target.value)}>
                <MenuItem value="hour">Hourly</MenuItem>
                <MenuItem value="day">Daily</MenuItem>
                <MenuItem value="week">Weekly</MenuItem>
                <MenuItem value="month">Monthly</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              label="Cost per kWh ($)"
              type="number"
              value={costPerKwh}
              onChange={(e) => setCostPerKwh(parseFloat(e.target.value))}
              fullWidth
              inputProps={{ step: 0.01, min: 0 }}
            />
          </Grid>
          <Grid item xs={12} sm={12} md={2}>
            <Button
              variant="contained"
              fullWidth
              onClick={fetchAllData}
              disabled={loading}
              sx={{ height: 56 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Refresh'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Quick Stats Cards */}
      {quickStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Today
                </Typography>
                <Typography variant="h4">{quickStats.today.total.toFixed(1)} kWh</Typography>
                <Typography variant="body2" color="textSecondary">
                  Peak: {quickStats.today.peak.toFixed(1)} kWh
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  This Week
                </Typography>
                <Typography variant="h4">{quickStats.this_week.total.toFixed(1)} kWh</Typography>
                <Typography variant="body2" color="textSecondary">
                  Avg: {quickStats.this_week.average.toFixed(1)} kWh/day
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  This Month
                </Typography>
                <Typography variant="h4">{quickStats.this_month.total.toFixed(1)} kWh</Typography>
                <Typography variant="body2" color="textSecondary">
                  Avg: {quickStats.this_month.average.toFixed(1)} kWh/day
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Last 24 Hours
                </Typography>
                <Typography variant="h4">{quickStats.last_24h.total.toFixed(1)} kWh</Typography>
                <Typography variant="body2" color="textSecondary">
                  Peak: {quickStats.last_24h.peak.toFixed(1)} kWh
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Summary Section */}
      {summary && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Period Summary
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={4}>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Total Consumption
                </Typography>
                <Typography variant="h5">{summary.total_consumption.toFixed(2)} kWh</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Average Daily
                </Typography>
                <Typography variant="h5">{summary.average_daily.toFixed(2)} kWh/day</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Peak Consumption
                </Typography>
                <Typography variant="h5">{summary.peak_consumption.toFixed(2)} kWh</Typography>
                <Typography variant="caption" color="textSecondary">
                  {formatDate(summary.peak_timestamp)}
                </Typography>
              </Box>
            </Grid>
            {summary.total_cost && (
              <Grid item xs={12} sm={6} md={4}>
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    Estimated Cost
                  </Typography>
                  <Typography variant="h5" color="primary">
                    {formatCurrency(summary.total_cost)}
                  </Typography>
                </Box>
              </Grid>
            )}
            <Grid item xs={12} sm={6} md={4}>
              <Box>
                <Typography variant="body2" color="textSecondary">
                  Data Points
                </Typography>
                <Typography variant="h5">{summary.data_points}</Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Trends Chart */}
      {trends && trends.daily_data && trends.daily_data.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Consumption Trends (Last 30 Days)</Typography>
            <Box display="flex" alignItems="center">
              {trends.trend_direction === 'increasing' ? (
                <TrendingUpIcon color="error" />
              ) : trends.trend_direction === 'decreasing' ? (
                <TrendingDownIcon color="success" />
              ) : null}
              <Chip
                label={`${trends.trend_direction} ${Math.abs(trends.trend_percentage).toFixed(1)}%`}
                color={trends.trend_direction === 'increasing' ? 'error' : 'success'}
                size="small"
                sx={{ ml: 1 }}
              />
            </Box>
          </Box>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trends.daily_data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis label={{ value: 'kWh', angle: -90, position: 'insideLeft' }} />
              <RechartsTooltip
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value) => [`${value.toFixed(2)} kWh`, 'Total']}
              />
              <Area type="monotone" dataKey="total" stroke="#1976d2" fill="#1976d2" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </Paper>
      )}

      {/* Cost Calculation */}
      {costData && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" alignItems="center" mb={2}>
            <MoneyIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">Cost Analysis</Typography>
          </Box>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="textSecondary">
                Total Consumption
              </Typography>
              <Typography variant="h5">{costData.total_kwh.toFixed(2)} kWh</Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="textSecondary">
                Rate per kWh
              </Typography>
              <Typography variant="h5">{formatCurrency(costData.cost_per_kwh)}</Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="textSecondary">
                Total Cost
              </Typography>
              <Typography variant="h5" color="primary">
                {formatCurrency(costData.total_cost)}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Period Comparison */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center">
            <CompareIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">Period Comparison</Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={2}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Compare With</InputLabel>
              <Select
                value={comparisonType}
                onChange={(e) => setComparisonType(e.target.value)}
              >
                <MenuItem value="previous_period">Previous Period</MenuItem>
                <MenuItem value="same_period_last_month">Same Period Last Month</MenuItem>
                <MenuItem value="same_period_last_year">Same Period Last Year</MenuItem>
              </Select>
            </FormControl>
            <Button variant="outlined" onClick={fetchComparison}>
              Compare
            </Button>
          </Box>
        </Box>
        {comparison && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="textSecondary">
                    Current Period
                  </Typography>
                  <Typography variant="h4">{comparison.current_period.total.toFixed(2)} kWh</Typography>
                  <Typography variant="body2">
                    Avg: {comparison.current_period.average.toFixed(2)} kWh
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="textSecondary">
                    Comparison Period
                  </Typography>
                  <Typography variant="h4">{comparison.comparison_period.total.toFixed(2)} kWh</Typography>
                  <Typography variant="body2">
                    Avg: {comparison.comparison_period.average.toFixed(2)} kWh
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Divider />
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="body1">
                  Difference: <strong>{comparison.difference.toFixed(2)} kWh</strong>
                </Typography>
                <Chip
                  label={`${comparison.percentage_change > 0 ? '+' : ''}${comparison.percentage_change.toFixed(1)}%`}
                  color={comparison.percentage_change > 0 ? 'error' : 'success'}
                  sx={{ mt: 1 }}
                />
              </Box>
            </Grid>
          </Grid>
        )}
      </Paper>
    </Container>
  );
};

export default AnalyticsEnhanced;
