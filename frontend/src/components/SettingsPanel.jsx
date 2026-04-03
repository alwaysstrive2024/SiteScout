const MODELS = [
  { value: 'deepseek-chat',  label: '🧠 DeepSeek Chat',  hint: 'Fast · Cost-efficient' },
  { value: 'gpt-4o',        label: '✨ GPT-4o',          hint: 'Powerful · Precise' },
  { value: 'gpt-4o-mini',   label: '⚡ GPT-4o Mini',     hint: 'Fast · Affordable' },
]

export default function SettingsPanel({ rawN, setRawN, llmK, setLlmK, modelChoice, setModelChoice }) {
  return (
    <>
      {/* Raw N slider */}
      <div className="setting-group">
        <label className="setting-label" htmlFor="raw-n-slider">
          Raw N
          <span className="setting-value">{rawN}</span>
        </label>
        <input
          id="raw-n-slider"
          className="slider"
          type="range"
          min={1} max={50} step={1}
          value={rawN}
          onChange={e => setRawN(Number(e.target.value))}
          style={{ '--pct': `${((rawN - 1) / 49) * 100}%` }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.72rem', color: 'var(--text-muted)' }}>
          <span>1</span><span>Results per domain</span><span>50</span>
        </div>
      </div>

      {/* LLM K slider */}
      <div className="setting-group">
        <label className="setting-label" htmlFor="llm-k-slider">
          LLM K
          <span className="setting-value">{llmK}</span>
        </label>
        <input
          id="llm-k-slider"
          className="slider"
          type="range"
          min={1} max={20} step={1}
          value={llmK}
          onChange={e => setLlmK(Number(e.target.value))}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.72rem', color: 'var(--text-muted)' }}>
          <span>1</span><span>Top results sent to AI</span><span>20</span>
        </div>
      </div>

      {/* Model selector */}
      <div className="setting-group full-width">
        <label className="setting-label" htmlFor="model-select">
          AI Model
          <span style={{ fontSize: '.72rem', fontWeight: 400, color: 'var(--text-muted)', letterSpacing: 0 }}>
            {MODELS.find(m => m.value === modelChoice)?.hint}
          </span>
        </label>
        <select
          id="model-select"
          className="model-select"
          value={modelChoice}
          onChange={e => setModelChoice(e.target.value)}
        >
          {MODELS.map(m => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
      </div>
    </>
  )
}
