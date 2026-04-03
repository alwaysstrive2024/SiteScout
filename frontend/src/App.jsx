import { useState, useCallback } from 'react'
import SearchBar      from './components/SearchBar.jsx'
import SettingsPanel  from './components/SettingsPanel.jsx'
import SitePool       from './components/SitePool.jsx'
import QuickTemplates from './components/QuickTemplates.jsx'
import LoadingState   from './components/LoadingState.jsx'
import AIInsightsTable from './components/AIInsightsTable.jsx'
import RawResults     from './components/RawResults.jsx'

const DEFAULT_DOMAINS = ['reddit.com', 'github.com', 'v2ex.com']

async function callRefine(payload) {
  const res = await fetch('/refine', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export default function App() {
  // ── Search state ─────────────────────────────────────────
  const [query,        setQuery]        = useState('')
  const [domains,      setDomains]      = useState(DEFAULT_DOMAINS)
  const [rawN,         setRawN]         = useState(10)
  const [llmK,         setLlmK]         = useState(5)
  const [modelChoice,  setModelChoice]  = useState('deepseek-chat')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [activeTemplate, setActiveTemplate] = useState(null)

  // ── Result state ─────────────────────────────────────────
  const [results,      setResults]      = useState(null)
  const [loading,      setLoading]      = useState(false)
  const [error,        setError]        = useState(null)
  const [hasSearched,  setHasSearched]  = useState(false)

  // ── Handlers ─────────────────────────────────────────────
  const handleSearch = useCallback(async () => {
    if (!query.trim() || domains.length === 0) return
    setLoading(true)
    setError(null)
    setHasSearched(true)
    setResults(null)

    try {
      const data = await callRefine({
        query:        query.trim(),
        domains,
        raw_n:        rawN,
        llm_k:        llmK,
        model_choice: modelChoice,
      })
      setResults(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [query, domains, rawN, llmK, modelChoice])

  const handleKeyDown = (e) => { if (e.key === 'Enter') handleSearch() }

  const handleTemplate = (t) => {
    setDomains(t.domains)
    setActiveTemplate(t.id)
    // Auto-open settings so user sees the pool change
    setSettingsOpen(true)
  }

  const handleReset = () => {
    setHasSearched(false)
    setResults(null)
    setError(null)
    setLoading(false)
  }

  // Count failed domains from results
  const failedDomains = results
    ? results.raw_search.results_per_domain.filter(d => d.error).length
    : 0

  const isHero = !hasSearched

  return (
    <div className="app-wrapper">
      <main className="main-content">
        <div className={isHero ? 'hero-layout' : 'results-layout'}>

          {/* ── LOGO (hero only) ── */}
          {isHero && (
            <div className="logo">
              <h1 className="logo-title">
                <span className="gradient-text">SiteScout</span>
                {' '}
                <span style={{ opacity: .7, fontSize: '0.65em' }}>灵嗅</span>
              </h1>
              <p className="logo-sub">Precision Multi-Site Search · LLM-Powered Refinement</p>
              <div className="logo-badge">
                <span>⚡</span>
                <span>Parallel asyncio · Bocha / Tavily · DeepSeek / GPT</span>
              </div>
            </div>
          )}

          {/* ── SEARCH AREA ── */}
          <div className={isHero ? 'search-section' : 'search-bar-compact search-section'}>

            {/* Quick Templates (hero only) */}
            {isHero && (
              <QuickTemplates onApply={handleTemplate} activeTemplate={activeTemplate} />
            )}

            <SearchBar
              query={query}
              setQuery={setQuery}
              onSearch={handleSearch}
              onKeyDown={handleKeyDown}
              loading={loading}
              compact={!isHero}
            />

            {/* Settings toggle row */}
            <div className="settings-toggle-row">
              <button
                id="settings-toggle"
                className={`settings-toggle-btn ${settingsOpen ? 'active' : ''}`}
                onClick={() => setSettingsOpen(v => !v)}
                aria-expanded={settingsOpen}
              >
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <circle cx="8" cy="8" r="2.5"/>
                  <path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M3.2 3.2l1 1M11.8 11.8l1 1M11.8 3.2l-1 1M4.2 11.8l-1 1"/>
                </svg>
                Search Settings
                <svg viewBox="0 0 10 6" fill="currentColor" style={{ transition: 'transform .2s', transform: settingsOpen ? 'rotate(180deg)' : 'none' }}>
                  <path d="M0 0l5 6 5-6z"/>
                </svg>
              </button>
              {hasSearched && (
                <button className="settings-toggle-btn" onClick={handleReset} style={{ marginLeft: 'auto' }}>
                  ← New Search
                </button>
              )}
            </div>

            {/* Collapsible settings panel */}
            {settingsOpen && (
              <div className="glass settings-panel" style={{ marginTop: 12 }}>
                <SettingsPanel
                  rawN={rawN} setRawN={setRawN}
                  llmK={llmK} setLlmK={setLlmK}
                  modelChoice={modelChoice} setModelChoice={setModelChoice}
                />
                <div className="setting-group full-width">
                  <SitePool domains={domains} setDomains={setDomains} />
                </div>
              </div>
            )}
          </div>

          {/* ── RESULTS AREA ── */}
          {hasSearched && (
            <div style={{ width: '100%' }}>

              {/* Loading animation */}
              <LoadingState loading={loading} domains={domains} />

              {/* Error banner */}
              {error && !loading && (
                <div className="error-card">
                  <span className="error-icon">⚠️</span>
                  <div className="error-msg">
                    <strong>Search failed:</strong> {error}
                    <br />
                    <small style={{ opacity: .7 }}>
                      Make sure the backend is running on port 8000 and your API keys are configured.
                    </small>
                  </div>
                </div>
              )}

              {/* Partial domain-failure notice */}
              {failedDomains > 0 && !loading && (
                <div className="warn-card">
                  <span>⚠️</span>
                  <span>
                    <strong>{failedDomains} domain{failedDomains > 1 ? 's' : ''}</strong> failed to respond —
                    results from the rest are still shown below.
                  </span>
                </div>
              )}

              {/* Stats bar */}
              {results && !loading && (
                <div className="stats-bar" style={{ marginBottom: 24 }}>
                  <div className="stat"><span>🔍</span><span>Query: <strong>{results.query}</strong></span></div>
                  <div className="stat-divider" />
                  <div className="stat"><span>🌐</span><span><strong>{results.raw_search.domains_queried.length}</strong> domains</span></div>
                  <div className="stat-divider" />
                  <div className="stat"><span>📄</span><span><strong>{results.raw_search.grand_total}</strong> raw results</span></div>
                  <div className="stat-divider" />
                  <div className="stat"><span>💎</span><span><strong>{results.refined.length}</strong> AI insights</span></div>
                  <div className="stat-divider" />
                  <div className="stat"><span>🤖</span><span>via <strong>{results.model_used}</strong></span></div>
                  {failedDomains > 0 && (
                    <>
                      <div className="stat-divider" />
                      <div className="stat" style={{ color: 'var(--warning)' }}>
                        <span>⚠️</span><span><strong>{failedDomains}</strong> failed</span>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* AI Insights section */}
              {results && !loading && (
                <>
                  <div className="section-header">
                    <span style={{ fontSize: '1.1rem' }}>💎</span>
                    <h2 className="section-title">AI Insights</h2>
                    <span className="section-badge">{results.refined.length} resources</span>
                    <div className="section-divider" />
                  </div>
                  <AIInsightsTable refined={results.refined} query={results.query} />

                  {/* Raw Results section */}
                  <div className="section-header" style={{ marginTop: 36 }}>
                    <span style={{ fontSize: '1.1rem' }}>🔍</span>
                    <h2 className="section-title">Raw Results</h2>
                    <span className="section-badge">{results.raw_search.grand_total} total</span>
                    <div className="section-divider" />
                  </div>
                  <RawResults domainResults={results.raw_search.results_per_domain} />
                </>
              )}

            </div>
          )}

        </div>
      </main>
    </div>
  )
}
