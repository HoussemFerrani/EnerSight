import {
  Alert,
  Box,
  CircularProgress,
  Container,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Tab,
  Tabs,
  Typography
} from '@mui/material'
import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { energyAPI } from '../services/api'

function Analytics() {
  const [tabValue, setTabValue] = useState(0)
  const [period, setPeriod] = useState('week')
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Mock data for visualization
  const weeklyData = [
    { day: 'Mon', consumption: 145.2, renewable: 25.5, net: 119.7 },
    { day: 'Tue', consumption: 152.8, renewable: 28.3, net: 124.5 },
    { day: 'Wed', consumption: 138.5, renewable: 22.1, net: 116.4 },
    { day: 'Thu', consumption: 148.9, renewable: 26.7, net: 122.2 },
    { day: 'Fri', consumption: 156.3, renewable: 30.2, net: 126.1 },
    { day: 'Sat', consumption: 95.4, renewable: 18.5, net: 76.9 },
    { day: 'Sun', consumption: 88.7, renewable: 16.2, net: 72.5 },
  ]

  const deviceBreakdown = [
    { name: 'HVAC', value: 45, color: '#1976d2' },
    { name: 'Lighting', value: 25, color: '#dc004e' },
    { name: 'Equipment', value: 20, color: '#ff9800' },
    { name: 'Other', value: 10, color: '#4caf50' },
  ]

  const hourlyPattern = [
    { hour: '00:00', value: 35 },
    { hour: '03:00', value: 28 },
    { hour: '06:00', value: 45 },
    { hour: '09:00', value: 75 },
    { hour: '12:00', value: 85 },
    { hour: '15:00', value: 78 },
    { hour: '18:00', value: 65 },
    { hour: '21:00', value: 50 },
  ]

  useEffect(() => {
    fetchStatistics()
  }, [period])

  const fetchStatistics = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await energyAPI.getStatistics(period)
      setStatistics(response.data)
    } catch (err) {
      console.error('Failed to fetch statistics:', err)
      setError('Using demo data - connect InfluxDB for historical analytics')

      // Use mock data
      setStatistics({
        total_consumption: 925.8,
        average_daily: 132.3,
        peak_consumption: 156.3,
        minimum_consumption: 88.7,
        days: 7
      })
    } finally {
      setLoading(false)
    }
  }

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue)
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Energy Analytics
          </Typography>
          <Typography color="text.secondary">
            Historical data analysis and insights
          </Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Time Period</InputLabel>
          <Select
            value={period}
            label="Time Period"
            onChange={(e) => setPeriod(e.target.value)}
          >
            <MenuItem value="day">Last Day</MenuItem>
            <MenuItem value="week">Last Week</MenuItem>
            <MenuItem value="month">Last Month</MenuItem>
            <MenuItem value="year">Last Year</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {error && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Consumption Trends" />
          <Tab label="Device Breakdown" />
          <Tab label="Hourly Patterns" />
        </Tabs>
      </Box>

      {/* Consumption Trends Tab */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Daily Consumption Overview
              </Typography>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="consumption" fill="#1976d2" name="Total Consumption" />
                  <Bar dataKey="renewable" fill="#4caf50" name="Renewable Energy" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Net Consumption Trend
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="net" stroke="#1976d2" strokeWidth={2} name="Net Consumption (kWh)" />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Key Statistics
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography color="text.secondary">Total Consumption:</Typography>
                  <Typography variant="h6">{statistics?.total_consumption?.toFixed(1) || '0.0'} kWh</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography color="text.secondary">Daily Average:</Typography>
                  <Typography variant="h6">{statistics?.average_daily?.toFixed(1) || '0.0'} kWh</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography color="text.secondary">Peak Day:</Typography>
                  <Typography variant="h6" color="error.main">{statistics?.peak_consumption?.toFixed(1) || '0.0'} kWh</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography color="text.secondary">Lowest Day:</Typography>
                  <Typography variant="h6" color="success.main">{statistics?.minimum_consumption?.toFixed(1) || '0.0'} kWh</Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Device Breakdown Tab */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Energy Usage by Device
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={deviceBreakdown}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {deviceBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Device Consumption Details
              </Typography>
              <Box sx={{ mt: 2 }}>
                {deviceBreakdown.map((device, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography>{device.name}</Typography>
                      <Typography fontWeight="bold">{device.value}%</Typography>
                    </Box>
                    <Box sx={{ bgcolor: 'grey.200', borderRadius: 1, overflow: 'hidden' }}>
                      <Box
                        sx={{
                          bgcolor: device.color,
                          height: 8,
                          width: `${device.value}%`,
                          transition: 'width 0.3s'
                        }}
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Hourly Patterns Tab */}
      {tabValue === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Average Hourly Consumption Pattern
              </Typography>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={hourlyPattern}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#1976d2" name="Avg Consumption (kWh)" />
                </BarChart>
              </ResponsiveContainer>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                * Demo data - Connect InfluxDB to analyze your actual consumption patterns
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Container>
  )
}

export default Analytics
