import BoltIcon from '@mui/icons-material/Bolt'
import OpacityIcon from '@mui/icons-material/Opacity'
import PeopleIcon from '@mui/icons-material/People'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import {
  Box,
  Card, CardContent,
  Chip,
  Container,
  Grid,
  LinearProgress,
  Paper,
  Typography
} from '@mui/material'
import { useEffect, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

function RealTime() {
  const [currentReading, setCurrentReading] = useState({
    consumption: 75.5,
    temperature: 22.5,
    humidity: 45.0,
    occupancy: 15,
    timestamp: new Date().toISOString()
  })

  const [recentData, setRecentData] = useState([
    { time: '10:00', value: 72.3 },
    { time: '10:05', value: 74.1 },
    { time: '10:10', value: 73.8 },
    { time: '10:15', value: 75.5 },
    { time: '10:20', value: 76.2 },
    { time: '10:25', value: 75.9 },
    { time: '10:30', value: 75.5 },
  ])

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      const newReading = {
        consumption: 70 + Math.random() * 15,
        temperature: 20 + Math.random() * 5,
        humidity: 40 + Math.random() * 20,
        occupancy: Math.floor(10 + Math.random() * 10),
        timestamp: now.toISOString()
      }

      setCurrentReading(newReading)

      setRecentData(prev => {
        const newData = [...prev.slice(1), {
          time: now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          value: newReading.consumption
        }]
        return newData
      })
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [])

  const getConsumptionLevel = (value) => {
    if (value < 60) return { color: 'success', label: 'Low' }
    if (value < 80) return { color: 'warning', label: 'Normal' }
    return { color: 'error', label: 'High' }
  }

  const consumptionLevel = getConsumptionLevel(currentReading.consumption)

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Real-Time Monitoring
          </Typography>
          <Typography color="text.secondary">
            Live energy consumption data (simulated demo)
          </Typography>
        </Box>
        <Chip
          label={`Last updated: ${new Date(currentReading.timestamp).toLocaleTimeString()}`}
          color="info"
          size="small"
        />
      </Box>

      <Grid container spacing={3}>
        {/* Current Consumption */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ bgcolor: consumptionLevel.color + '.light' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BoltIcon sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Current Consumption
                </Typography>
              </Box>
              <Typography variant="h3" component="div">
                {currentReading.consumption.toFixed(1)}
              </Typography>
              <Typography variant="caption">kWh</Typography>
              <Box sx={{ mt: 1 }}>
                <Chip label={consumptionLevel.label} color={consumptionLevel.color} size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Temperature */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ThermostatIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Temperature
                </Typography>
              </Box>
              <Typography variant="h3" component="div">
                {currentReading.temperature.toFixed(1)}
              </Typography>
              <Typography variant="caption">°C</Typography>
              <LinearProgress
                variant="determinate"
                value={(currentReading.temperature / 30) * 100}
                sx={{ mt: 1 }}
                color="info"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Humidity */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <OpacityIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Humidity
                </Typography>
              </Box>
              <Typography variant="h3" component="div">
                {currentReading.humidity.toFixed(0)}
              </Typography>
              <Typography variant="caption">%</Typography>
              <LinearProgress
                variant="determinate"
                value={currentReading.humidity}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Occupancy */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PeopleIcon sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Occupancy
                </Typography>
              </Box>
              <Typography variant="h3" component="div">
                {currentReading.occupancy}
              </Typography>
              <Typography variant="caption">people</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Live Consumption Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Live Consumption Trend (Last 30 Minutes)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={recentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[60, 90]} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#1976d2"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                  name="Consumption (kWh)"
                />
              </LineChart>
            </ResponsiveContainer>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              * Demo mode - data is simulated. Connect to InfluxDB for real sensor data.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  )
}

export default RealTime
