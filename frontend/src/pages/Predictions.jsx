import PredictIcon from '@mui/icons-material/TrendingUp'
import {
  Alert,
  Box,
  Button,
  Card, CardContent,
  CircularProgress,
  Container,
  Divider,
  Grid, Paper, TextField,
  Typography
} from '@mui/material'
import { useState } from 'react'
import { predictionsAPI } from '../services/api'

function Predictions() {
  const [formData, setFormData] = useState({
    temperature: 22.5,
    humidity: 45.0,
    occupancy: 15,
    hvac_usage: 12.5,
    lighting_usage: 3.2,
    equipment_usage: 8.7,
    renewable_energy: 5.0
  })

  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }))
  }

  const handlePredict = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await predictionsAPI.predict(formData)
      setPrediction(response.data)
    } catch (err) {
      console.error('Prediction error:', err)
      setError(err.response?.data?.detail || 'Prediction failed. ML model may not be loaded.')
    } finally {
      setLoading(false)
    }
  }

  const totalInput = formData.hvac_usage + formData.lighting_usage + formData.equipment_usage

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Energy Consumption Prediction
      </Typography>
      <Typography color="text.secondary" paragraph>
        Use machine learning to predict energy consumption based on environmental and operational factors
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Input Form */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Input Parameters
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Environmental Conditions
            </Typography>
            <TextField
              fullWidth
              label="Temperature (°C)"
              name="temperature"
              type="number"
              value={formData.temperature}
              onChange={handleInputChange}
              margin="normal"
              inputProps={{ step: 0.1, min: -50, max: 60 }}
            />
            <TextField
              fullWidth
              label="Humidity (%)"
              name="humidity"
              type="number"
              value={formData.humidity}
              onChange={handleInputChange}
              margin="normal"
              inputProps={{ step: 0.1, min: 0, max: 100 }}
            />
            <TextField
              fullWidth
              label="Occupancy (people)"
              name="occupancy"
              type="number"
              value={formData.occupancy}
              onChange={handleInputChange}
              margin="normal"
              inputProps={{ step: 1, min: 0 }}
            />

            <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mt: 3 }}>
              Energy Usage (kWh)
            </Typography>
            <TextField
              fullWidth
              label="HVAC Usage"
              name="hvac_usage"
              type="number"
              value={formData.hvac_usage}
              onChange={handleInputChange}
              margin="normal"
              inputProps={{ step: 0.1, min: 0 }}
            />
            <TextField
              fullWidth
              label="Lighting Usage"
              name="lighting_usage"
              type="number"
              value={formData.lighting_usage}
              onChange={handleInputChange}
              margin="normal"
              inputProps={{ step: 0.1, min: 0 }}
            />
            <TextField
              fullWidth
              label="Equipment Usage"
              name="equipment_usage"
              type="number"
              value={formData.equipment_usage}
              onChange={handleInputChange}
              margin="normal"
              inputProps={{ step: 0.1, min: 0 }}
            />
            <TextField
              fullWidth
              label="Renewable Energy"
              name="renewable_energy"
              type="number"
              value={formData.renewable_energy}
              onChange={handleInputChange}
              margin="normal"
              inputProps={{ step: 0.1, min: 0 }}
            />

            <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Current Total: {totalInput.toFixed(1)} kWh
              </Typography>
              <Button
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PredictIcon />}
                onClick={handlePredict}
                disabled={loading}
              >
                {loading ? 'Predicting...' : 'Predict Consumption'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Results */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Prediction Results
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {!prediction && !loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
                <Typography color="text.secondary">
                  Enter parameters and click "Predict" to see results
                </Typography>
              </Box>
            )}

            {prediction && (
              <Box>
                <Card sx={{ mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      Predicted Consumption
                    </Typography>
                    <Typography variant="h2" component="div">
                      {prediction.predicted_consumption?.toFixed(2) || '0.00'}
                    </Typography>
                    <Typography variant="body2">
                      kWh
                    </Typography>
                  </CardContent>
                </Card>

                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Model Used
                        </Typography>
                        <Typography variant="h6">
                          {prediction.model || 'Random Forest'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Confidence Score
                        </Typography>
                        <Typography variant="h6">
                          {((prediction.confidence || 0) * 100).toFixed(0)}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Analysis
                  </Typography>
                  <Typography variant="body2">
                    {prediction.predicted_consumption > totalInput
                      ? `⚠️ Predicted consumption (${prediction.predicted_consumption.toFixed(1)} kWh) is higher than current input (${totalInput.toFixed(1)} kWh). Consider optimizing energy usage.`
                      : `✓ Predicted consumption (${prediction.predicted_consumption.toFixed(1)} kWh) is in line with current input (${totalInput.toFixed(1)} kWh).`
                    }
                  </Typography>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3 }}>
        <Alert severity="info">
          <Typography variant="body2">
            <strong>Note:</strong> Predictions are generated using a Random Forest regression model trained on historical energy consumption data.
            To enable predictions, ensure ML models are loaded in the backend.
          </Typography>
        </Alert>
      </Box>
    </Container>
  )
}

export default Predictions
