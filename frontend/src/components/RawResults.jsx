import { useState } from 'react'

function ResultItem({ result, index }) {
  return (
    <div className="result-item" style={{ animationDelay: `${index * 30}ms` }}>
      <div className="result-title">
        <a href={result.url} target="_blank" rel="noopener noreferrer">
          {result.title || result.url}
        </a>
      </div>
      <div className="result-url">{result.url}</div>
      {result.snippet && <p className="result-snippet">{result.snippet}</p>}
      <div className="result-meta">
        {result.site && <span>🌐 {result.site}</span>}
        {result.published_date && <span>📅 {result.published_date.slice(0, 10)}</span>}
      </div>
    </div>
  )
}

function DomainBucket({ dr }) {
  const [open, setOpen] = useState(true)
  const hasError = !!dr.error

  return (
    <div className="glass domain-bucket">
      <div
        className={`domain-bucket-header ${open ? 'open' : ''}`}
        onClick={() => setOpen(v => !v)}
        role="button"
        aria-expanded={open}
      >
        <span className="domain-name">
          <span className="domain-dot" style={hasError ? { background: 'var(--danger)' } : {}} />
          {dr.domain}
          <span className="domain-count">
            {hasError ? '' : `· ${dr.total} result${dr.total !== 1 ? 's' : ''}`}
          </span>
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {hasError && (
            <span className="domain-error-badge">
              ⚠️ {dr.error.length > 60 ? dr.error.slice(0, 60) + '…' : dr.error}
            </span>
          )}
          <svg
            className={`chevron ${open ? 'open' : ''}`}
            width="14" height="14" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2.5"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </div>

      {open && (
        <div className="result-items">
          {dr.results.length === 0 && !hasError ? (
            <div className="empty-state" style={{ padding: '20px' }}>
              No results from this domain.
            </div>
          ) : (
            dr.results.map((r, i) => <ResultItem key={r.url + i} result={r} index={i} />)
          )}
        </div>
      )}
    </div>
  )
}

export default function RawResults({ domainResults }) {
  if (!domainResults || domainResults.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📭</div>
        <p>No raw results to display.</p>
      </div>
    )
  }

  return (
    <div className="raw-results-grid">
      {domainResults.map(dr => (
        <DomainBucket key={dr.domain} dr={dr} />
      ))}
    </div>
  )
}
