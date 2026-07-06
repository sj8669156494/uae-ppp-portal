import { useState } from 'react'
import { ExternalLink, ChevronDown, ChevronRight } from 'lucide-react'

const STATUS_COLORS = {
  'Planned': 'bg-yellow-100 text-yellow-800',
  'Tendering': 'bg-blue-100 text-blue-800',
  'Under Execution': 'bg-green-100 text-green-800',
  'Complete': 'bg-slate-100 text-slate-700',
}

const SECTOR_COLORS = {
  Transport: 'bg-indigo-50 text-indigo-700',
  Energy: 'bg-orange-50 text-orange-700',
  Water: 'bg-cyan-50 text-cyan-700',
  Healthcare: 'bg-red-50 text-red-700',
  Education: 'bg-purple-50 text-purple-700',
  Social: 'bg-pink-50 text-pink-700',
  Infrastructure: 'bg-gray-50 text-gray-700',
  Environment: 'bg-green-50 text-green-700',
  Other: 'bg-slate-50 text-slate-600',
}

function DetailField({ label, value, isLink = false }) {
  if (!value) return null
  return (
    <div>
      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</span>
      <p className="text-xs text-slate-700 mt-0.5">
        {isLink ? (
          <a href={value} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-1">
            {value.length > 60 ? value.slice(0, 60) + '…' : value}
            <ExternalLink size={10} />
          </a>
        ) : value}
      </p>
    </div>
  )
}

function ExpandedRow({ p }) {
  const hasV2 = p.description || p.sub_sector || p.responsible_entity || p.project_type ||
    p.mode_of_implementation || p.ppp_type || p.ppp_model || p.requirements ||
    p.start_date || p.tender_end_date || p.news_link || p.ministry_link || p.contact_details

  return (
    <tr className="bg-slate-50 border-b border-slate-200">
      <td colSpan={7} className="px-6 py-4">
        <div className="grid grid-cols-3 gap-4">
          {p.description && (
            <div className="col-span-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Description</span>
              <p className="text-xs text-slate-700 mt-0.5">{p.description}</p>
            </div>
          )}
          <DetailField label="Sub Sector" value={p.sub_sector} />
          <DetailField label="Responsible Entity" value={p.responsible_entity} />
          <DetailField label="Project Type" value={p.project_type} />
          <DetailField label="Mode of Implementation" value={p.mode_of_implementation} />
          <DetailField label="PPP Type" value={p.ppp_type} />
          <DetailField label="PPP Model" value={p.ppp_model} />
          <DetailField label="Start Date" value={p.start_date} />
          <DetailField label="Tender End Date" value={p.tender_end_date} />
          <DetailField label="Contact" value={p.contact_details} />
          {p.requirements && (
            <div className="col-span-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Requirements</span>
              <p className="text-xs text-slate-700 mt-0.5">{p.requirements}</p>
            </div>
          )}
          <DetailField label="News Link" value={p.news_link} isLink />
          <DetailField label="Ministry Link" value={p.ministry_link} isLink />
          {p.notes && (
            <div className="col-span-3">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Notes</span>
              <p className="text-xs text-slate-500 mt-0.5 italic">{p.notes}</p>
            </div>
          )}
          {!hasV2 && p.notes && null}
          {!hasV2 && !p.notes && (
            <p className="text-xs text-slate-400 col-span-3">No extended details available for this project yet.</p>
          )}
        </div>
      </td>
    </tr>
  )
}

export function ProjectTable({ projects = [], total = 0, loading = false }) {
  const [expanded, setExpanded] = useState(null)

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-16 bg-slate-100 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (!projects.length) {
    return (
      <div className="text-center py-16 text-slate-500">
        <p className="text-lg font-medium">No projects found</p>
        <p className="text-sm mt-1">Try adjusting your filters or search terms</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          {total} project{total !== 1 ? 's' : ''} found
          <span className="ml-2 text-xs text-slate-400">· Click a row to expand details</span>
        </p>
        <a
          href="/api/projects/export.csv"
          download="uae_ppp_projects.csv"
          className="inline-flex items-center gap-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
        >
          ⬇ Export CSV
        </a>
      </div>
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th className="text-left px-4 py-3 w-8"></th>
              <th className="text-left px-4 py-3">Project</th>
              <th className="text-left px-4 py-3">Sector</th>
              <th className="text-left px-4 py-3">Emirate</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-right px-4 py-3">Value (AED B)</th>
              <th className="text-left px-4 py-3">Owner</th>
              <th className="text-center px-4 py-3">Year</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {projects.map(p => (
              <>
                <tr
                  key={p.id}
                  className="bg-white hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                >
                  <td className="px-4 py-3 text-slate-400">
                    {expanded === p.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </td>
                  <td className="px-4 py-3 max-w-xs">
                    <div className="flex items-start gap-1">
                      <span className="font-medium text-slate-800 line-clamp-2">{p.name}</span>
                      {p.source_url && (
                        <a
                          href={p.source_url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={e => e.stopPropagation()}
                          className="shrink-0 text-slate-400 hover:text-blue-600 mt-0.5"
                        >
                          <ExternalLink size={12} />
                        </a>
                      )}
                    </div>
                    {p.contractors && (
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{p.contractors}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${SECTOR_COLORS[p.sector] || 'bg-slate-100 text-slate-600'}`}>
                      {p.sector}
                    </span>
                    {p.sub_sector && (
                      <p className="text-xs text-slate-400 mt-0.5">{p.sub_sector}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{p.emirate}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[p.status] || 'bg-gray-100 text-gray-600'}`}>
                      {p.status}
                    </span>
                    {p.ppp_model && (
                      <p className="text-xs text-slate-400 mt-0.5">{p.ppp_model}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-slate-800">
                    {p.contract_value_aed != null ? p.contract_value_aed.toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-3 text-slate-600 text-xs max-w-xs">
                    <span className="line-clamp-2">{p.owner}</span>
                  </td>
                  <td className="px-4 py-3 text-center text-slate-500">
                    {p.expected_completion_year || '—'}
                  </td>
                </tr>
                {expanded === p.id && <ExpandedRow key={`${p.id}-exp`} p={p} />}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
