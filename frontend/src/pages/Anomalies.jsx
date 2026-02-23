import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import RefreshIcon from '@mui/icons-material/Refresh'
import WarningIcon from '@mui/icons-material/Warning'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  FormControl, InputLabel,
  MenuItem,
  Paper,
  Select,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Typography
} from '@mui/material'
import { useEffect, useState } from 'react'
import { anomaliesAPI } from '../services/api'

function Anomalies() {
  const [anomalies, setAnomalies] = useState([])
  const [hours, setHours] = useState(24)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    detectAnomalies()
  }, [])

  const detectAnomalies = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await anomaliesAPI.detect(hours)
      setAnomalies(response.data.anomalies || [])
    } catch (err) {
      console.error('Anomaly detection error:', err)
      setError(err.response?.data?.detail || 'Anomaly detection failed. Database or ML model may not be configured.')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    detectAnomalies()
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Anomaly Detection
          </Typography>
          <Typography color="text.secondary">
            Unusual energy consumption patterns and alerts
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Time Period</InputLabel>
            <Select
              value={hours}
              label="Time Period"
              onChange={(e) => setHours(e.target.value)}
            >
              <MenuItem value={6}>Last 6 hours</MenuItem>
              <MenuItem value={12}>Last 12 hours</MenuItem>
              <MenuItem value={24}>Last 24 hours</MenuItem>
              <MenuItem value={48}>Last 48 hours</MenuItem>
              <MenuItem value={168}>Last 7 days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            {loading ? 'Scanning...' : 'Scan for Anomalies'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
            <CircularProgress size={60} />
          </Box>
        ) : anomalies.length === 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
            <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Anomalies Detected
            </Typography>
            <Typography color="text.secondary">
              All energy consumption patterns are within normal ranges for the past {hours} hours.
            </Typography>
          </Box>
        ) : (
          <>
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
              <WarningIcon color="warning" />
              <Typography variant="h6">
                {anomalies.length} Anomal{anomalies.length === 1 ? 'y' : 'ies'} Detected
              </Typography>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Device</TableCell>
                    <TableCell align="right">Consumption</TableCell>
                    <TableCell align="right">Expected</TableCell>
                    <TableCell align="right">Anomaly Score</TableCell>
                    <TableCell>Severity</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {anomalies.map((anomaly, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        {new Date(anomaly.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>{anomaly.device_id || 'N/A'}</TableCell>
                      <TableCell align="right">
                        {anomaly.consumption?.toFixed(2)} kWh
                      </TableCell>
                      <TableCell align="right">
                        {anomaly.expected_consumption?.toFixed(2)} kWh
                      </TableCell>
                      <TableCell align="right">
                        {(anomaly.anomaly_score * 100).toFixed(0)}%
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={anomaly.severity}
                          color={
                            anomaly.severity === 'high' ? 'error' :
                              anomaly.severity === 'medium' ? 'warning' : 'info'
                          }
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </Paper>

      <Box sx={{ mt: 3 }}>
        <Alert severity="info">
          <Typography variant="body2">
            <strong>About Anomaly Detection:</strong> This system uses an Isolation Forest algorithm to identify unusual energy consumption patterns.
            Anomalies may indicate equipment malfunction, inefficient device behavior, or unusual usage patterns.
            Configure InfluxDB and load the anomaly detector model to enable real-time anomaly detection.
          </Typography>
        </Alert>
      </Box>
    </Container>
  )
}

export default Anomalies
