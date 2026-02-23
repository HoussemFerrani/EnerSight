import { Navigate } from 'react-router-dom';
import { authService } from '../services/authService';

/**
 * ProtectedRoute component
 * Redirects to login if user is not authenticated
 */
function ProtectedRoute({ children }) {
  const isAuthenticated = authService.isAuthenticated();

  if (!isAuthenticated) {
    // Redirect to login page if not authenticated
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
