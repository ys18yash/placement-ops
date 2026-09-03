export default function Hero({
  onGenerate,
  loading,
  generated,
  generateLatency,
  seed,
}) {
  return (
    <section className="hero-section">
      <div className="hero-left">
        <span className="hero-eyebrow">PLACEMENT OPERATIONS</span>
        <h1 className="hero-title">
          Deterministic Placement<br />Scheduling Engine
        </h1>

        <p className="hero-subtitle">
          Constraint-aware interview scheduling and deterministic replanning across students, companies, panels and rooms.
        </p>


        <div className="hero-meta-row">
          <span>Seed: <strong className="mono">{seed || '20260829'}</strong></span>
          <span className="meta-sep">·</span>
          <span>Engine: <strong className="text-success">Live</strong></span>
          {generated && generateLatency !== null && (
            <>
              <span className="meta-sep">·</span>
              <span>Runtime: <strong className="mono">{generateLatency}ms</strong></span>
            </>
          )}
        </div>
      </div>

      <div className="hero-right">
        <button
          type="button"
          className="btn-hero-primary"
          onClick={onGenerate}
          disabled={loading}
          id="generate-schedule-btn"
        >
          {loading ? (
            <>
              <span className="spinner-icon" />
              <span>Generating Schedule…</span>
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                <polygon points="6 3 20 12 6 21 6 3"></polygon>
              </svg>
              <span>Generate Schedule</span>
            </>
          )}
        </button>
      </div>
    </section>

  )
}
