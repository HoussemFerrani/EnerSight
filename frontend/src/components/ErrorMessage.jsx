import {
  Close as CloseIcon,
  ErrorOutline as ErrorIcon,
  InfoOutlined as InfoIcon,
  CheckCircleOutline as SuccessIcon,
  WarningAmber as WarningIcon,
} from '@mui/icons-material';
import { Alert, AlertTitle, Box, Button, Collapse, IconButton } from '@mui/material';
import React from 'react';

/**
 * Enhanced error message component with better UX
 */
const ErrorMessage = ({
  severity = 'error',
  title,
  message,
  details,
  onRetry,
  onClose,
  retryLabel = 'Try Again',
  persistent = false,
  sx = {},
}) => {
  const [open, setOpen] = React.useState(true);
  const [showDetails, setShowDetails] = React.useState(false);

  const handleClose = () => {
    if (!persistent) {
      setOpen(false);
      if (onClose) {
        onClose();
      }
    }
  };

  const getIcon = () => {
    switch (severity) {
      case 'error':
        return <ErrorIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'info':
        return <InfoIcon />;
      case 'success':
        return <SuccessIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const getUserFriendlyMessage = (message) => {
    // Map common error messages to user-friendly versions
    const errorMap = {
      'Network Error': 'Unable to connect to the server. Please check your internet connection.',
      'Request failed with status code 401': 'Your session has expired. Please log in again.',
      'Request failed with status code 403': 'You do not have permission to perform this action.',
      'Request failed with status code 404': 'The requested resource was not found.',
      'Request failed with status code 500': 'A server error occurred. Please try again later.',
      'timeout': 'The request took too long to complete. Please try again.',
    };

    // Check if message matches any known patterns
    for (const [key, value] of Object.entries(errorMap)) {
      if (message?.toLowerCase().includes(key.toLowerCase())) {
        return value;
      }
    }

    return message;
  };

  return (
    <Collapse in={open}>
      <Alert
        severity={severity}
        icon={getIcon()}
        action={
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {onRetry && (
              <Button color="inherit" size="small" onClick={onRetry}>
                {retryLabel}
              </Button>
            )}
            {!persistent && (
              <IconButton
                aria-label="close"
                color="inherit"
                size="small"
                onClick={handleClose}
              >
                <CloseIcon fontSize="inherit" />
              </IconButton>
            )}
          </Box>
        }
        sx={{ mb: 2, ...sx }}
      >
        {title && <AlertTitle>{title}</AlertTitle>}
        {getUserFriendlyMessage(message)}

        {details && (
          <Box sx={{ mt: 1 }}>
            <Button
              size="small"
              onClick={() => setShowDetails(!showDetails)}
              sx={{ p: 0, minWidth: 'auto', textTransform: 'none' }}
            >
              {showDetails ? 'Hide' : 'Show'} details
            </Button>
            <Collapse in={showDetails}>
              <Box
                sx={{
                  mt: 1,
                  p: 1,
                  backgroundColor: 'rgba(0,0,0,0.05)',
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.85rem',
                  wordBreak: 'break-word',
                }}
              >
                {details}
              </Box>
            </Collapse>
          </Box>
        )}
      </Alert>
    </Collapse>
  );
};

/**
 * Quick error toast for brief messages
 */
export const ErrorToast = ({ message, onClose }) => {
  React.useEffect(() => {
    if (onClose) {
      const timer = setTimeout(onClose, 5000);
      return () => clearTimeout(timer);
    }
  }, [onClose]);

  return (
    <ErrorMessage
      severity="error"
      message={message}
      onClose={onClose}
      sx={{
        position: 'fixed',
        top: 80,
        right: 20,
        zIndex: 9999,
        minWidth: 300,
        boxShadow: 4,
      }}
    />
  );
};

/**
 * Success message component
 */
export const SuccessMessage = ({ message, onClose, autoHide = true }) => {
  React.useEffect(() => {
    if (autoHide && onClose) {
      const timer = setTimeout(onClose, 4000);
      return () => clearTimeout(timer);
    }
  }, [autoHide, onClose]);

  return (
    <ErrorMessage
      severity="success"
      message={message}
      onClose={onClose}
    />
  );
};

export default ErrorMessage;
