import { useState } from 'react'

// ── Markdown serialiser ───────────────────────────────────────────────────────

function toMarkdown(refined, query) {
  const header = `## 💎 SiteScout AI Insights\n\n**Query:** \`${query}\`\n\n`
  const cols = '| # | Resource | Source | Direct Link | Password | Status |'
  const sep  = '|---|---|---|---|---|---|'
  const rows = refined.map((r, i) => {
    const link = r.direct_link ? `[Link](${r.direct_link})` : '—'
    const pwd  = r.password    ? `\`${r.password}\``         : '—'
    return `| ${i + 1} | ${r.resource_name || '—'} | ${r.source || '—'} | ${link} | ${pwd} | ${r.status || '—'} |`
  })
  return header + [cols, sep, ...rows].join('\n')
}

// ── Copy button ───────────────────────────────────────────────────────────────

function CopyMarkdownBtn({ refined, query }) {
  const [state, setState] = useState('idle') // idle | copied | error

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(toMarkdown(refined, query))
      setState('copied')
      setTimeout(() => setState('idle'), 2200)
    } catch {
      setState('error')
      setTimeout(() => setState('idle'), 2200)
    }
  }

  const labels = { idle: '📋 Copy Markdown', copied: '✅ Copied!', error: '❌ Failed' }
  const colors = { idle: 'var(--accent-light)', copied: 'var(--success)', error: 'var(--danger)' }

  return (
    <button
      id="copy-markdown-btn"
      className="copy-md-btn"
      onClick={handleCopy}
      style={{ color: colors[state] }}
      disabled={state !== 'idle'}
      title="Copy AI Insights as a Markdown table"
    >
      {labels[state]}
    </button>
  )
}

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  if (!status) return <span className="status-badge" style={{ color: 'var(--text-muted)' }}>—</span>
  let color = 'var(--text-secondary)'
  if (status.includes('✅') || status.toLowerCase().includes('verified'))   color = 'var(--success)'
  if (status.includes('⚠️') || status.toLowerCase().includes('unverified')) color = 'var(--warning)'
  if (status.includes('❌') || status.toLowerCase().includes('dead'))        color = 'var(--danger)'
  if (status.includes('🔒') || status.toLowerCase().includes('pay'))         color = 'var(--info)'
  return <span className="status-badge" style={{ color }}>{status}</span>
}

// ── Main component ────────────────────────────────────────────────────────────

export default function AIInsightsTable({ refined, query = '' }) {
  if (!refined || refined.length === 0) {
    return (
      <div className="glass insights-card">
        <div className="empty-state">
          <div className="empty-icon">🔮</div>
          <p>No AI insights extracted. Try broadening your query or increasing LLM K.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass insights-card">
      {/* Card toolbar */}
      <div className="insights-toolbar">
        <span className="insights-toolbar-info">
          {refined.length} resource{refined.length !== 1 ? 's' : ''} extracted
        </span>
        <CopyMarkdownBtn refined={refined} query={query} />
      </div>

      <div className="table-container">
        <table className="insights-table" aria-label="AI extracted resources">
          <thead>
            <tr>
              <th>#</th>
              <th>Resource</th>
              <th>Source</th>
              <th>Direct Link</th>
              <th>Password</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {refined.map((r, i) => (
              <tr key={i}>
                <td style={{ color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums', width: 36 }}>
                  {i + 1}
                </td>
                <td className="resource-name">{r.resource_name || '—'}</td>
                <td>
                  <span style={{
                    display: 'inline-block', padding: '2px 8px', borderRadius: '99px',
                    background: 'rgba(6,182,212,.08)', border: '1px solid rgba(6,182,212,.18)',
                    fontSize: '.75rem', color: '#67e8f9', whiteSpace: 'nowrap',
                  }}>
                    {r.source || '—'}
                  </span>
                </td>
                <td className="link-cell">
                  {r.direct_link
                    ? <a href={r.direct_link} target="_blank" rel="noopener noreferrer" title={r.direct_link}>
                        {r.direct_link.length > 55 ? r.direct_link.slice(0, 55) + '…' : r.direct_link}
                      </a>
                    : <span className="no-link">No link found</span>
                  }
                </td>
                <td className="password-cell">
                  {r.password
                    ? <code>{r.password}</code>
                    : <span style={{ color: 'var(--text-muted)' }}>—</span>
                  }
                </td>
                <td><StatusBadge status={r.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
