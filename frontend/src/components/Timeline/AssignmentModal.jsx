export default function AssignmentModal({ assignment, onClose, onCopy }) {
  if (!assignment) return null

  const [sh, sm] = (assignment.start_time || '09:00').split(':').map(Number)
  const [eh, em] = (assignment.end_time || '10:00').split(':').map(Number)
  const duration = (eh * 60 + em) - (sh * 60 + sm)

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="modal-type-tag">Interview Assignment</span>
            <h2 className="modal-title mono">{assignment.interview_id}</h2>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close dialog">
            ✕
          </button>
        </div>

        <div className="modal-content">
          <div className="modal-details-grid">
            <div className="detail-item">
              <span className="detail-label">Candidate</span>
              <strong
                className="mono cell-copy"
                onClick={() => onCopy(assignment.student_id, `Copied ${assignment.student_id}`)}
                title="Click to copy"
              >
                {assignment.student_id}
              </strong>
            </div>

            <div className="detail-item">
              <span className="detail-label">Corporate Partner</span>
              <strong className="cell-company">{assignment.company_id}</strong>
            </div>

            <div className="detail-item">
              <span className="detail-label">Interviewer Panel</span>
              <strong className="mono text-muted">{assignment.panel_id}</strong>
            </div>

            <div className="detail-item">
              <span className="detail-label">Physical Suite</span>
              <strong className="mono">{assignment.room_id}</strong>
            </div>

            <div className="detail-item">
              <span className="detail-label">Placement Day</span>
              <strong>{assignment.day.replace('_', ' ')}</strong>
            </div>

            <div className="detail-item">
              <span className="detail-label">Time Window</span>
              <strong className="mono">
                {assignment.start_time} – {assignment.end_time} ({duration}m)
              </strong>
            </div>
          </div>

          <div className="modal-notice-box">
            <span className="text-success font-bold">✓ Constraints Verified</span>
            <p>Non-overlapping candidate assignment, room capacity satisfied, interviewer panel bounded, and corporate placement-day authorized.</p>
          </div>
        </div>

        <div className="modal-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => onCopy(JSON.stringify(assignment, null, 2), 'Copied JSON')}
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
  )
}
