import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../services/supabase'
import { useAuthStore } from '../stores/authStore'

export default function AuthCallback() {
  const navigate = useNavigate()
  const { setSession } = useAuthStore()

  useEffect(() => {
    const init = async () => {
      const { data } = await supabase.auth.getSession()
      if (data.session) {
        setSession(data.session)
        navigate('/')
      } else {
        navigate('/login')
      }
    }
    init()
  }, [])

  return <p className="text-center mt-20">Logging you in...</p>
}
