const TEMPLATES = [
  {
    id: 'dev',
    icon: '⚙️',
    label: 'Dev Mode',
    desc: 'Code & engineering',
    domains: ['github.com', 'stackoverflow.com', 'dev.to', 'news.ycombinator.com'],
    accent: 'var(--accent)',
  },
  {
    id: 'resource',
    icon: '📦',
    label: 'Resource Mode',
    desc: 'Community & downloads',
    domains: ['reddit.com', 'v2ex.com', 'sspai.com', 'hostloc.com'],
    accent: 'var(--accent-cyan)',
  },
  {
    id: 'academic',
    icon: '🎓',
    label: 'Academic Mode',
    desc: 'Papers & research',
    domains: ['arxiv.org', 'semanticscholar.org', 'papers.with.code', 'huggingface.co'],
    accent: 'var(--success)',
  },
]

export default function QuickTemplates({ onApply, activeTemplate }) {
  return (
    <div className="quick-templates">
      <span className="qt-label">Quick Templates</span>
      <div className="qt-buttons">
        {TEMPLATES.map(t => (
          <button
            key={t.id}
            id={`template-${t.id}`}
            className={`qt-btn ${activeTemplate === t.id ? 'qt-btn--active' : ''}`}
            style={{ '--template-accent': t.accent }}
            onClick={() => onApply(t)}
            title={t.domains.join(', ')}
          >
            <span className="qt-icon">{t.icon}</span>
            <span className="qt-text">
              <span className="qt-name">{t.label}</span>
              <span className="qt-desc">{t.desc}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
