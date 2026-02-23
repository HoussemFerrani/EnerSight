import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import { Alert, Box, Chip, Container, Grid, Paper, Typography, Tooltip } from '@mui/material'
import { useEffect, useState } from 'react'
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip as RechartsTooltip, XAxis, YAxis } from 'recharts'
import { useMockLiveData } from '../hooks/useMockLiveData'
import { useWebSocket } from '../hooks/useWebSocket'
import { energyAPI, systemAPI } from '../services/api'
import { DashboardSkeleton } from '../components/LoadingSkeleton'
import ErrorMessage from '../components/ErrorMessage'

function Dashboard() {
  const [statistics, setStatistics] = useState(null)
  const [healthStatus, setHealthStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // WebSocket for live data (if backend is running)
  const wsUrl = `ws://localhost:8000/api/v1/ws/energy/live`
  const { data: wsData, isConnected: isLiveConnected } = useWebSocket(wsUrl, {
    autoConnect: true,
    reconnectAttempts: 3,
    onConnect: () => console.log('📡 Connected to real backend WebSocket'),
    onDisconnect: () => console.log('📡 Backend WebSocket disconnected'),
  })

  // Mock data generator (works WITHOUT backend - auto-start if WebSocket not connected)
  const { data: mockData, isActive: isMockActive } = useMockLiveData({
    updateInterval: 5000,
    autoStart: true, // Always generates data
  })

  // Use WebSocket data if available, otherwise use mock data
  const liveData = isLiveConnected ? wsData : mockData
  const dataMode = isLiveConnected ? 'real-backend' : 'mock-frontend'

  // Mock chart data (will be replaced with real data when InfluxDB is connected)
  const mockChartData = [
    { time: '00:00', consumption: 45.2, renewable: 5.0 },
    { time: '04:00', consumption: 38.5, renewable: 3.2 },
    { time: '08:00', consumption: 72.3, renewable: 15.5 },
    { time: '12:00', consumption: 85.7, renewable: 22.8 },
    { time: '16:00', consumption: 78.4, renewable: 18.3 },
    { time: '20:00', consumption: 65.1, renewable: 8.5 },
  ]

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)

      // Fetch statistics
      const statsResponse = await energyAPI.getStatistics('week')
      setStatistics(statsResponse.data)

      // Fetch health status
      const healthResponse = await systemAPI.getHealth()
      setHealthStatus(healthResponse.data)

      setError(null)
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
      setError(err.response?.data?.detail || 'Failed to load dashboard data. Using demo mode.')

      // Set mock data for demo
      setStatistics({
        total_consumption: 1245.80,
        average_daily: 41.53,
        peak_consumption: 62.30,
        minimum_consumption: 28.40,
        days: 7
      })
      setHealthStatus({
        status: 'demo',
        components: {
          api: 'operational',
          influxdb: 'not_configured',
          postgresql: 'not_configured'
        }
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <DashboardSkeleton />
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Energy Monitoring Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {liveData && (
            <Chip
              icon={<FiberManualRecordIcon sx={{ animation: 'pulse 2s infinite' }} />}
              label={isLiveConnected ? 'Live (Backend)' : 'Live (Demo)'}
              color={isLiveConnected ? 'success' : 'warning'}
              size="small"
              sx={{
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.5 },
                },
              }}
            />
          )}
          {healthStatus && (
            <Chip
              label={healthStatus.status === 'healthy' || healthStatus.status === 'demo' ? 'System Online' : 'System Degraded'}
              color={healthStatus.status === 'healthy' || healthStatus.status === 'demo' ? 'success' : 'warning'}
              size="small"
            />
          )}
        </Box>
      </Box>

      {error && (
        <ErrorMessage
          severity="info"
          title="Demo Mode"
          message={error}
          onClose={() => setError(null)}
        />
      )}

      {!isLiveConnected && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Running in demo mode with simulated live data. Start the backend to see real WebSocket data.
        </Alert>
      )}

      {/* Live Data Card (Real-time) */}
      {liveData && (
        <Paper sx={{ p: 3, mb: 3, background: isLiveConnected ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              ⚡ Real-time Consumption
            </Typography>
            <Chip
              label={isLiveConnected ? 'Backend WebSocket' : 'Browser Simulation'}
              size="small"
              sx={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption">Current Power</Typography>
              <Typography variant="h4">{liveData.consumption} kWh</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption">Voltage</Typography>
              <Typography variant="h5">{liveData.voltage} V</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption">Temperature</Typography>
              <Typography variant="h5">{liveData.temperature}°C</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption">Cost (Real-time)</Typography>
              <Typography variant="h5">${liveData.cost}</Typography>
            </Grid>
          </Grid>
          <Typography variant="caption" sx={{ mt: 2, display: 'block', opacity: 0.8 }}>
            Last updated: {new Date(liveData.timestamp).toLocaleTimeString()} {!isLiveConnected && '(Demo)'}
          </Typography>
        </Paper>
      )}

      <Grid container spacing={3}>
        {/* Total Consumption Card */}
        <Grid item xs={12} md={3}>
          <Tooltip title="Total energy consumed over the past 7 days" arrow placement="top">
            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140, cursor: 'help' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Total (7 Days)
              </Typography>
              <Typography variant="h3" component="div">
                {statistics?.total_consumption?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">kWh</Typography>
            </Paper>
          </Tooltip>
        </Grid>

        {/* Average Daily Card */}
        <Grid item xs={12} md={3}>
          <Tooltip title="Average energy consumption per day" arrow placement="top">
            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140, cursor: 'help' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Daily Average
              </Typography>
              <Typography variant="h3" component="div">
                {statistics?.average_daily?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">kWh/day</Typography>
            </Paper>
          </Tooltip>
        </Grid>

        {/* Peak Consumption Card */}
        <Grid item xs={12} md={3}>
          <Tooltip title="Highest energy consumption recorded in the period" arrow placement="top">
            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140, cursor: 'help' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" color="text.secondary">
                  Peak
                </Typography>
                <TrendingUpIcon color="error" sx={{ ml: 1 }} />
              </Box>
              <Typography variant="h3" component="div" color="error.main">
                {statistics?.peak_consumption?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">kWh</Typography>
            </Paper>
          </Tooltip>
        </Grid>

        {/* Minimum Consumption Card */}
        <Grid item xs={12} md={3}>
          <Tooltip title="Lowest energy consumption recorded in the period" arrow placement="top">
            <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140, cursor: 'help' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" color="text.secondary">
                  Minimum
                </Typography>
                <TrendingDownIcon color="success" sx={{ ml: 1 }} />
              </Box>
              <Typography variant="h3" component="div" color="success.main">
                {statistics?.minimum_consumption?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">kWh</Typography>
            </Paper>
          </Tooltip>
        </Grid>

        {/* Consumption Trend Chart */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Energy Consumption Trend
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={mockChartData}>
                <defs>
                  <linearGradient id="colorConsumption" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1976d2" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#1976d2" stopOpacity={0.1} />
                  </linearGradient>
                  <linearGradient id="colorRenewable" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4caf50" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#4caf50" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="consumption" stroke="#1976d2" fillOpacity={1} fill="url(#colorConsumption)" name="Consumption (kWh)" />
                <Area type="monotone" dataKey="renewable" stroke="#4caf50" fillOpacity={1} fill="url(#colorRenewable)" name="Renewable (kWh)" />
              </AreaChart>
            </ResponsiveContainer>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              * Demo data - Connect InfluxDB to see real-time trends
            </Typography>
          </Paper>
        </Grid>

        {/* System Status */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            {healthStatus && (
              <Box sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">API</Typography>
                  <Chip label={healthStatus.components.api} color="success" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">InfluxDB</Typography>
                  <Chip
                    label={healthStatus.components.influxdb || 'not_configured'}
                    color={healthStatus.components.influxdb === 'connected' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">PostgreSQL</Typography>
                  <Chip
                    label={healthStatus.components.postgresql || 'not_configured'}
                    color={healthStatus.components.postgresql === 'connected' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
                <Box sx={{ mt: 3 }}>
                  <Typography variant="caption" color="text.secondary">
                    Version: {healthStatus.version || '1.0.0'}
                  </Typography>
                  <br />
                  <Typography variant="caption" color="text.secondary">
                    Environment: {healthStatus.environment || 'development'}
                  </Typography>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  )
}

export default Dashboard
