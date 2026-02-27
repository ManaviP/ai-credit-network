export default function TrustScoreGauge({ score }) {
  const getScoreColor = (score) => {
    if (score >= 700) return 'text-success'
    if (score >= 500) return 'text-warning'
    return 'text-danger'
  }

  const getScoreLabel = (score) => {
    if (score >= 700) return 'Excellent'
    if (score >= 500) return 'Good'
    if (score >= 300) return 'Building'
    return 'New'
  }

  const percentage = (score / 1000) * 100

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-48">
        <svg className="w-full h-full" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="10"
          />
          {/* Score circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            strokeDasharray={`${percentage * 2.827} 282.7`}
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
            className={getScoreColor(score)}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-bold ${getScoreColor(score)}`}>
            {Math.round(score)}
          </span>
          <span className="text-sm text-gray-600">out of 1000</span>
        </div>
      </div>
      <div className="mt-4 text-center">
        <span className={`text-xl font-semibold ${getScoreColor(score)}`}>
          {getScoreLabel(score)}
        </span>
      </div>
    </div>
  )
}
