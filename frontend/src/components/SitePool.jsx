import { useState } from 'react'

function normalizeDomain(raw) {
  return raw
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, '')
    .replace(/\/+$/, '')
}

export default function SitePool({ domains, setDomains }) {
  const [input, setInput] = useState('')
  const [shake, setShake] = useState(false)

  const addDomain = () => {
    const d = normalizeDomain(input)
    if (!d) return
    if (domains.includes(d)) {
      // Briefly animate to signal duplicate
      setShake(true)
      setTimeout(() => setShake(false), 400)
      setInput('')
      return
    }
    setDomains(prev => [...prev, d])
    setInput('')
  }

  const removeDomain = (d) => setDomains(prev => prev.filter(x => x !== d))

  const handleKeyDown = (e) => { if (e.key === 'Enter') addDomain() }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div className="setting-label">
        Site Pool
        <span style={{ fontSize: '.72rem', fontWeight: 400, color: 'var(--text-muted)', letterSpacing: 0 }}>
          {domains.length} domain{domains.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="site-pool-input-row">
        <input
          id="domain-input"
          className="site-pool-input"
          type="url"
          placeholder="e.g. sspai.com"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Add domain"
          style={shake ? { animation: 'shakeX .3s ease' } : {}}
        />
        <button
          id="add-domain-btn"
          className="add-domain-btn"
          onClick={addDomain}
          disabled={!input.trim()}
        >
          + Add
        </button>
      </div>

      {domains.length === 0 ? (
        <p style={{ fontSize: '.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
          No domains added. Add at least one.
        </p>
      ) : (
        <div className="domain-tags">
          {domains.map(d => (
            <span key={d} className="domain-tag">
              <span>{d}</span>
              <button
                className="tag-remove"
                onClick={() => removeDomain(d)}
                aria-label={`Remove ${d}`}
                title="Remove"
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}

      {/* inline keyframe for shake (won't conflict with global CSS) */}
      <style>{`
        @keyframes shakeX {
          0%,100%{transform:translateX(0)}
          25%{transform:translateX(-5px)}
          75%{transform:translateX(5px)}
        }
      `}</style>
    </div>
  )
}
