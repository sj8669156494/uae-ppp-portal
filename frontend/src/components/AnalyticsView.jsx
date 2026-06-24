import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { useStats } from '../hooks/useProjects'

const COLORS = ['#1e40af', '#0891b2', '#059669', '#dc2626', '#7c3aed', '#db2777', '#d97706', '#6d28d9', '#374151']

export function AnalyticsView() {
  const { data: stats, isLoading } = useStats()

  if (isLoading) {
    return <div className="flex items-center justify-center h-64 text-slate-400">Loading analytics…</div>
  }

  if (!stats) return null

  const sectorData = Object.entries(stats.by_sector || {})
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  const emirateData = Object.entries(stats.by_emirate || {})
    .map(([name, count]) => ({ name, value: count }))
    .sort((a, b) => b.value - a.value)

  const statusData = Object.entries(stats.by_status || {})
    .map(([name, count]) => ({ name, count }))

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="bg-blue-50 rounded-xl p-4">
          <div className="text-3xl font-bold text-blue-700">{stats.total_projects}</div>
          <div className="text-sm text-blue-500 mt-1">Total Projects</div>
        </div>
        <div className="bg-green-50 rounded-xl p-4">
          <div className="text-3xl font-bold text-green-700">
            AED {(stats.total_value_aed_billions || 0).toFixed(0)}B
          </div>
          <div className="text-sm text-green-500 mt-1">Combined Value</div>
        </div>
        <div className="bg-purple-50 rounded-xl p-4">
          <div className="text-3xl font-bold text-purple-700">
            {Object.keys(stats.by_sector || {}).length}
          </div>
          <div className="text-sm text-purple-500 mt-1">Sectors Covered</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        <div>
          <h3 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wider">Projects by Sector</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sectorData} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={90} />
              <Tooltip />
              <Bar dataKey="count" fill="#1e40af" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wider">Projects by Emirate</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={emirateData}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="value"
                nameKey="name"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {emirateData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wider">Projects by Status</h3>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={statusData}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {statusData.map((entry, i) => (
                <Cell
                  key={i}
                  fill={
                    entry.name === 'Under Execution' ? '#059669' :
                    entry.name === 'Tendering' ? '#2563eb' :
                    entry.name === 'Planned' ? '#d97706' : '#6b7280'
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
