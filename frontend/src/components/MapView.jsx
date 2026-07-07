'use client'
import { MapContainer, TileLayer, CircleMarker, Popup, ZoomControl } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { useState } from 'react'

// UAE emirate centre coordinates
const EMIRATE_COORDS = {
  'Abu Dhabi':      [24.4539, 54.3773],
  'Dubai':          [25.2048, 55.2708],
  'Sharjah':        [25.3462, 55.4209],
  'Ras Al Khaimah': [25.7895, 55.9432],
  'Fujairah':       [25.1288, 56.3265],
  'Ajman':          [25.4052, 55.5136],
  'Umm Al Quwain':  [25.5653, 55.5550],
  'Multiple':       [24.1500, 54.2000],
  'Federal':        [23.8000, 53.8000],
}

const SECTOR_COLORS = {
  Transport:      '#1e40af',
  Energy:         '#c2410c',
  Water:          '#0891b2',
  Healthcare:     '#dc2626',
  Education:      '#7c3aed',
  Social:         '#db2777',
  Infrastructure: '#374151',
  Environment:    '#16a34a',
  Other:          '#6b7280',
}

const STATUS_FILL_OPACITY = {
  'Planned':         0.4,
  'Tendering':       0.65,
  'Under Execution': 0.9,
  'Complete':        0.95,
}

// Spread projects in a small circle so they don't stack
function jitter(base, index, total) {
  if (total <= 1) return base
  const angle = (index / total) * 2 * Math.PI
  const r = Math.min(0.06, 0.015 * Math.sqrt(total))
  return [base[0] + r * Math.sin(angle), base[1] + r * Math.cos(angle)]
}

const UAE_CENTER = [24.4, 54.8]

export default function MapView({ projects = [] }) {
  const [hovered, setHovered] = useState(null)

  // Group by emirate for jitter calculation
  const grouped = {}
  projects.forEach(p => {
    const e = p.emirate || 'Multiple'
    if (!grouped[e]) grouped[e] = []
    grouped[e].push(p)
  })

  // Flatten with jittered positions
  const positioned = []
  Object.entries(grouped).forEach(([emirate, list]) => {
    const base = EMIRATE_COORDS[emirate] || EMIRATE_COORDS['Multiple']
    list.forEach((p, i) => {
      positioned.push({ ...p, _pos: jitter(base, i, list.length) })
    })
  })

  return (
    <div className="flex gap-4 h-full">
      {/* Map */}
      <div className="flex-1 rounded-xl overflow-hidden border border-slate-200 shadow-sm" style={{ minHeight: 520 }}>
        <MapContainer
          center={UAE_CENTER}
          zoom={8}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ZoomControl position="bottomright" />

          {positioned.map(p => {
            const color = SECTOR_COLORS[p.sector] || '#6b7280'
            const opacity = STATUS_FILL_OPACITY[p.status] ?? 0.7
            const radius = p.contract_value_aed
              ? Math.max(7, Math.min(22, 7 + Math.sqrt(p.contract_value_aed) * 1.2))
              : 8

            return (
              <CircleMarker
                key={p.id}
                center={p._pos}
                radius={radius}
                pathOptions={{
                  color: '#fff',
                  weight: 1.5,
                  fillColor: color,
                  fillOpacity: opacity,
                }}
                eventHandlers={{
                  mouseover: () => setHovered(p.id),
                  mouseout: () => setHovered(null),
                }}
              >
                <Popup maxWidth={280}>
                  <div className="text-xs space-y-1.5 py-1" style={{ fontFamily: 'inherit' }}>
                    <p className="font-bold text-slate-900 text-sm leading-tight">{p.name}</p>
                    <div className="flex flex-wrap gap-1">
                      <span style={{ background: color, color: '#fff' }} className="px-1.5 py-0.5 rounded text-xs">
                        {p.sector}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-xs bg-slate-100 text-slate-700">
                        {p.status}
                      </span>
                      {p.ppp_model && (
                        <span className="px-1.5 py-0.5 rounded text-xs bg-blue-50 text-blue-700">
                          {p.ppp_model}
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-slate-600">
                      <span className="text-slate-400">Owner</span>
                      <span className="font-medium truncate">{p.owner}</span>
                      {p.contract_value_aed != null && (
                        <>
                          <span className="text-slate-400">Value</span>
                          <span className="font-medium text-green-700">AED {p.contract_value_aed.toFixed(1)}B</span>
                        </>
                      )}
                      {p.expected_completion_year && (
                        <>
                          <span className="text-slate-400">Completion</span>
                          <span>{p.expected_completion_year}</span>
                        </>
                      )}
                      {p.contractors && (
                        <>
                          <span className="text-slate-400">Contractor</span>
                          <span className="truncate">{p.contractors}</span>
                        </>
                      )}
                    </div>
                    {p.description && (
                      <p className="text-slate-500 text-xs leading-relaxed border-t border-slate-100 pt-1">
                        {p.description.slice(0, 120)}{p.description.length > 120 ? '…' : ''}
                      </p>
                    )}
                    {p.source_url && (
                      <a
                        href={p.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 hover:underline text-xs block pt-0.5"
                      >
                        Source →
                      </a>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>

      {/* Legend + stats panel */}
      <div className="w-52 shrink-0 flex flex-col gap-4">
        {/* Summary stats */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Showing</p>
          <p className="text-2xl font-bold text-slate-900">{projects.length}</p>
          <p className="text-xs text-slate-500">
            {projects.length === 1 ? 'project' : 'projects'}
            {projects.filter(p => p.contract_value_aed).length > 0 && (
              <span className="block text-green-700 font-semibold text-sm mt-0.5">
                AED {projects.reduce((s, p) => s + (p.contract_value_aed || 0), 0).toFixed(0)}B total
              </span>
            )}
          </p>
        </div>

        {/* Sector legend */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Sector</p>
          <div className="space-y-1.5">
            {Object.entries(SECTOR_COLORS).map(([sector, color]) => {
              const count = projects.filter(p => p.sector === sector).length
              if (count === 0) return null
              return (
                <div key={sector} className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-full shrink-0" style={{ background: color }} />
                    <span className="text-xs text-slate-700">{sector}</span>
                  </div>
                  <span className="text-xs font-medium text-slate-500">{count}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Status legend */}
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Opacity = Status</p>
          <div className="space-y-1.5">
            {Object.entries(STATUS_FILL_OPACITY).map(([status, opacity]) => {
              const count = projects.filter(p => p.status === status).length
              if (count === 0) return null
              return (
                <div key={status} className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-3 h-3 rounded-full shrink-0 bg-slate-600"
                      style={{ opacity }}
                    />
                    <span className="text-xs text-slate-700">{status}</span>
                  </div>
                  <span className="text-xs font-medium text-slate-500">{count}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Bubble size note */}
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-3">
          <p className="text-xs text-slate-500 leading-relaxed">
            <span className="font-semibold text-slate-700">Bubble size</span> = contract value. Larger = higher AED value.
          </p>
        </div>
      </div>
    </div>
  )
}
