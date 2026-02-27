export default function TrustScoreBreakdown({ breakdown }) {
  if (!breakdown?.components) return null

  const components = [
    { key: 'repayment_history', label: 'Repayment History', weight: '40%' },
    { key: 'community_tenure', label: 'Community Tenure', weight: '20%' },
    { key: 'vouch_count', label: 'Vouch Count', weight: '15%' },
    { key: 'voucher_reliability', label: 'Voucher Quality', weight: '15%' },
    { key: 'loan_volume', label: 'Loan Volume', weight: '10%' },
  ]

  return (
    <div className="space-y-4">
      {components.map(({ key, label, weight }) => {
        const component = breakdown.components[key]
        if (!component) return null

        const percentage = (component.score / 1000) * 100

        return (
          <div key={key}>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium">{label}</span>
              <span className="text-gray-600">{weight}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-500 h-2 rounded-full transition-all"
                style={{ width: `${percentage}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs mt-1 text-gray-500">
              <span>Score: {Math.round(component.score)}</span>
              <span>Contribution: {Math.round(component.weighted_contribution)}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
