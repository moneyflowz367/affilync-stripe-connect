import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Payments from './pages/Payments'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

function App() {
  const [accountId, setAccountId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for account ID from URL params (after OAuth callback)
    const params = new URLSearchParams(window.location.search)
    const urlAccountId = params.get('account_id')
    const token = params.get('token')

    if (urlAccountId) {
      // Store in localStorage for persistence
      localStorage.setItem('stripe_connect_account_id', urlAccountId)
      if (token) {
        localStorage.setItem('stripe_connect_token', token)
      }
      setAccountId(urlAccountId)
      // Clean up URL
      window.history.replaceState({}, '', window.location.pathname)
    } else {
      // Check localStorage
      const storedAccountId = localStorage.getItem('stripe_connect_account_id')
      if (storedAccountId) {
        setAccountId(storedAccountId)
      }
    }

    setIsLoading(false)
  }, [])

  const handleDisconnect = () => {
    localStorage.removeItem('stripe_connect_account_id')
    localStorage.removeItem('stripe_connect_token')
    setAccountId(null)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted">Loading...</div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <div className="noise-overlay" />
      <Routes>
        {/* Public landing page */}
        <Route
          path="/"
          element={
            accountId ? <Navigate to="/dashboard" replace /> : <Landing />
          }
        />

        {/* Protected routes */}
        {accountId ? (
          <Route element={<Layout accountId={accountId} onDisconnect={handleDisconnect} />}>
            <Route path="/dashboard" element={<Dashboard accountId={accountId} />} />
            <Route path="/payments" element={<Payments accountId={accountId} />} />
            <Route path="/analytics" element={<Analytics accountId={accountId} />} />
            <Route path="/settings" element={<Settings accountId={accountId} onDisconnect={handleDisconnect} />} />
          </Route>
        ) : (
          <>
            <Route path="/dashboard" element={<Navigate to="/" replace />} />
            <Route path="/payments" element={<Navigate to="/" replace />} />
            <Route path="/analytics" element={<Navigate to="/" replace />} />
            <Route path="/settings" element={<Navigate to="/" replace />} />
          </>
        )}

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
