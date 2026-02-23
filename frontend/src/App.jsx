import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { ThemeProvider } from './contexts/ThemeContext'
import Alerts from './pages/Alerts'
import AnalyticsEnhanced from './pages/AnalyticsEnhanced'
import Anomalies from './pages/Anomalies'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Predictions from './pages/Predictions'
import RealTime from './pages/RealTime'
import Welcome from './pages/Welcome'

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/welcome" element={<Welcome />} />
                    <Route path="/realtime" element={<RealTime />} />
                    <Route path="/analytics" element={<AnalyticsEnhanced />} />
                    <Route path="/predictions" element={<Predictions />} />
                    <Route path="/anomalies" element={<Anomalies />} />
                    <Route path="/alerts" element={<Alerts />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
