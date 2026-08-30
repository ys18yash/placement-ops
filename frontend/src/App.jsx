import { useMemo, useState } from 'react'
import './App.css'

const EMPTY_METRICS = {
  total_interviews: 0,
  scheduled_interviews: 0,
  unscheduled_interviews: 0,
  completion_rate: 0,
  room_utilization: 0,
  panel_utilization: 0,
  schedule_span: {
    days_used: 0,
    total_minutes: 0,
    by_day: {},
  },
}

const DISRUPTION_TYPES = [
  {
    value: 'PANEL_DROPOUT',
    label: 'Panel Dropout',
    resourceLabel: 'Panel',
    resourcePlaceholder: 'e.g. PANEL-COMP027-01',
  },
  {
    value: 'ROOM_UNAVAILABLE',
    label: 'Room Unavailable',
    resourceLabel: 'Room',
    resourcePlaceholder: 'e.g. ROOM001',
  },
  {
    value: 'STUDENT_WITHDRAWAL',
    label: 'Student Withdrawal',
    resourceLabel: 'Student',
    resourcePlaceholder: 'e.g. STU0595',
  },
  {
    value: 'COMPANY_DELAY',
    label: 'Company Delay',
    resourceLabel: 'Company',
    resourcePlaceholder: 'e.g. COMP027',
  },
]

function formatPercent(value) {
  return `${(Number(value) * 100).toFixed(2)}%`
}

function formatTimeRange(start, end) {
  if (!start || !end) return '—'
  return `${start} – ${end}`
}

async function parseResponse(response, fallbackMessage) {
  if (response.ok) {
    return response.json()
  }

  let message = `${fallbackMessage} (${response.status})`

  try {
    const body = await response.json()
    if (body.detail) {
      message = body.detail
    }
  } catch {
    // Keep fallback message.
  }

  throw new Error(message)
}

function App() {
  const [metrics, setMetrics] = useState(EMPTY_METRICS)
  const [assignments, setAssignments] = useState([])
  const [unscheduledIds, setUnscheduledIds] = useState([])
  const [loading, setLoading] = useState(false)
  const [replanning, setReplanning] = useState(false)
  const [error, setError] = useState('')
  const [generated, setGenerated] = useState(false)

  const [disruptionType, setDisruptionType] = useState('ROOM_UNAVAILABLE')
  const [disruptionDay, setDisruptionDay] = useState('DAY_1')
  const [resourceId, setResourceId] = useState('ROOM001')
  const [effectiveTime, setEffectiveTime] = useState('')
  const [details, setDetails] = useState('')

  const [replanResult, setReplanResult] = useState(null)

  const selectedDisruption = useMemo(
    () =>
      DISRUPTION_TYPES.find((item) => item.value === disruptionType) ||
      DISRUPTION_TYPES[0],
    [disruptionType],
  )

  async function generateSchedule() {
    setLoading(true)
    setError('')
    setReplanResult(null)

    try {
      const response = await fetch('/api/schedule/generate', {
        method: 'POST',
      })

      const data = await parseResponse(
        response,
        'Schedule generation failed',
      )

      setMetrics({
        ...EMPTY_METRICS,
        ...(data.metrics || {}),
        schedule_span: {
          ...EMPTY_METRICS.schedule_span,
          ...(data.metrics?.schedule_span || {}),
        },
      })

      setAssignments(
        Array.isArray(data.schedule?.assignments)
          ? data.schedule.assignments
          : [],
      )

      setUnscheduledIds(
        Array.isArray(data.schedule?.unscheduled_interview_ids)
          ? data.schedule.unscheduled_interview_ids
          : [],
      )

      setGenerated(true)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to generate schedule.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function replanSchedule() {
    setReplanning(true)
    setError('')

    try {
      const response = await fetch('/api/schedule/replan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          seed: 20260829,
          disruption: {
            id: `UI-${disruptionType}`,
            type: disruptionType,
            day: disruptionDay,
            effective_time: effectiveTime || null,
            resource_id: resourceId || null,
            details: details || null,
          },
        }),
      })

      const data = await parseResponse(
        response,
        'Schedule replanning failed',
      )

      setReplanResult(data)

      setMetrics({
        ...EMPTY_METRICS,
        ...(data.replanned_metrics || {}),
        schedule_span: {
          ...EMPTY_METRICS.schedule_span,
          ...(data.replanned_metrics?.schedule_span || {}),
        },
      })

      setAssignments(
        Array.isArray(data.replanned_schedule?.assignments)
          ? data.replanned_schedule.assignments
          : [],
      )

      setUnscheduledIds(
        Array.isArray(data.replanned_schedule?.unscheduled_interview_ids)
          ? data.replanned_schedule.unscheduled_interview_ids
          : [],
      )

      setGenerated(true)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to replan schedule.',
      )
    } finally {
      setReplanning(false)
    }
  }

  const daySummary = useMemo(() => {
    const byDay = metrics.schedule_span?.by_day || {}

    return Object.entries(byDay).map(([day, minutes]) => ({
      day,
      minutes,
    }))
  }, [metrics])

  const replanningMetrics = replanResult?.replanning_metrics

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>PlacementOps</h1>
          <p>Constraint-aware placement scheduling platform</p>
        </div>

        <div className="status">
          <span className="status-dot" />
          API connected
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <div className="eyebrow">SCHEDULING OPERATIONS</div>

            <h2>Manage placement interviews with confidence.</h2>

            <p>
              Generate a validated interview schedule and replan it when
              panels, rooms, students, or companies become unavailable.
            </p>
          </div>

          <button
            type="button"
            className="generate-button"
            onClick={generateSchedule}
            disabled={loading || replanning}
          >
            {loading ? 'Generating…' : 'Generate Schedule'}
          </button>
        </section>

        {error && (
          <section className="error-banner" role="alert">
            <strong>Operation failed</strong>
            <span>{error}</span>
          </section>
        )}

        <section className="metrics-grid">
          <MetricCard
            label="Total Interviews"
            value={metrics.total_interviews}
            detail="Input workload"
          />

          <MetricCard
            label="Scheduled"
            value={metrics.scheduled_interviews}
            detail="Successfully assigned"
          />

          <MetricCard
            label="Unscheduled"
            value={metrics.unscheduled_interviews}
            detail="Require attention"
            warning={metrics.unscheduled_interviews > 0}
          />

          <MetricCard
            label="Completion Rate"
            value={formatPercent(metrics.completion_rate)}
            detail="Scheduled / total"
          />
        </section>

        <section className="content-grid">
          <div className="main-column">
            <section className="panel disruption-panel">
              <div className="panel-header">
                <div>
                  <h3>Disruption & Replanning</h3>
                  <p>
                    Simulate an operational disruption and automatically
                    rebuild the affected schedule.
                  </p>
                </div>

                <span className="simulation-badge">SIMULATION</span>
              </div>

              <div className="disruption-form">
                <div className="form-field">
                  <label htmlFor="disruption-type">
                    Disruption type
                  </label>

                  <select
                    id="disruption-type"
                    value={disruptionType}
                    onChange={(event) =>
                      setDisruptionType(event.target.value)
                    }
                  >
                    {DISRUPTION_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-field">
                  <label htmlFor="disruption-day">Day</label>

                  <select
                    id="disruption-day"
                    value={disruptionDay}
                    onChange={(event) =>
                      setDisruptionDay(event.target.value)
                    }
                  >
                    <option value="DAY_1">DAY 1</option>
                    <option value="DAY_2">DAY 2</option>
                    <option value="DAY_3">DAY 3</option>
                    <option value="DAY_4">DAY 4</option>
                    <option value="DAY_5">DAY 5</option>
                  </select>
                </div>

                <div className="form-field">
                  <label htmlFor="resource-id">
                    {selectedDisruption.resourceLabel}
                  </label>

                  <input
                    id="resource-id"
                    value={resourceId}
                    onChange={(event) =>
                      setResourceId(event.target.value)
                    }
                    placeholder={selectedDisruption.resourcePlaceholder}
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="effective-time">
                    Effective time
                  </label>

                  <input
                    id="effective-time"
                    type="time"
                    value={effectiveTime}
                    onChange={(event) =>
                      setEffectiveTime(event.target.value)
                    }
                  />
                </div>

                <div className="form-field form-field-wide">
                  <label htmlFor="details">Details</label>

                  <input
                    id="details"
                    value={details}
                    onChange={(event) => setDetails(event.target.value)}
                    placeholder="Optional disruption details"
                  />
                </div>

                <button
                  type="button"
                  className="replan-button"
                  onClick={replanSchedule}
                  disabled={replanning}
                >
                  {replanning ? 'Replanning…' : 'Replan Schedule'}
                </button>
              </div>
            </section>

            {replanResult && (
              <section className="panel replan-summary">
                <div className="panel-header">
                  <div>
                    <h3>Replanning Result</h3>
                    <p>
                      {replanResult.disruption?.type || disruptionType}
                      {' · '}
                      {replanResult.disruption?.day || disruptionDay}
                    </p>
                  </div>
                </div>

                <div className="replan-stats">
                  <ResultStat
                    label="Original"
                    value={replanResult.original_schedule?.assignments?.length ?? 0}
                  />

                  <ResultStat
                    label="Replanned"
                    value={
                      replanResult.replanned_schedule?.assignments?.length ?? 0
                    }
                  />

                  <ResultStat
                    label="Changes"
                    value={replanningMetrics?.changes ?? 0}
                  />

                  <ResultStat
                    label="Rescheduled"
                    value={replanningMetrics?.rescheduled ?? 0}
                  />

                  <ResultStat
                    label="Unscheduled"
                    value={replanningMetrics?.unscheduled ?? 0}
                    warning={(replanningMetrics?.unscheduled ?? 0) > 0}
                  />

                  <ResultStat
                    label="Conflicts"
                    value={replanningMetrics?.conflicts ?? 0}
                    warning={(replanningMetrics?.conflicts ?? 0) > 0}
                  />
                </div>

                <div className="changes-section">
                  <div className="changes-heading">
                    <div>
                      <h4>Schedule Changes</h4>
                      <p>
                        Interviews considered during this disruption.
                      </p>
                    </div>

                    <span className="change-count">
                      {Array.isArray(replanResult.changes)
                        ? replanResult.changes.length
                        : 0}{' '}
                      records
                    </span>
                  </div>

                  {!Array.isArray(replanResult.changes) ||
                  replanResult.changes.length === 0 ? (
                    <div className="small-empty">
                      No change records returned.
                    </div>
                  ) : (
                    <div className="changes-list">
                      {replanResult.changes
                        .slice(0, 20)
                        .map((change) => (
                          <ChangeRow
                            key={change.interview_id}
                            change={change}
                          />
                        ))}
                    </div>
                  )}

                  {Array.isArray(replanResult.changes) &&
                    replanResult.changes.length > 20 && (
                      <div className="table-footer">
                        Showing 20 of {replanResult.changes.length} change
                        records
                      </div>
                    )}
                </div>
              </section>
            )}

            <section className="panel">
              <div className="panel-header">
                <div>
                  <h3>Schedule Overview</h3>
                  <p>
                    {generated
                      ? `${assignments.length} assignments returned by the scheduler`
                      : 'Generate a schedule to view assignments'}
                  </p>
                </div>
              </div>

              {!generated ? (
                <EmptyState
                  icon="↗"
                  title="No schedule generated"
                  description="Run the scheduler to populate interview assignments and operational metrics."
                />
              ) : assignments.length === 0 ? (
                <EmptyState
                  icon="!"
                  title="No assignments returned"
                  description="The scheduler completed, but no scheduled interviews were returned."
                />
              ) : (
                <div className="table-wrapper">
                  <table className="assignments-table">
                    <thead>
                      <tr>
                        <th>Interview</th>
                        <th>Student</th>
                        <th>Company</th>
                        <th>Panel</th>
                        <th>Room</th>
                        <th>Day</th>
                        <th>Time</th>
                      </tr>
                    </thead>

                    <tbody>
                      {assignments.slice(0, 50).map((assignment) => (
                        <tr key={assignment.interview_id}>
                          <td className="mono">
                            {assignment.interview_id}
                          </td>
                          <td>{assignment.student_id}</td>
                          <td>{assignment.company_id}</td>
                          <td>{assignment.panel_id}</td>
                          <td>{assignment.room_id}</td>
                          <td>
                            <span className="day-badge">
                              {assignment.day}
                            </span>
                          </td>
                          <td className="time">
                            {formatTimeRange(
                              assignment.start_time,
                              assignment.end_time,
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {assignments.length > 50 && (
                    <div className="table-footer">
                      Showing 50 of {assignments.length} scheduled interviews
                    </div>
                  )}
                </div>
              )}
            </section>
          </div>

          <div className="side-column">
            <section className="panel utilization-panel">
              <div className="panel-header">
                <div>
                  <h3>Resource Utilization</h3>
                  <p>Current generated schedule</p>
                </div>
              </div>

              <div className="utilization-content">
                <UtilizationRow
                  label="Room utilization"
                  value={metrics.room_utilization}
                />

                <UtilizationRow
                  label="Panel utilization"
                  value={metrics.panel_utilization}
                />
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <div>
                  <h3>Schedule Span</h3>
                  <p>Time allocated across placement days</p>
                </div>
              </div>

              <div className="day-list">
                {daySummary.length === 0 ? (
                  <div className="small-empty">
                    No schedule data yet.
                  </div>
                ) : (
                  daySummary.map(({ day, minutes }) => (
                    <div className="day-row" key={day}>
                      <div>
                        <strong>{day.replace('_', ' ')}</strong>
                        <span>{minutes} minutes</span>
                      </div>

                      <span className="day-duration">
                        {Math.round(minutes / 60)}h
                      </span>
                    </div>
                  ))
                )}
              </div>
            </section>

            <section className="panel attention-panel">
              <div className="panel-header">
                <div>
                  <h3>Needs Attention</h3>
                  <p>Interviews without a schedule slot</p>
                </div>
              </div>

              <div className="attention-content">
                <strong>{unscheduledIds.length}</strong>

                <span>
                  {unscheduledIds.length === 1
                    ? 'interview remains unscheduled'
                    : 'interviews remain unscheduled'}
                </span>
              </div>
            </section>
          </div>
        </section>
      </main>
    </div>
  )
}

function MetricCard({ label, value, detail, warning = false }) {
  return (
    <article
      className={`metric-card ${warning ? 'metric-warning' : ''}`}
    >
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  )
}

function ResultStat({ label, value, warning = false }) {
  return (
    <div className={`result-stat ${warning ? 'result-warning' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function UtilizationRow({ label, value }) {
  const percentage = Number(value) * 100

  return (
    <div className="utilization-row">
      <div className="utilization-label">
        <span>{label}</span>
        <strong>{formatPercent(value)}</strong>
      </div>

      <div className="progress-track">
        <div
          className="progress-value"
          style={{
            width: `${Math.min(Math.max(percentage, 0), 100)}%`,
          }}
        />
      </div>
    </div>
  )
}

function ChangeRow({ change }) {
  const oldAssignment = change.old_assignment
  const newAssignment = change.new_assignment

  const changeType = change.change_type || 'UNKNOWN'
  const isChanged = changeType !== 'UNCHANGED'

  return (
    <article className={`change-row ${isChanged ? 'is-changed' : ''}`}>
      <div className="change-main">
        <div className="change-title">
          <span className="mono">{change.interview_id}</span>

          <span className={`change-badge ${changeType.toLowerCase()}`}>
            {changeType.replaceAll('_', ' ')}
          </span>
        </div>

        <p>{change.reason || 'No reason provided.'}</p>
      </div>

      <div className="change-assignment">
        <div>
          <span>Original</span>
          <strong>
            {oldAssignment
              ? `${oldAssignment.day} · ${formatTimeRange(
                  oldAssignment.start_time,
                  oldAssignment.end_time,
                )}`
              : 'Unscheduled'}
          </strong>
        </div>

        <div className="change-arrow">→</div>

        <div>
          <span>New</span>
          <strong>
            {newAssignment
              ? `${newAssignment.day} · ${formatTimeRange(
                  newAssignment.start_time,
                  newAssignment.end_time,
                )}`
              : 'Unscheduled'}
          </strong>
        </div>
      </div>
    </article>
  )
}

function EmptyState({ icon, title, description }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <h4>{title}</h4>
      <p>{description}</p>
    </div>
  )
}

export default App