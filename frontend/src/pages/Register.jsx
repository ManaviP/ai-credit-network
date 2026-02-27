import { useState } from 'react'
import { signInWithEmailOtp, signInWithGoogle } from '../services/supabase'

export default function Register() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleEmailSignup = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    try {
      await signInWithEmailOtp(email)
      setMessage('Magic link sent. Check your inbox.')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleGoogleSignup = async () => {
    try {
      await signInWithGoogle()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-md bg-white p-6 rounded-2xl shadow">
        <h2 className="text-xl font-bold text-center">Create account</h2>

        {message && <p className="text-green-600 text-sm mt-2">{message}</p>}
        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}

        <button
          onClick={handleGoogleSignup}
          className="mt-4 w-full border rounded-lg py-2"
        >
          Continue with Google
        </button>

        <div className="my-4 text-center text-sm text-gray-400">OR</div>

        <form onSubmit={handleEmailSignup}>
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
      </div>
    </div>
  )
}
