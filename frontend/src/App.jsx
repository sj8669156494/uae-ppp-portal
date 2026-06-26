import { useState } from 'react'
import { BarChart2, Table2, MessageSquare, Database } from 'lucide-react'
import { StatsStrip } from './components/StatsStrip'
import { FilterSidebar } from './components/FilterSidebar'
import { ProjectTable } from './components/ProjectTable'
import { ChatPanel } from './components/ChatPanel'
import { AnalyticsView } from './components/AnalyticsView'
import { useProjects } from './hooks/useProjects'

const TABS = [
  { id: 'projects', label: 'Projects', Icon: Table2 },
  { id: 'analytics', label: 'Analytics', Icon: BarChart2 },
  { id: 'chat', label: 'AI Chat', Icon: MessageSquare },
  { id: 'sources', label: 'Data Sources', Icon: Database },
]

const DATA_SOURCES = [
  { name: 'ADIO – Abu Dhabi Investment Office', url: 'https://www.adio.gov.ae', priority: 'HIGH', method: 'HTTP + LLM' },
  { name: 'WAM – UAE Media Office', url: 'https://wam.ae', priority: 'HIGH', method: 'RSS + HTTP' },
  { name: 'Dubai DOF PPP Portal', url: 'https://www.dof.gov.ae/ppp', priority: 'HIGH', method: 'HTML scrape' },
  { name: 'RTA Dubai', url: 'https://www.rta.ae', priority: 'HIGH', method: 'HTML scrape' },
  { name: 'DEWA / EWEC', url: 'https://www.dewa.gov.ae', priority: 'MEDIUM', method: 'HTML scrape' },
  { name: 'The National', url: 'https://www.thenationalnews.com', priority: 'MEDIUM', method: 'RSS + LLM' },
  { name: 'Gulf News Business', url: 'https://gulfnews.com', priority: 'MEDIUM', method: 'RSS + LLM' },
]

const DEFAULT_FILTERS = {
  sector: null,
  emirate: null,
  status: null,
  min_value: null,
  max_value: null,
  search: null,
}

export default function App() {
  const [tab, setTab] = useState('projects')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)

  const { data, isLoading } = useProjects(filters)

  const handleChatFilters = (chatFilters) => {
    const mapped = {}
    if (chatFilters.sector) mapped.sector = chatFilters.sector
    if (chatFilters.emirate) mapped.emirate = chatFilters.emirate
    if (chatFilters.status) mapped.status = chatFilters.status
    if (chatFilters.min_value != null) mapped.min_value = chatFilters.min_value
    if (chatFilters.max_value != null) mapped.max_value = chatFilters.max_value
    setFilters(prev => ({ ...prev, ...mapped }))
    setTab('projects')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">🇦🇪 UAE PPP Intelligence Portal</h1>
          <p className="text-slate-400 text-xs mt-0.5">AI-powered infrastructure project intelligence</p>
        </div>
        <div className="text-xs text-slate-500">Powered by GPT-4o-mini</div>
      </header>

      {/* Stats Strip */}
      <StatsStrip />

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-slate-200 px-6 flex gap-1">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="flex-1 px-6 py-5">
        {tab === 'projects' && (
          <div className="flex gap-6">
            <FilterSidebar filters={filters} onChange={setFilters} />
            <div className="flex-1 min-w-0">
              <ProjectTable
                projects={data?.projects || []}
                total={data?.total || 0}
                loading={isLoading}
              />
            </div>
          </div>
        )}

        {tab === 'analytics' && (
          <div className="max-w-5xl mx-auto">
            <AnalyticsView />
          </div>
        )}

        {tab === 'chat' && (
          <div className="max-w-2xl mx-auto" style={{ height: 'calc(100vh - 220px)' }}>
            <ChatPanel onFiltersChanged={handleChatFilters} />
          </div>
        )}

        {tab === 'sources' && (
          <div className="max-w-3xl mx-auto space-y-8">
            {/* Sources table */}
            <div>
              <h2 className="text-lg font-semibold text-slate-700 mb-1">Data Sources</h2>
              <p className="text-sm text-slate-500 mb-4">
                Chosen because they are the primary official UAE government portals and highest-signal news feeds for PPP/infrastructure announcements. Together they cover federal + all 7 emirates.
              </p>
              <div className="space-y-3">
                {DATA_SOURCES.map(s => (
                  <div key={s.name} className="bg-white border border-slate-200 rounded-lg px-4 py-3 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-800 text-sm">{s.name}</p>
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">{s.url}</a>
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className={`px-2 py-0.5 rounded-full ${s.priority === 'HIGH' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                        {s.priority}
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{s.method}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <a
                  href="/api/projects/export.csv"
                  download="uae_ppp_projects.csv"
                  className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  ⬇ Download Full Dataset (CSV)
                </a>
                <span className="ml-3 text-xs text-slate-400">43 projects · all fields · clean schema</span>
              </div>
            </div>

            {/* Scale & Limitations */}
            <div>
              <h2 className="text-lg font-semibold text-slate-700 mb-1">Scale & Where It Would Break</h2>
              <p className="text-sm text-slate-500 mb-3">Scrapers run daily at 6am via APScheduler. Here is an honest assessment of failure points:</p>
              <div className="space-y-2">
                {[
                  { risk: 'Website layout changes', impact: 'High', note: 'CSS selectors break silently. Mitigation: store raw HTML + LLM re-extracts from text, not markup.' },
                  { risk: 'JavaScript-rendered pages', impact: 'Medium', note: 'httpx misses JS-only content. Mitigation: Playwright fallback already in BaseScraper.' },
                  { risk: 'Rate limiting / CAPTCHA', impact: 'High', note: '2s delay + retry backoff implemented. At scale: rotating proxies + residential IPs needed.' },
                  { risk: 'Arabic-language sources', impact: 'Medium', note: 'Not in scope v1. V2: add translation layer before LLM extraction.' },
                  { risk: 'LLM extraction errors', impact: 'Medium', note: 'Confidence score flags < 0.7 for review. Human review queue needed at scale.' },
                  { risk: 'Duplicate projects across sources', impact: 'Medium', note: 'rapidfuzz fuzzy match at 80% threshold. Edge case: same project with very different names.' },
                  { risk: 'Single SQLite DB', impact: 'High at scale', note: 'Dev only. Production needs PostgreSQL + read replicas for concurrent users.' },
                ].map(r => (
                  <div key={r.risk} className="bg-white border border-slate-200 rounded-lg px-4 py-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-slate-800">{r.risk}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${r.impact.includes('High') ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{r.impact}</span>
                    </div>
                    <p className="text-xs text-slate-500">{r.note}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* What's next */}
            <div>
              <h2 className="text-lg font-semibold text-slate-700 mb-1">What We'd Build Next</h2>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { title: 'More sources', desc: 'Etihad Rail, Sharjah, RAK government portals, MEED, Zawya' },
                  { title: 'Arabic NLP', desc: 'Translate Arabic announcements before LLM extraction' },
                  { title: 'Alerts & notifications', desc: 'Email/webhook when a new tender matches a saved filter' },
                  { title: 'Contractor analytics', desc: 'Who is winning which sectors? Market share charts' },
                  { title: 'Document ingestion', desc: 'Upload PDFs (tender docs, annual reports) → auto-extract projects' },
                  { title: 'PostgreSQL + prod deploy', desc: 'Move from SQLite to PostgreSQL, deploy to cloud (AWS/Azure)' },
                ].map(n => (
                  <div key={n.title} className="bg-white border border-slate-200 rounded-lg px-4 py-3">
                    <p className="text-sm font-medium text-slate-800">{n.title}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{n.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="bg-slate-100 text-center text-xs text-slate-400 py-3 border-t border-slate-200">
        UAE PPP Intelligence Portal · Data updated daily at 6am · Powered by GPT-4o-mini
      </footer>
    </div>
  )
}
