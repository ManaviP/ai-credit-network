import { useState, useEffect } from 'react'
import { usersAPI } from '../services/api'
import TrustScoreGauge from '../components/TrustScoreGauge'
import TrustScoreBreakdown from '../components/TrustScoreBreakdown'

export default function Dashboard() {
  const [profile, setProfile] = useState(null)
  const [scoreData, setScoreData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const profileRes = await usersAPI.getProfile()
      setProfile(profileRes.data)

      if (profileRes.data.id) {
        const scoreRes = await usersAPI.getScore(profileRes.data.id)
        setScoreData(scoreRes.data)
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {profile?.name}! 👋
        </h1>
        <p className="mt-2 text-gray-600">
          Here&apos;s your credit profile overview
        </p>
      </div>

      {/* Trust Score Card */}
      {scoreData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">Your Trust Score</h2>
            <TrustScoreGauge score={scoreData.score} />
            <p className="mt-4 text-sm text-gray-600">{scoreData.explanation}</p>
          </div>

          <div className="card p-6">
            <h2 className="text-xl font-semibold mb-4">Score Breakdown</h2>
            <TrustScoreBreakdown breakdown={scoreData.breakdown} />
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900">Account Tier</h3>
          <p className="mt-2 text-3xl font-bold text-primary-600">
            {profile?.tier?.toUpperCase() || 'BRONZE'}
          </p>
        </div>
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900">Member Since</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {profile?.joined_at ? new Date(profile.joined_at).toLocaleDateString() : 'N/A'}
          </p>
        </div>
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900">Location</h3>
          <p className="mt-2 text-xl font-bold text-gray-900">
            {profile?.location || 'Not specified'}
          </p>
        </div>
      </div>
    </div>
  )
}
