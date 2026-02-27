import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import AuthCallback from './pages/AuthCallback'
import Dashboard from './pages/Dashboard'
import TrustScore from './pages/TrustScore'
import Communities from './pages/Communities'
import CommunityDashboard from './pages/CommunityDashboard'
import Loans from './pages/Loans'
import LoanApplication from './pages/LoanApplication'

function PrivateRoute({ children }) {
  const { isAuthenticated, hydrated } = useAuthStore()
  if (!hydrated) {
    return (
      <div className="min-h-screen grid place-items-center bg-slate-50">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-primary-600" />
      </div>
    )
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/auth/callback" element={<AuthCallback />} />

        <Route path="/" element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="trust-score" element={<TrustScore />} />
          <Route path="communities" element={<Communities />} />
          <Route path="communities/:id" element={<CommunityDashboard />} />
          <Route path="loans" element={<Loans />} />
          <Route path="loans/apply" element={<LoanApplication />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
