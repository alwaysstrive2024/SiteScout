export default function SearchBar({ query, setQuery, onSearch, onKeyDown, loading, compact }) {
  return (
    <div className="search-box" style={compact ? { borderRadius: '14px' } : {}}>
      {/* Search icon */}
      <span className="search-icon" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </span>

      <input
        id="search-input"
        className="search-input"
        type="search"
        autoComplete="off"
        spellCheck="false"
        value={query}
        onChange={e => setQuery(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Search across your site pool…"
        aria-label="Search query"
        disabled={loading}
      />

      <button
        id="search-btn"
        className="search-btn"
        onClick={onSearch}
        disabled={loading || !query.trim()}
        aria-label="Run search"
      >
        {loading ? 'Scouting…' : 'Scout →'}
      </button>
    </div>
  )
}
