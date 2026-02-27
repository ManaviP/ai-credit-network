import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://zdwedezftuzyppkslxhr.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpkd2VkZXpmdHV6eXBwa3NseGhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAxOTA1MTQsImV4cCI6MjA1NTU1MDUxNH0.sb_publishable_GdvNrXJpowDfXkA90b-zKw_X8PZ86o8'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export const signInWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: `${window.location.origin}/auth/callback` // Or whatever your redirect URL is
        }
    })
    if (error) throw error
    return data
}

export const getSession = async () => {
    const { data, error } = await supabase.auth.getSession()
    if (error) throw error
    return data.session
}

export const signOut = async () => {
    await supabase.auth.signOut()
}
