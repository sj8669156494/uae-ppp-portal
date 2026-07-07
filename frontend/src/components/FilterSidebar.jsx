'use client'
import { X } from 'lucide-react'

const SECTORS = ['Transport', 'Energy', 'Water', 'Healthcare', 'Education', 'Social', 'Infrastructure', 'Environment', 'Other']
const EMIRATES = ['Abu Dhabi', 'Dubai', 'Sharjah', 'Ras Al Khaimah', 'Fujairah', 'Ajman', 'Umm Al Quwain', 'Multiple', 'Federal']
const STATUSES = ['Planned', 'Tendering', 'Under Execution', 'Complete']

export function FilterSidebar({ filters, onChange, compact = false }) {
  const set = (key, value) => onChange({ ...filters, [key]: value || null })
  const reset = () => onChange({ sector: null, emirate: null, status: null, min_value: null, max_value: null, search: null })

  const activeCount = Object.values(filters).filter(Boolean).length

  if (compact) {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        <select
          value={filters.sector || ''}
          onChange={e => set('sector', e.target.value)}
          className="text-xs border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-white"
        >
          <option value="">All Sectors</option>
          {SECTORS.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
        <select
          value={filters.emirate || ''}
          onChange={e => set('emirate', e.target.value)}
          className="text-xs border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-white"
        >
          <option value="">All Emirates</option>
          {EMIRATES.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
        <select
          value={filters.status || ''}
          onChange={e => set('status', e.target.value)}
          className="text-xs border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-300 bg-white"
        >
          <option value="">All Statuses</option>
          {STATUSES.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
        {activeCount > 0 && (
          <button onClick={reset} className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
            <X size={12} /> Clear
          </button>
        )}
      </div>
    )
  }

  return (
    <aside className="w-56 shrink-0 flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-slate-700 text-sm uppercase tracking-wider">Filters</h2>
        {activeCount > 0 && (
          <button onClick={reset} className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
            <X size={12} /> Clear ({activeCount})
          </button>
        )}
      </div>

      <div>
        <label className="block text-xs text-slate-500 mb-1">Search</label>
        <input
          type="text"
          placeholder="Project name, owner…"
          value={filters.search || ''}
          onChange={e => set('search', e.target.value)}
          className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
        />
      </div>

      <FilterSelect label="Sector" value={filters.sector} options={SECTORS} onChange={v => set('sector', v)} />
      <FilterSelect label="Emirate" value={filters.emirate} options={EMIRATES} onChange={v => set('emirate', v)} />
      <FilterSelect label="Status" value={filters.status} options={STATUSES} onChange={v => set('status', v)} />

      <div>
        <label className="block text-xs text-slate-500 mb-1">Value (AED Billions)</label>
        <div className="flex gap-1 items-center">
          <input
            type="number"
            placeholder="Min"
            min="0"
            value={filters.min_value || ''}
            onChange={e => set('min_value', e.target.value ? Number(e.target.value) : null)}
            className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <span className="text-slate-400 text-xs">–</span>
          <input
            type="number"
            placeholder="Max"
            min="0"
            value={filters.max_value || ''}
            onChange={e => set('max_value', e.target.value ? Number(e.target.value) : null)}
            className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>
      </div>
    </aside>
  )
}

function FilterSelect({ label, value, options, onChange }) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      <select
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white"
      >
        <option value="">All</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )
}
