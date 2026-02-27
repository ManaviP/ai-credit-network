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

  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated])

  const handleGoogleLogin = async () => {
    if (loading) return
    setLoading(true)
    setError('')
    try {
      await signInWithGoogle()
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const handleEmailLogin = async (e) => {
    e.preventDefault()
    if (loading) return

    setLoading(true)
    setError('')
    setEmailSent(false)

    try {
      await signInWithEmailOtp(email)
      setEmailSent(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md bg-white p-6 rounded-2xl shadow">
        <h2 className="text-xl font-bold text-center">Welcome back</h2>

        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        {emailSent && <p className="text-green-600 text-sm mt-2">Check your inbox</p>}

        <button
          onClick={handleGoogleLogin}
          className="mt-4 w-full bg-white border rounded-lg py-2"
        >
          Continue with Google
        </button>

        <div className="my-4 text-center text-sm text-gray-400">OR</div>

        <form onSubmit={handleEmailLogin}>
          <input
            type="email"
            required
            placeholder="Email"
            className="w-full border rounded-lg p-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button className="mt-3 w-full bg-primary-600 text-white py-2 rounded-lg">
            Send Magic Link
          </button>
        </form>

        <p className="text-sm mt-4 text-center">
          New here? <Link to="/register">Create account</Link>
        </p>
      </div>
    </div>
  )
}