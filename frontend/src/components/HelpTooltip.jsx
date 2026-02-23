import React from 'react';
import { Tooltip, IconButton, Box, Typography } from '@mui/material';
import { Help as HelpIcon, Info as InfoIcon } from '@mui/icons-material';

/**
 * Informational tooltip with help icon
 */
export const HelpTooltip = ({ title, children, placement = 'top', ...props }) => {
  return (
    <Tooltip title={title} placement={placement} arrow {...props}>
      {children || (
        <IconButton size="small" sx={{ ml: 0.5 }}>
          <HelpIcon fontSize="small" />
        </IconButton>
      )}
    </Tooltip>
  );
};

/**
 * Info tooltip with info icon
 */
export const InfoTooltip = ({ title, placement = 'top' }) => {
  return (
    <Tooltip title={title} placement={placement} arrow>
      <IconButton size="small" sx={{ ml: 0.5 }}>
        <InfoIcon fontSize="small" color="info" />
      </IconButton>
    </Tooltip>
  );
};

/**
 * Label with tooltip
 */
export const LabelWithTooltip = ({ label, tooltip, required = false }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
      <Typography variant="body2" component="label">
        {label}
        {required && <span style={{ color: 'red' }}> *</span>}
      </Typography>
      {tooltip && <HelpTooltip title={tooltip} />}
    </Box>
  );
};

/**
 * Feature description with tooltip
 */
export const FeatureTooltip = ({ feature, description, children }) => {
  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
            {feature}
          </Typography>
          <Typography variant="body2">{description}</Typography>
        </Box>
      }
      arrow
      placement="top"
    >
      {children}
    </Tooltip>
  );
};

export default HelpTooltip;
