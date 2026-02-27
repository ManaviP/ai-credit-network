import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { signInWithEmailOtp, signInWithGoogle } from '../services/supabase'

export default function Login() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [email, setEmail] = useState('')
  const [emailSent, setEmailSent] = useState(false)

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleGoogleLogin = async () => {
    if (loading) return
    setError('')
    setLoading(true)

    try {
      await signInWithGoogle()
      // Do NOT set loading false here
      // Supabase will redirect automatically
    } catch (err) {
      setError(err?.message || 'Google sign-in failed')
      setLoading(false)
    }
  }

  const handleEmailLogin = async (e) => {
    e.preventDefault()
    if (loading) return

    setError('')
    setEmailSent(false)

    if (!email.trim()) {
      setError('Please enter your email.')
      return
    }

    setLoading(true)

    try {
      await signInWithEmailOtp(email.trim())
      setEmailSent(true)
    } catch (err) {
      setError(err?.message || 'Failed to send magic link')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

            <div className="text-center">
              <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-50 text-primary-700">
                <span className="text-lg font-extrabold">CN</span>
              </div>
              <h2 className="mt-4 text-2xl font-bold text-slate-900">
                Welcome back
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Sign in to continue to your dashboard
              </p>
            </div>

            {error && (
              <div className="mt-5 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {emailSent && (
              <div className="mt-5 rounded-xl border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-700">
                Magic link sent. Check your inbox.
              </div>
            )}

            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              className="mt-6 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-60"
            >
              {loading ? 'Connecting…' : 'Continue with Google'}
            </button>

            <div className="my-5 flex items-center gap-3">
              <div className="h-px flex-1 bg-slate-200" />
              <div className="text-xs text-slate-500">OR</div>
              <div className="h-px flex-1 bg-slate-200" />
            </div>

            <form onSubmit={handleEmailLogin} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-60"
              >
                {loading ? 'Sending…' : 'Send magic link'}
              </button>
            </form>

            <p className="mt-4 text-center text-xs text-slate-500">
              New here?{' '}
              <Link
                to="/register"
                className="font-semibold text-primary-700 hover:text-primary-800"
              >
                Create an account
              </Link>
            </p>

          </div>
        </div>
      </div>
    </div>
  )
}