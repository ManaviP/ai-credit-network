import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../services/supabase'
import { authAPI } from '../services/api'
import { useAuthStore } from '../stores/authStore'

export default function AuthCallback() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [error, setError] = useState(null)
  const ranOnceRef = useRef(false)

  useEffect(() => {
    // React 18 StrictMode runs effects twice in dev; PKCE exchange must only run once.
    if (ranOnceRef.current) return
    ranOnceRef.current = true

    const handleAuthRedirect = async () => {
      try {
        const params = new URLSearchParams(window.location.search)
        const oauthError = params.get('error') || params.get('error_code')
        const oauthErrorDescription = params.get('error_description')
        if (oauthError) {
          throw new Error(oauthErrorDescription || oauthError)
        }

        // If we already have a session, don't try to exchange again.
        const { data: sessionDataBefore, error: sessionBeforeError } = await supabase.auth.getSession()
        if (sessionBeforeError) throw sessionBeforeError

        let session = sessionDataBefore?.session

        // PKCE flow: if we have a code and no session yet, exchange it.
        const code = params.get('code')
        if (!session?.access_token && code) {
          const { data, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)
          if (exchangeError) throw exchangeError
          session = data?.session || null

          // Remove the code from the URL to prevent retries on refresh.
          try {
            window.history.replaceState({}, document.title, '/auth/callback')
          } catch {
            // ignore
          }
        }

        const { data: sessionData, error: sessionError } = await supabase.auth.getSession()
        if (sessionError) throw sessionError
        session = sessionData?.session
        if (!session?.access_token) {
          throw new Error('No session found. Please try signing in again.')
        }

        try {
          const response = await authAPI.oauthLogin({ access_token: session.access_token })
          login(response.data, response.data.user_id)
          navigate('/', { replace: true })
        } catch (backendErr) {
          if (backendErr.response?.status === 404) {
            navigate('/register', { replace: true })
          } else {
            const detail = backendErr.response?.data?.detail
            setError(detail || backendErr.message || 'Failed to authenticate with backend')
          }
        }
      } catch (err) {
        setError(err?.message || String(err))
      }
    }

    handleAuthRedirect()
  }, [navigate, login])

  if (error) {
    return (
      <div className="min-h-screen grid place-items-center bg-slate-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Authentication error</h3>
          <p className="mt-2 text-sm text-slate-600">{error}</p>
          <button
            onClick={() => navigate('/login', { replace: true })}
            className="mt-5 inline-flex w-full items-center justify-center rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            Back to sign in
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen grid place-items-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-primary-600" />
          <div>
            <div className="text-sm font-semibold text-slate-900">Signing you in</div>
            <div className="text-sm text-slate-600">Completing authentication…</div>
          </div>
        </div>
      </div>
    </div>
  )
}
