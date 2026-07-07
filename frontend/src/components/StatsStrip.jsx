'use client'
import { useStats } from '../hooks/useProjects'

export function StatsStrip() {
  const { data: stats, isLoading } = useStats()

  if (isLoading) {
    return (
      <div className="bg-slate-800 text-white py-3 px-6 flex gap-8 animate-pulse">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-6 bg-slate-600 rounded w-32" />
        ))}
      </div>
    )
  }

  if (!stats) return null

  const statusCounts = stats.by_status || {}

  return (
    <div className="bg-slate-800 text-white py-3 px-6 flex flex-wrap gap-6 text-sm">
      <StatItem label="Total Projects" value={stats.total_projects} />
      <StatItem
        label="Total Value"
        value={`AED ${(stats.total_value_aed_billions || 0).toFixed(0)}B`}
      />
      <StatItem label="Under Execution" value={statusCounts['Under Execution'] ?? 0} />
      <StatItem label="Tendering" value={statusCounts['Tendering'] ?? 0} />
      <StatItem label="Planned" value={statusCounts['Planned'] ?? 0} />
      <StatItem label="Complete" value={statusCounts['Complete'] ?? 0} />
    </div>
  )
}

function StatItem({ label, value }) {
  return (
    <div className="flex flex-col">
      <span className="text-slate-400 text-xs uppercase tracking-wider">{label}</span>
      <span className="font-bold text-white text-base">{value}</span>
    </div>
  )
}
