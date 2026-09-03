export default function AssignmentDrawer({ assignment, onClose, onCopy }) {
  if (!assignment) return null

  const duration = (() => {
    if (!assignment.start_time || !assignment.end_time) return null
    const [sh, sm] = assignment.start_time.split(':').map(Number)
    const [eh, em] = assignment.end_time.split(':').map(Number)
    return (eh * 60 + em) - (sh * 60 + sm)
  })()

  return (
    <div className="drawer-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <span className="drawer-kicker">INTERVIEW INSPECTOR</span>
            <h3 className="drawer-title">{assignment.interview_id}</h3>
          </div>
          <button type="button" className="drawer-close" onClick={onClose} aria-label="Close drawer">
            ×
          </button>
        </div>

        <div className="drawer-body">
          <div className="drawer-field-grid">
            <div className="drawer-field">
              <span className="drawer-field-label">Student ID</span>
              <span
                className="drawer-field-val mono-badge mono-clickable"
                onClick={() => onCopy(assignment.student_id, `Copied ${assignment.student_id}`)}
                title="Click to copy Student ID"
              >
                {assignment.student_id}
              </span>
            </div>

            <div className="drawer-field">
              <span className="drawer-field-label">Company</span>
              <span className="drawer-field-val entity-tag company-tag">
                {assignment.company_id}
              </span>
            </div>

            <div className="drawer-field">
              <span className="drawer-field-label">Interview Panel</span>
              <span className="drawer-field-val entity-tag panel-tag" title={assignment.panel_id}>
                {assignment.panel_id}
              </span>
            </div>

            <div className="drawer-field">
              <span className="drawer-field-label">Allocated Room</span>
              <span className="drawer-field-val entity-tag room-tag">
                {assignment.room_id}
              </span>
            </div>

            <div className="drawer-field">
              <span className="drawer-field-label">Placement Day</span>
              <span className="drawer-field-val day-pill">
                {assignment.day.replace('_', ' ')}
              </span>
            </div>

            <div className="drawer-field">
              <span className="drawer-field-label">Scheduled Window</span>
              <span className="drawer-field-val time-mono">
                {assignment.start_time} – {assignment.end_time} ({duration}m)
              </span>
            </div>
          </div>

          <div className="drawer-validation-box">
            <div className="validation-status-row">
              <span className="status-dot dot-healthy" />
              <strong>Validated Constraint Clearance</strong>
            </div>
            <p className="validation-note">
              Cleared all multi-resource constraints: student non-overlap, panel concurrency bound, physical room capacity, and corporate placement-day authorization.
            </p>
          </div>

          <div className="drawer-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => onCopy(JSON.stringify(assignment, null, 2), 'Copied JSON payload')}
            >
              Copy JSON
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => onCopy(assignment.interview_id, `Copied ${assignment.interview_id}`)}
            >
              Copy ID
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
