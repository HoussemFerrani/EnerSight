import React from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Paper,
  useTheme,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  ShowChart as ShowChartIcon,
  Warning as WarningIcon,
  Notifications as NotificationsIcon,
  Speed as SpeedIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const Welcome = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const features = [
    {
      icon: <DashboardIcon sx={{ fontSize: 40 }} />,
      title: 'Real-Time Monitoring',
      description: 'Monitor your energy consumption in real-time with live WebSocket updates and instant notifications.',
      link: '/realtime',
      color: '#1976d2',
    },
    {
      icon: <ShowChartIcon sx={{ fontSize: 40 }} />,
      title: 'Advanced Analytics',
      description: 'Analyze historical data with powerful aggregation, cost calculation, and period comparison features.',
      link: '/analytics',
      color: '#9c27b0',
    },
    {
      icon: <AssessmentIcon sx={{ fontSize: 40 }} />,
      title: 'Smart Predictions',
      description: 'ML-powered forecasting using LSTM neural networks to predict future energy consumption patterns.',
      link: '/predictions',
      color: '#f57c00',
    },
    {
      icon: <WarningIcon sx={{ fontSize: 40 }} />,
      title: 'Anomaly Detection',
      description: 'Automatically detect unusual consumption patterns and potential issues before they become problems.',
      link: '/anomalies',
      color: '#d32f2f',
    },
    {
      icon: <NotificationsIcon sx={{ fontSize: 40 }} />,
      title: 'Smart Alerts',
      description: 'Get notified via email when consumption exceeds thresholds or anomalies are detected.',
      link: '/alerts',
      color: '#00796b',
    },
    {
      icon: <SpeedIcon sx={{ fontSize: 40 }} />,
      title: 'Live Dashboard',
      description: 'Beautiful, responsive dashboard with real-time metrics, charts, and system status indicators.',
      link: '/',
      color: '#5e35b1',
    },
  ];

  const stats = [
    { label: 'Real-Time Updates', value: 'Every 5s', icon: <SpeedIcon /> },
    { label: 'ML Accuracy', value: '95%+', icon: <TrendingUpIcon /> },
    { label: 'Data Points', value: '1M+', icon: <AssessmentIcon /> },
    { label: 'Secure', value: 'JWT Auth', icon: <SecurityIcon /> },
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Hero Section */}
      <Paper
        sx={{
          p: 6,
          mb: 4,
          background: theme.palette.mode === 'dark'
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
            Welcome to EnerSight
          </Typography>
          <Typography variant="h5" sx={{ mb: 3, opacity: 0.9 }}>
            AI-Powered Energy Monitoring & Analytics Platform
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, maxWidth: 800, mx: 'auto', opacity: 0.9 }}>
            Monitor, analyze, and optimize your energy consumption with advanced machine learning,
            real-time alerts, and comprehensive analytics. Make data-driven decisions to reduce costs
            and improve efficiency.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/')}
              sx={{
                backgroundColor: 'white',
                color: 'primary.main',
                '&:hover': { backgroundColor: 'rgba(255,255,255,0.9)' },
              }}
            >
              View Dashboard
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/realtime')}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': { borderColor: 'white', backgroundColor: 'rgba(255,255,255,0.1)' },
              }}
            >
              Start Monitoring
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Stats Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ textAlign: 'center', p: 2 }}>
              <Box sx={{ color: 'primary.main', mb: 1 }}>{stat.icon}</Box>
              <Typography variant="h4" color="primary" gutterBottom>
                {stat.value}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stat.label}
              </Typography>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Features Section */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h2" gutterBottom textAlign="center" fontWeight="bold">
          Platform Features
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 4 }}>
          Everything you need to monitor and optimize your energy consumption
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: `${feature.color}15`,
                    color: feature.color,
                    mb: 2,
                  }}
                >
                  {feature.icon}
                </Box>
                <Typography variant="h6" component="h3" gutterBottom fontWeight="bold">
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ p: 2, pt: 0 }}>
                <Button
                  size="small"
                  onClick={() => navigate(feature.link)}
                  sx={{ color: feature.color }}
                >
                  Explore →
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Technology Stack */}
      <Paper sx={{ p: 4, mt: 4 }}>
        <Typography variant="h5" component="h3" gutterBottom textAlign="center" fontWeight="bold">
          Powered By Advanced Technology
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap', mt: 3 }}>
          {['React', 'FastAPI', 'PostgreSQL', 'InfluxDB', 'TensorFlow', 'LSTM', 'WebSocket', 'JWT Auth', 'Material-UI', 'Recharts'].map(
            (tech) => (
              <Chip
                key={tech}
                label={tech}
                variant="outlined"
                color="primary"
                sx={{ fontWeight: 500 }}
              />
            )
          )}
        </Box>
      </Paper>

      {/* Call to Action */}
      <Box sx={{ textAlign: 'center', mt: 4, p: 4 }}>
        <Typography variant="h5" gutterBottom>
          Ready to get started?
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Explore the dashboard and discover how EnerSight can help you optimize your energy usage
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={() => navigate('/')}
          startIcon={<DashboardIcon />}
        >
          Go to Dashboard
        </Button>
      </Box>
    </Container>
  );
};

export default Welcome;
