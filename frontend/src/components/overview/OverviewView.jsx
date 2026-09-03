export default function OverviewView({
  metrics,
  generated,
  onNavigate,
}) {
  const total = metrics.total_interviews || 859
  const scheduled = metrics.scheduled_interviews || 0
  const unscheduled = metrics.unscheduled_interviews || 0
  const completionRate = (metrics.completion_rate * 100).toFixed(2)

  return (
    <div className="overview-view">
      {/* 1. FOUR EXECUTIVE METRICS */}
      <div className="metrics-strip">
        <div className="metric-cell">
          <span className="metric-label">Total Workload</span>
          <strong className="metric-number">{total}</strong>
          <span className="metric-caption">Requested interview slots</span>
        </div>

        <div className="metric-cell">
          <span className="metric-label">Scheduled</span>
          <strong className={`metric-number ${generated ? 'text-success' : 'text-muted'}`}>
            {generated ? scheduled : '—'}
          </strong>
          <span className="metric-caption">
            {generated ? 'Allocated with zero conflicts' : 'Pending generation'}
          </span>
        </div>

        <div className="metric-cell">
          <span className="metric-label">Unscheduled</span>
          <strong className={`metric-number ${generated && unscheduled > 0 ? 'text-warning' : 'text-muted'}`}>
            {generated ? unscheduled : '—'}
          </strong>
          <span className="metric-caption">
            {generated ? 'Capacity bottleneck' : 'Pending generation'}
          </span>
        </div>

        <div className="metric-cell">
          <span className="metric-label">Completion Rate</span>
          <strong className={`metric-number ${generated ? 'text-accent' : 'text-muted'}`}>
            {generated ? `${completionRate}%` : '—'}
          </strong>
          <span className="metric-caption">
            {generated ? 'Deterministic placement rate' : 'Pending generation'}
          </span>
        </div>
      </div>

      {/* 2. OPERATIONAL SUMMARY & QUICK WORKSPACES */}
      <div className="overview-grid">
        {/* Left: Constraint Guarantees */}
        <div className="overview-section-box">
          <div className="section-header-row">
            <h3 className="section-title">Constraint Satisfaction</h3>
          </div>


          <div className="constraint-checklist">
            <div className="checklist-item">
              <span className="check-bullet">✓</span>
              <div className="check-body">
                <strong>Zero Candidate Time Conflicts</strong>
                <p>No student is assigned overlapping interview sessions across companies or days.</p>
              </div>
            </div>

            <div className="checklist-item">
              <span className="check-bullet">✓</span>
              <div className="check-body">
                <strong>Physical Room Capacity Enforced</strong>
                <p>Allocation strictly respects 20 physical interview suites with zero double-booking.</p>
              </div>
            </div>

            <div className="checklist-item">
              <span className="check-bullet">✓</span>
              <div className="check-body">
                <strong>Panel Concurrency Bounds</strong>
                <p>Interviews are distributed across 85 corporate interviewer panels within operational hours.</p>
              </div>
            </div>

            <div className="checklist-item">
              <span className="check-bullet">✓</span>
              <div className="check-body">
                <strong>Placement Day Authorization</strong>
                <p>Company interviews strictly occur on days authorized for each corporate partner.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Quick Links */}
        <div className="overview-section-box">
          <div className="section-header-row">
            <h3 className="section-title">Operational Workspaces</h3>
          </div>

          <div className="quick-workspace-list">
            <div
              className="workspace-link-item"
              onClick={() => onNavigate('SCHEDULE')}
              role="button"
              tabIndex={0}
            >
              <div>
                <strong>Schedule Explorer</strong>
                <p>Search, filter by company/room, sort, and export schedule records.</p>
              </div>
              <span className="arrow-icon">→</span>
            </div>

            <div
              className="workspace-link-item"
              onClick={() => onNavigate('TIMELINE')}
              role="button"
              tabIndex={0}
            >
              <div>
                <strong>Visual Timeline</strong>
                <p>Gantt chart view of 09:00–16:00 interview blocks across rooms and panels.</p>


              </div>
              <span className="arrow-icon">→</span>
            </div>

            <div
              className="workspace-link-item"
              onClick={() => onNavigate('ANALYTICS')}
              role="button"
              tabIndex={0}
            >
              <div>
                <strong>Analytics & Utilization</strong>
                <p>Inspect hourly concurrency, room efficiency rankings, and partner quotas.</p>
              </div>
              <span className="arrow-icon">→</span>
            </div>

            <div
              className="workspace-link-item"
              onClick={() => onNavigate('REPLANNING')}
              role="button"
              tabIndex={0}
            >
              <div>
                <strong>Disruption Replanning</strong>
                <p>Simulate room outages or delays and compute deterministic schedule diffs.</p>
              </div>
              <span className="arrow-icon">→</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
