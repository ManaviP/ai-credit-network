import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import { signInWithEmailOtp, supabase, signInWithGoogle } from '../services/supabase'

export default function Register() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [step, setStep] = useState('google') // 'google', 'details'

  const [sessionToken, setSessionToken] = useState(null)
  const [email, setEmail] = useState('')
  const [emailSent, setEmailSent] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    aadhaar: '',
    location: '',
    consent_given: true
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    // If the user arrived here from the AuthCallback, they already have a session
    // but need to complete the 2nd step of registration. Pick up where they left off.
    const checkSession = async () => {
      const { data: { session }, error } = await supabase.auth.getSession()
      if (error) {
        setError(error.message)
        return
      }
      if (session?.access_token) {
        setSessionToken(session.access_token)
        setFormData(prev => ({
          ...prev,
          name: session.user?.user_metadata?.full_name || '',
        }))
        setStep('details')
      }
    }

    checkSession()
  }, [])

  const formatAPIError = (err) => {
    const detail = err.response?.data?.detail
    if (!detail) return err.message || 'An error occurred'
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map(d => d.msg || d.message || JSON.stringify(d)).join(' | ')
    }
    if (typeof detail === 'object') return detail.message || JSON.stringify(detail)
    return String(detail)
  }

  const handleGoogleLogin = async () => {
    setError('')
    try {
      setLoading(true)
      await signInWithGoogle()
    } catch (err) {
      setError(err?.message || String(err))
      setLoading(false)
    }
  }

  const handleEmailStart = async (e) => {
    e.preventDefault()
    setError('')
    setEmailSent(false)
    try {
      if (!email.trim()) throw new Error('Enter your email.')
      setLoading(true)
      await signInWithEmailOtp(email.trim())
      setEmailSent(true)
      setLoading(false)
    } catch (err) {
      setError(err?.message || String(err))
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (!sessionToken) {
        throw new Error('Please authenticate first (Google or magic link).')
      }

      const payload = {
        ...formData,
        phone: formData.phone ? formData.phone.replace(/\s|-/g, '').replace(/^\+/, '') : null,
        aadhaar: formData.aadhaar.replace(/\s/g, ''),
        access_token: sessionToken,
        provider: 'supabase'
      }

      const response = await authAPI.register(payload)
      login(response.data, response.data.user_id)
      navigate('/')
    } catch (err) {
      setError(formatAPIError(err))
    } finally {
      setLoading(false)
    }
  }

  if (step === 'google') {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-12">
          <div className="w-full max-w-md">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="text-center">
                <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-50 text-primary-700">
                  <span className="text-lg font-extrabold">CN</span>
                </div>
                <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">
                  Create your account
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                  Start with Google, then complete your profile
                </p>
              </div>

              {error && (
                <div className="mt-5 rounded-xl border border-danger/30 bg-danger-light px-4 py-3 text-sm text-danger-dark">
                  {error}
                </div>
              )}

              {emailSent && (
                <div className="mt-5 rounded-xl border border-success/30 bg-success-light px-4 py-3 text-sm text-success-dark">
                  Magic link sent. Check your inbox and open the link to continue.
                </div>
              )}

              <button
                onClick={handleGoogleLogin}
                disabled={loading}
                className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
                {loading ? 'Connecting…' : 'Continue with Google'}
              </button>

              <div className="my-5 flex items-center gap-3">
                <div className="h-px flex-1 bg-slate-200" />
                <div className="text-xs font-medium text-slate-500">OR</div>
                <div className="h-px flex-1 bg-slate-200" />
              </div>

              <form onSubmit={handleEmailStart} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex w-full items-center justify-center rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? 'Sending…' : 'Send magic link'}
                </button>
              </form>

              <p className="mt-4 text-center text-xs text-slate-500">
                By continuing, you agree to let us process your data for credit scoring.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="text-center">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                Complete your profile
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                This helps us personalize your credit network and scoring.
              </p>
            </div>

            <form className="mt-6 space-y-4" onSubmit={handleRegister}>
              {error && (
                <div className="rounded-xl border border-danger/30 bg-danger-light px-4 py-3 text-sm text-danger-dark">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700">Full name</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Your name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">Phone (optional)</label>
                <input
                  type="tel"
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="10-digit phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">Aadhaar (12 digits)</label>
                <input
                  type="text"
                  inputMode="numeric"
                  required
                  maxLength="12"
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="xxxxxxxxxxxx"
                  value={formData.aadhaar}
                  onChange={(e) => setFormData({ ...formData, aadhaar: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">Location (optional)</label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="City / district"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                />
              </div>

              <label className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5">
                <input
                  type="checkbox"
                  checked={formData.consent_given}
                  onChange={(e) => setFormData({ ...formData, consent_given: e.target.checked })}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-slate-700">
                  I consent to data processing for trust scoring (DPDP Act 2023)
                </span>
              </label>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full items-center justify-center rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? 'Creating account…' : 'Complete registration'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
