import { useEffect, useState } from 'react'

const PHASES = [
  { icon: '🌐', label: 'Dispatching parallel searches',  detail: 'Firing site: queries across your domain pool' },
  { icon: '⚡', label: 'Fetching raw results',           detail: 'Collecting and deduplicating search hits' },
  { icon: '🧠', label: 'AI is refining',                 detail: 'LLM extracting links, passwords & status' },
]

// Cycle through phases every ~2.5s to give real-time feedback feel
function useLoadingPhase(loading) {
  const [phase, setPhase] = useState(0)
  useEffect(() => {
    if (!loading) { setPhase(0); return }
    const id = setInterval(() => setPhase(p => Math.min(p + 1, PHASES.length - 1)), 2500)
    return () => clearInterval(id)
  }, [loading])
  return phase
}

export default function LoadingState({ loading, domains = [] }) {
  const phase = useLoadingPhase(loading)
  if (!loading) return null

  return (
    <div className="loading-state" role="status" aria-live="polite">
      {/* Radar animation */}
      <div className="radar-wrap">
        <div className="radar-ring r1" />
        <div className="radar-ring r2" />
        <div className="radar-ring r3" />
        <div className="radar-sweep" />
        <div className="radar-dot" />
      </div>

      {/* Phase steps */}
      <div className="loading-phases">
        {PHASES.map((p, i) => {
          const state = i < phase ? 'done' : i === phase ? 'active' : 'pending'
          return (
            <div key={i} className={`loading-phase loading-phase--${state}`}>
              <span className="phase-icon">
                {state === 'done' ? '✅' : p.icon}
              </span>
              <div className="phase-text">
                <span className="phase-label">{p.label}</span>
                {state === 'active' && (
                  <span className="phase-detail">{p.detail}<span className="loading-dots" /></span>
                )}
              </div>
              {state === 'active' && <div className="phase-spinner" />}
            </div>
          )
        })}
      </div>

      {/* Domain pills */}
      {domains.length > 0 && (
        <div className="loading-domains">
          <span className="loading-domains-label">Scouting</span>
          {domains.map(d => (
            <span key={d} className="loading-domain-pill">{d}</span>
          ))}
        </div>
      )}
    </div>
  )
}
