import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import {
  Inbox as InboxIcon,
  DataUsage as DataIcon,
  Warning as WarningIcon,
  CloudOff as CloudOffIcon,
  BatteryAlert as BatteryAlertIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';

/**
 * Generic empty state component
 */
const EmptyState = ({
  icon: Icon = InboxIcon,
  title = 'No Data Available',
  description = 'There is no data to display at the moment.',
  actionLabel,
  onAction,
  image,
}) => {
  return (
    <Paper
      sx={{
        p: 6,
        textAlign: 'center',
        backgroundColor: 'background.default',
        border: '2px dashed',
        borderColor: 'divider',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
        }}
      >
        {image ? (
          <img src={image} alt="Empty state" style={{ width: 200, height: 200, opacity: 0.5 }} />
        ) : (
          <Icon sx={{ fontSize: 80, color: 'text.disabled' }} />
        )}
        <Typography variant="h5" color="text.primary" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 500 }}>
          {description}
        </Typography>
        {actionLabel && onAction && (
          <Button variant="contained" onClick={onAction} sx={{ mt: 2 }}>
            {actionLabel}
          </Button>
        )}
      </Box>
    </Paper>
  );
};

/**
 * Empty state for no alerts
 */
export const NoAlertsEmptyState = ({ onRefresh }) => {
  return (
    <EmptyState
      icon={BatteryAlertIcon}
      title="No Alerts"
      description="You're all caught up! There are no active alerts at the moment. Your energy consumption is within normal parameters."
      actionLabel="Refresh"
      onAction={onRefresh}
    />
  );
};

/**
 * Empty state for no analytics data
 */
export const NoDataEmptyState = ({ onRefresh }) => {
  return (
    <EmptyState
      icon={DataIcon}
      title="No Data Available"
      description="No energy consumption data found for the selected period. Try adjusting your date range or check if the data collection is properly configured."
      actionLabel="Refresh"
      onAction={onRefresh}
    />
  );
};

/**
 * Empty state for no anomalies
 */
export const NoAnomaliesEmptyState = ({ onRefresh }) => {
  return (
    <EmptyState
      icon={AssessmentIcon}
      title="No Anomalies Detected"
      description="Great news! No unusual patterns or anomalies have been detected in your energy consumption. Your system is running normally."
      actionLabel="Refresh"
      onAction={onRefresh}
    />
  );
};

/**
 * Empty state for disconnected state
 */
export const DisconnectedEmptyState = ({ onRetry }) => {
  return (
    <EmptyState
      icon={CloudOffIcon}
      title="Connection Lost"
      description="Unable to connect to the server. Please check your internet connection or try again later."
      actionLabel="Retry"
      onAction={onRetry}
    />
  );
};

/**
 * Empty state for errors
 */
export const ErrorEmptyState = ({ title, message, onRetry }) => {
  return (
    <EmptyState
      icon={WarningIcon}
      title={title || 'Something Went Wrong'}
      description={message || 'An unexpected error occurred. Please try again or contact support if the problem persists.'}
      actionLabel="Try Again"
      onAction={onRetry}
    />
  );
};

/**
 * Empty state for search results
 */
export const NoSearchResultsEmptyState = ({ searchTerm, onClear }) => {
  return (
    <EmptyState
      icon={InboxIcon}
      title="No Results Found"
      description={`No results found for "${searchTerm}". Try adjusting your search criteria.`}
      actionLabel="Clear Search"
      onAction={onClear}
    />
  );
};

/**
 * Empty state for predictions
 */
export const NoPredictionsEmptyState = ({ onGenerate }) => {
  return (
    <EmptyState
      icon={AssessmentIcon}
      title="No Predictions Available"
      description="No energy consumption predictions have been generated yet. Generate predictions to see forecasts for future consumption."
      actionLabel="Generate Predictions"
      onAction={onGenerate}
    />
  );
};

export default EmptyState;
