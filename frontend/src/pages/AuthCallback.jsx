import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../services/supabase'
import { authAPI } from '../services/api'
import { useAuthStore } from '../stores/authStore'

export default function AuthCallback() {
    const navigate = useNavigate()
    const { login } = useAuthStore()
    const [error, setError] = useState(null)

    useEffect(() => {
        // Supabase automatically parses the URL hash into a session object, 
        // we just need to wait for it and then act.
        const handleAuthRedirect = async () => {
            try {
                const { data: { session }, error: sessionError } = await supabase.auth.getSession()

                if (sessionError) throw sessionError
                if (!session) throw new Error("No session found in URL")

                // Try to log in with our custom backend
                try {
                    const response = await authAPI.oauthLogin({ access_token: session.access_token })
                    login(response.data, response.data.user_id)
                    navigate('/') // Successfully logged in
                } catch (backendErr) {
                    if (backendErr.response?.status === 404) {
                        // User isn't in our PostgreSQL database yet, take them to register
                        navigate('/register')
                    } else {
                        setError(backendErr.response?.data?.detail || backendErr.message || "Failed to authenticate with backend")
                    }
                }
            } catch (err) {
                setError(err.message)
            }
        }

        handleAuthRedirect()
    }, [navigate, login])

    if (error) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-4">
                <div className="bg-red-50 text-red-600 p-4 rounded-md shadow-sm max-w-md w-full">
                    <h3 className="font-bold text-lg mb-2">Authentication Error</h3>
                    <p>{error}</p>
                    <button
                        onClick={() => navigate('/login')}
                        className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                        Return to Login
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <span className="ml-3 text-gray-600">Completing sign in...</span>
        </div>
    )
}
