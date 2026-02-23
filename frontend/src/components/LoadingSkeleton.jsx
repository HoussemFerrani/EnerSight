import React from 'react';
import { Skeleton, Grid, Card, CardContent, Box, Paper } from '@mui/material';

/**
 * Loading skeleton for the dashboard
 */
export const DashboardSkeleton = () => {
  return (
    <Box sx={{ mt: 4, mb: 4 }}>
      {/* Header Skeleton */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Skeleton variant="text" width={300} height={50} />
        <Skeleton variant="rectangular" width={150} height={32} sx={{ borderRadius: 2 }} />
      </Box>

      {/* Live Data Card Skeleton */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Skeleton variant="text" width={200} height={30} />
        <Grid container spacing={2} sx={{ mt: 1 }}>
          {[1, 2, 3, 4].map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item}>
              <Skeleton variant="text" width={100} height={20} />
              <Skeleton variant="text" width={150} height={60} />
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Stats Cards Skeleton */}
      <Grid container spacing={3}>
        {[1, 2, 3, 4].map((item) => (
          <Grid item xs={12} md={3} key={item}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="80%" height={30} />
                <Skeleton variant="text" width="60%" height={60} />
                <Skeleton variant="text" width="40%" height={20} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Chart Skeleton */}
      <Box sx={{ mt: 3 }}>
        <Paper sx={{ p: 3 }}>
          <Skeleton variant="text" width={200} height={30} sx={{ mb: 2 }} />
          <Skeleton variant="rectangular" width="100%" height={300} />
        </Paper>
      </Box>
    </Box>
  );
};

/**
 * Loading skeleton for analytics page
 */
export const AnalyticsSkeleton = () => {
  return (
    <Box sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Skeleton variant="text" width={250} height={50} />
        <Skeleton variant="rectangular" width={150} height={40} sx={{ borderRadius: 1 }} />
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          {[1, 2, 3, 4, 5].map((item) => (
            <Grid item xs={12} sm={6} md={2.4} key={item}>
              <Skeleton variant="rectangular" width="100%" height={56} sx={{ borderRadius: 1 }} />
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {[1, 2, 3, 4].map((item) => (
          <Grid item xs={12} sm={6} md={3} key={item}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="70%" />
                <Skeleton variant="text" width="50%" height={50} />
                <Skeleton variant="text" width="60%" />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Chart */}
      <Paper sx={{ p: 3 }}>
        <Skeleton variant="text" width={200} height={30} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" width="100%" height={300} />
      </Paper>
    </Box>
  );
};

/**
 * Loading skeleton for alerts page
 */
export const AlertsSkeleton = () => {
  return (
    <Box sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Skeleton variant="text" width={200} height={50} sx={{ mb: 3 }} />

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {[1, 2, 3, 4, 5].map((item) => (
          <Grid item xs={12} sm={6} md={2.4} key={item}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="80%" />
                <Skeleton variant="text" width="60%" height={50} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Alert Items */}
      {[1, 2, 3].map((item) => (
        <Paper key={item} sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="text" width="40%" height={30} />
              <Skeleton variant="text" width="80%" />
              <Skeleton variant="text" width="60%" />
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Skeleton variant="rectangular" width={100} height={36} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={100} height={36} sx={{ borderRadius: 1 }} />
            </Box>
          </Box>
        </Paper>
      ))}
    </Box>
  );
};

/**
 * Generic table skeleton
 */
export const TableSkeleton = ({ rows = 5, columns = 4 }) => {
  return (
    <Box>
      {/* Table Header */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        {Array.from({ length: columns }).map((_, idx) => (
          <Skeleton key={idx} variant="text" width={`${100 / columns}%`} height={40} />
        ))}
      </Box>

      {/* Table Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <Box key={rowIdx} sx={{ display: 'flex', gap: 2, mb: 1 }}>
          {Array.from({ length: columns }).map((_, colIdx) => (
            <Skeleton key={colIdx} variant="text" width={`${100 / columns}%`} height={30} />
          ))}
        </Box>
      ))}
    </Box>
  );
};

/**
 * Card skeleton
 */
export const CardSkeleton = () => {
  return (
    <Card>
      <CardContent>
        <Skeleton variant="text" width="80%" height={30} />
        <Skeleton variant="text" width="60%" height={60} sx={{ my: 1 }} />
        <Skeleton variant="text" width="50%" />
      </CardContent>
    </Card>
  );
};

export default {
  DashboardSkeleton,
  AnalyticsSkeleton,
  AlertsSkeleton,
  TableSkeleton,
  CardSkeleton,
};
