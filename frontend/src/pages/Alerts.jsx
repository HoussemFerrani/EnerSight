import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Box,
  Button,
  ButtonGroup,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Error as ErrorIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { alertsAPI } from '../services/alertService';
import { AlertsSkeleton } from '../components/LoadingSkeleton';
import { NoAlertsEmptyState } from '../components/EmptyState';
import ErrorMessage from '../components/ErrorMessage';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, acknowledged, resolved

  useEffect(() => {
    fetchAlerts();
    fetchSummary();
  }, [filter]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const statusFilter = filter === 'all' ? null : filter;
      const data = await alertsAPI.getAlerts(statusFilter);
      setAlerts(data);
      setError(null);
    } catch (err) {
      setError('Failed to load alerts: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const data = await alertsAPI.getSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load summary:', err);
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await alertsAPI.acknowledgeAlert(alertId);
      fetchAlerts();
      fetchSummary();
    } catch (err) {
      setError('Failed to acknowledge alert: ' + err.message);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await alertsAPI.resolveAlert(alertId);
      fetchAlerts();
      fetchSummary();
    } catch (err) {
      setError('Failed to resolve alert: ' + err.message);
    }
  };

  const handleDelete = async (alertId) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      try {
        await alertsAPI.deleteAlert(alertId);
        fetchAlerts();
        fetchSummary();
      } catch (err) {
        setError('Failed to delete alert: ' + err.message);
      }
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
        return <InfoIcon color="info" />;
      default:
        return <NotificationsIcon />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'resolved':
        return 'success';
      case 'acknowledged':
        return 'info';
      case 'sent':
        return 'warning';
      case 'pending':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" alignItems="center" mb={3}>
        <NotificationsIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Alerts & Notifications
        </Typography>
      </Box>

      {error && (
        <ErrorMessage
          severity="error"
          title="Error Loading Alerts"
          message={error}
          onRetry={fetchAlerts}
          onClose={() => setError(null)}
        />
      )}

      {loading ? (
        <AlertsSkeleton />
      ) : (
        <>
          {/* Summary Cards */}
          {summary && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Alerts
                </Typography>
                <Typography variant="h4">{summary.total_alerts}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Pending
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {summary.pending_alerts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Critical
                </Typography>
                <Typography variant="h4" color="error.main">
                  {summary.critical_alerts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Unacknowledged
                </Typography>
                <Typography variant="h4" color="primary.main">
                  {summary.unacknowledged_alerts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Today
                </Typography>
                <Typography variant="h4">{summary.alerts_today}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filter Buttons */}
      <Box sx={{ mb: 3 }}>
        <ButtonGroup variant="outlined">
          <Button
            variant={filter === 'all' ? 'contained' : 'outlined'}
            onClick={() => setFilter('all')}
          >
            All
          </Button>
          <Button
            variant={filter === 'pending' ? 'contained' : 'outlined'}
            onClick={() => setFilter('pending')}
          >
            Pending
          </Button>
          <Button
            variant={filter === 'acknowledged' ? 'contained' : 'outlined'}
            onClick={() => setFilter('acknowledged')}
          >
            Acknowledged
          </Button>
          <Button
            variant={filter === 'resolved' ? 'contained' : 'outlined'}
            onClick={() => setFilter('resolved')}
          >
            Resolved
          </Button>
        </ButtonGroup>
      </Box>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <NoAlertsEmptyState onRefresh={fetchAlerts} />
      ) : (
        <Grid container spacing={2}>
          {alerts.map((alert) => (
            <Grid item xs={12} key={alert.id}>
              <Paper sx={{ p: 2 }}>
                <Box display="flex" alignItems="flex-start">
                  <Box sx={{ mr: 2, mt: 0.5 }}>{getSeverityIcon(alert.severity)}</Box>
                  <Box flexGrow={1}>
                    <Box display="flex" alignItems="center" mb={1}>
                      <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        {alert.title}
                      </Typography>
                      <Chip
                        label={alert.severity.toUpperCase()}
                        color={getSeverityColor(alert.severity)}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Chip
                        label={alert.status.toUpperCase()}
                        color={getStatusColor(alert.status)}
                        size="small"
                      />
                    </Box>

                    <Typography variant="body1" color="textSecondary" paragraph>
                      {alert.message}
                    </Typography>

                    {(alert.current_value || alert.threshold_value) && (
                      <Box sx={{ mb: 1 }}>
                        {alert.current_value && (
                          <Typography variant="body2">
                            <strong>Current:</strong> {alert.current_value.toFixed(2)} kWh
                          </Typography>
                        )}
                        {alert.threshold_value && (
                          <Typography variant="body2">
                            <strong>Threshold:</strong> {alert.threshold_value.toFixed(2)} kWh
                          </Typography>
                        )}
                      </Box>
                    )}

                    <Divider sx={{ my: 1 }} />

                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="caption" color="textSecondary">
                          Created: {formatDate(alert.created_at)}
                        </Typography>
                        {alert.acknowledged_at && (
                          <>
                            {' • '}
                            <Typography variant="caption" color="textSecondary">
                              Acknowledged: {formatDate(alert.acknowledged_at)}
                            </Typography>
                          </>
                        )}
                      </Box>

                      <Box>
                        {alert.status === 'pending' && (
                          <Button
                            size="small"
                            startIcon={<CheckIcon />}
                            onClick={() => handleAcknowledge(alert.id)}
                            sx={{ mr: 1 }}
                          >
                            Acknowledge
                          </Button>
                        )}
                        {alert.status !== 'resolved' && (
                          <Button
                            size="small"
                            startIcon={<CancelIcon />}
                            onClick={() => handleResolve(alert.id)}
                            color="success"
                            sx={{ mr: 1 }}
                          >
                            Resolve
                          </Button>
                        )}
                        <Tooltip title="Delete alert">
                          <IconButton
                            size="small"
                            onClick={() => handleDelete(alert.id)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      )}
        </>
      )}
    </Container>
  );
};

export default Alerts;
