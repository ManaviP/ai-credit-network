import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import { signInWithEmailOtp, supabase, signInWithGoogle } from '../services/supabase'

export default function Register() {
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const [step, setStep] = useState('auth') // 'auth' or 'details'
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

  // 🔥 HANDLE SUPABASE SESSION + AUTH STATE
  useEffect(() => {
    let mounted = true

    const setupSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()

      if (mounted && session?.access_token) {
        initializeUser(session)
      }
    }

    const initializeUser = (session) => {
      setSessionToken(session.access_token)

      setFormData(prev => ({
        ...prev,
        name: session.user?.user_metadata?.full_name ||
              session.user?.email?.split('@')[0] ||
              ''
      }))

      setStep('details')
    }

    setupSession()

    // Listen for auth changes (CRITICAL)
    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (session?.access_token) {
          initializeUser(session)
        }
      }
    )

    return () => {
      mounted = false
      listener?.subscription?.unsubscribe()
    }
  }, [])

  // 🔵 GOOGLE LOGIN
  const handleGoogleLogin = async () => {
    if (loading) return
    setError('')
    setLoading(true)

    try {
      await signInWithGoogle()
      // Supabase will redirect
    } catch (err) {
      setError(err?.message || 'Google login failed')
      setLoading(false)
    }
  }

  // 📧 MAGIC LINK START
  const handleEmailStart = async (e) => {
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

  // 📝 FINAL REGISTER STEP
  const handleRegister = async (e) => {
    e.preventDefault()
    if (loading) return

    setLoading(true)
    setError('')

    try {
      if (!sessionToken) {
        throw new Error('Please authenticate first.')
      }

      const payload = {
        ...formData,
        phone: formData.phone
          ? formData.phone.replace(/\s|-/g, '').replace(/^\+/, '')
          : null,
        aadhaar: formData.aadhaar.replace(/\s/g, ''),
        access_token: sessionToken,
        provider: 'supabase'
      }

      const response = await authAPI.register(payload)

      login(response.data, response.data.user_id)
      navigate('/')
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        typeof detail === 'string'
          ? detail
          : detail?.message || err.message || 'Registration failed'
      )
    } finally {
      setLoading(false)
    }
  }

  // ================= AUTH STEP =================
  if (step === 'auth') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="w-full max-w-md bg-white p-6 rounded-2xl shadow-sm border border-slate-200">

          <h2 className="text-2xl font-bold text-center text-slate-900">
            Create your account
          </h2>

          {error && (
            <div className="mt-4 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          {emailSent && (
            <div className="mt-4 bg-green-50 border border-green-300 text-green-700 px-4 py-3 rounded-xl text-sm">
              Magic link sent. Check your inbox.
            </div>
          )}

          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="mt-6 w-full bg-white border border-slate-200 rounded-xl py-2.5 text-sm font-semibold hover:bg-slate-50 disabled:opacity-60"
          >
            {loading ? 'Connecting…' : 'Continue with Google'}
          </button>

          <div className="my-5 flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-xs text-slate-500">OR</span>
            <div className="flex-1 h-px bg-slate-200" />
          </div>

          <form onSubmit={handleEmailStart} className="space-y-3">
            <input
              type="email"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-primary-500"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 text-white rounded-xl py-2.5 text-sm font-semibold hover:bg-primary-700 disabled:opacity-60"
            >
              {loading ? 'Sending…' : 'Send magic link'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  // ================= DETAILS STEP =================
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white p-6 rounded-2xl shadow-sm border border-slate-200">

        <h2 className="text-2xl font-bold text-center text-slate-900">
          Complete your profile
        </h2>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="mt-6 space-y-4">

          <input
            type="text"
            required
            placeholder="Full name"
            value={formData.name}
            onChange={(e) =>
              setFormData({ ...formData, name: e.target.value })
            }
            className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm"
          />

          <input
            type="tel"
            placeholder="Phone (optional)"
            value={formData.phone}
            onChange={(e) =>
              setFormData({ ...formData, phone: e.target.value })
            }
            className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm"
          />

          <input
            type="text"
            required
            maxLength="12"
            inputMode="numeric"
            placeholder="Aadhaar (12 digits)"
            value={formData.aadhaar}
            onChange={(e) =>
              setFormData({ ...formData, aadhaar: e.target.value })
            }
            className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm"
          />

          <input
            type="text"
            placeholder="Location (optional)"
            value={formData.location}
            onChange={(e) =>
              setFormData({ ...formData, location: e.target.value })
            }
            className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm"
          />

          <label className="flex gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={formData.consent_given}
              onChange={(e) =>
                setFormData({ ...formData, consent_given: e.target.checked })
              }
            />
            I consent to data processing for trust scoring
          </label>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white rounded-xl py-2.5 text-sm font-semibold hover:bg-primary-700 disabled:opacity-60"
          >
            {loading ? 'Creating account…' : 'Complete registration'}
          </button>

        </form>
      </div>
    </div>
  )
}