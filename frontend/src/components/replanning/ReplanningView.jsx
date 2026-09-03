import { useMemo, useState } from 'react'

const DISRUPTION_TYPES = [
  {
    value: 'ROOM_UNAVAILABLE',
    label: 'Room Unavailable',
    resourceLabel: 'Room ID',
    defaultResource: 'ROOM001',
    supportsEffectiveTime: false,
    description: 'Marks an entire physical room unavailable for a placement day. Affected interviews must be moved to another room or unscheduled.',
  },
  {
    value: 'COMPANY_DELAY',
    label: 'Company Delay',
    resourceLabel: 'Company ID',
    defaultResource: 'COMP001',
    supportsEffectiveTime: true,
    description: 'Delays corporate interviews on a given day until an effective start time. Interviews before this time must be rescheduled.',
  },
  {
    value: 'PANEL_DROPOUT',
    label: 'Panel Dropout',
    resourceLabel: 'Panel ID',
    defaultResource: 'PANEL-COMP001-01',
    supportsEffectiveTime: false,
    description: 'Marks an interviewer panel unavailable for the entire placement day. Workload is shifted to remaining company panels.',
  },
  {
    value: 'STUDENT_WITHDRAWAL',
    label: 'Student Withdrawal',
    resourceLabel: 'Student ID',
    defaultResource: 'STU0001',
    supportsEffectiveTime: false,
    description: 'Withdraws a candidate from the placement drive, releasing occupied rooms and interviewer panels for other interviews.',
  },
]

const TIME_15_MIN_OPTIONS = [
  '09:00', '09:15', '09:30', '09:45',
  '10:00', '10:15', '10:30', '10:45',
  '11:00', '11:15', '11:30', '11:45',
  '12:00', '12:15', '12:30', '12:45',
  '13:00', '13:15', '13:30', '13:45',
  '14:00', '14:15', '14:30', '14:45',
  '15:00', '15:15', '15:30', '15:45',
  '16:00', '16:15', '16:30', '16:45',
  '17:00', '17:15', '17:30', '17:45',
  '18:00',
]

const QUICK_PRESETS = [
  {
    title: 'Room 1 Outage',
    type: 'ROOM_UNAVAILABLE',
    day: 'DAY_1',
    resourceId: 'ROOM001',
    effectiveTime: '10:00',
    details: 'Lab power failure',
  },
  {
    title: 'Company 1 Delay (10:00)',
    type: 'COMPANY_DELAY',
    day: 'DAY_1',
    resourceId: 'COMP001',
    effectiveTime: '10:00',
    details: 'Corporate flight delay',
  },
  {
    title: 'Panel 1 Dropout',
    type: 'PANEL_DROPOUT',
    day: 'DAY_1',
    resourceId: 'PANEL-COMP001-01',
    effectiveTime: '10:00',
    details: 'Interviewer emergency',
  },
  {
    title: 'Student 1 Withdrawal',
    type: 'STUDENT_WITHDRAWAL',
    day: 'DAY_1',
    resourceId: 'STU0001',
    effectiveTime: '10:00',
    details: 'Accepted external offer',
  },
]

export default function ReplanningView({
  replanResult,
  onReplan,
  replanning,
  replanLatency,
  generated,
  onGenerate,
  loading,
}) {
  const [disruptionType, setDisruptionType] = useState('ROOM_UNAVAILABLE')
  const [disruptionDay, setDisruptionDay] = useState('DAY_1')
  const [resourceId, setResourceId] = useState('ROOM001')
  const [effectiveTime, setEffectiveTime] = useState('10:00')
  const [details, setDetails] = useState('')

  const [filterType, setFilterType] = useState('ALL')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 25

  const selectedDisruption = useMemo(
    () => DISRUPTION_TYPES.find((d) => d.value === disruptionType) || DISRUPTION_TYPES[0],
    [disruptionType],
  )

  function handleTypeChange(val) {
    setDisruptionType(val)
    const conf = DISRUPTION_TYPES.find((d) => d.value === val)
    if (conf) setResourceId(conf.defaultResource)
  }

  function applyPreset(p) {
    setDisruptionType(p.type)
    setDisruptionDay(p.day)
    setResourceId(p.resourceId)
    setEffectiveTime(p.effectiveTime || '10:00')
    setDetails(p.details)
  }

  function handleSubmit(e) {
    e.preventDefault()
    onReplan({
      type: disruptionType,
      day: disruptionDay,
      resourceId: resourceId.trim(),
      effectiveTime: selectedDisruption.supportsEffectiveTime ? effectiveTime : null,
      details: details.trim() || null,
    })
  }

  const filteredChanges = useMemo(() => {
    const list = Array.isArray(replanResult?.changes) ? replanResult.changes : []
    return list.filter((c) => {
      if (filterType !== 'ALL' && c.change_type !== filterType) return false
      if (search.trim()) {
        const q = search.trim().toLowerCase()
        return (
          c.interview_id.toLowerCase().includes(q) ||
          (c.reason && c.reason.toLowerCase().includes(q)) ||
          (c.old_assignment && (
            c.old_assignment.student_id.toLowerCase().includes(q) ||
            c.old_assignment.company_id.toLowerCase().includes(q) ||
            c.old_assignment.panel_id.toLowerCase().includes(q) ||
            c.old_assignment.room_id.toLowerCase().includes(q)
          )) ||
          (c.new_assignment && (
            c.new_assignment.student_id.toLowerCase().includes(q) ||
            c.new_assignment.company_id.toLowerCase().includes(q) ||
            c.new_assignment.panel_id.toLowerCase().includes(q) ||
            c.new_assignment.room_id.toLowerCase().includes(q)
          ))
        )
      }
      return true
    })
  }, [replanResult, filterType, search])

  const paginatedChanges = filteredChanges.slice((page - 1) * pageSize, page * pageSize)
  const totalPages = Math.max(1, Math.ceil(filteredChanges.length / pageSize))

  const metrics = replanResult?.replanning_metrics

  if (!generated) {
    return (
      <div className="empty-state-card">
        <h3>No Base Schedule Available</h3>
        <p>A validated schedule must be generated before simulating disruptions and computing replanning diffs.</p>
        <button type="button" className="btn-primary" onClick={onGenerate} disabled={loading}>
          Generate Base Schedule
        </button>
      </div>
    )
  }

  return (
    <div className="replanning-view-container">
      {/* 1. DISRUPTION SIMULATION WORKSPACE */}
      <div className="replan-form-card">
        <div className="card-top-row">
          <div>
            <h3 className="section-title">Simulate Operational Disruption</h3>
            <p className="section-desc">Test real-time resilience and compute deterministic schedule adjustments with zero conflicts.</p>
          </div>

          {/* Quick Presets */}
          <div className="presets-list">
            <span className="presets-tag">Presets:</span>
            {QUICK_PRESETS.map((p) => (
              <button
                key={p.title}
                type="button"
                className="btn-preset"
                onClick={() => applyPreset(p)}
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="replan-controls-grid">
          <div className="form-field">
            <label htmlFor="rep-type">Disruption Type</label>
            <select
              id="rep-type"
              className="filter-select select-full"
              value={disruptionType}
              onChange={(e) => handleTypeChange(e.target.value)}
            >
              {DISRUPTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label htmlFor="rep-day">Placement Day</label>
            <select
              id="rep-day"
              className="filter-select select-full"
              value={disruptionDay}
              onChange={(e) => setDisruptionDay(e.target.value)}
            >
              <option value="DAY_1">Day 1</option>
              <option value="DAY_2">Day 2</option>
              <option value="DAY_3">Day 3</option>
              <option value="DAY_4">Day 4</option>
            </select>
          </div>

          <div className="form-field">
            <label htmlFor="rep-res">{selectedDisruption.resourceLabel}</label>
            <input
              id="rep-res"
              type="text"
              className="form-input"
              value={resourceId}
              onChange={(e) => setResourceId(e.target.value)}
              required
            />
          </div>

          {selectedDisruption.supportsEffectiveTime ? (
            <div className="form-field">
              <label htmlFor="rep-time">Effective Delay Time</label>
              <select
                id="rep-time"
                className="filter-select select-full"
                value={effectiveTime}
                onChange={(e) => setEffectiveTime(e.target.value)}
              >
                {TIME_15_MIN_OPTIONS.map((slot) => (
                  <option key={slot} value={slot}>{slot}</option>
                ))}
              </select>
            </div>
          ) : (
            <div className="form-field field-disabled">
              <label htmlFor="rep-time-na">Effective Time</label>
              <input id="rep-time-na" className="form-input" value="Full Day Outage" disabled />
            </div>
          )}

          <div className="form-field span-full">
            <label htmlFor="rep-details">Operational Context / Notes (Optional)</label>
            <input
              id="rep-details"
              type="text"
              className="form-input"
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="e.g. Lab power failure, interviewer delay…"
            />
          </div>

          <div className="replan-submit-row span-full">
            <p className="replan-note">{selectedDisruption.description}</p>
            <button
              type="submit"
              className="btn-primary btn-replan"
              disabled={replanning}
              id="replan-schedule-btn"
            >
              {replanning ? (
                <>
                  <span className="spinner-icon" />
                  <span>Computing Replan…</span>
                </>
              ) : (
                <span>Execute Deterministic Replan</span>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* 2. REPLANNING METRICS & DIFF VIEW */}
      {replanResult && (
        <div className="replan-results-container">
          <div className="replan-kpi-grid">
            <div className="kpi-card">
              <span className="kpi-label">Total Adjustments</span>
              <strong className="kpi-num mono">{metrics?.schedule_change_count ?? 0}</strong>
              <small>Rescheduled + Unscheduled</small>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Rescheduled</span>
              <strong className="kpi-num mono text-success">{metrics?.moved_interviews ?? 0}</strong>
              <small>Moved to alternate slots</small>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Newly Unscheduled</span>
              <strong className={`kpi-num mono ${(metrics?.newly_unscheduled_interviews ?? 0) > 0 ? 'text-warning' : ''}`}>
                {metrics?.newly_unscheduled_interviews ?? 0}
              </strong>
              <small>Due to capacity limits</small>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Unchanged Stable</span>
              <strong className="kpi-num mono">{metrics?.unchanged_interviews ?? 0}</strong>
              <small>Preserved original slots</small>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Change Rate</span>
              <strong className="kpi-num mono">
                {((metrics?.change_rate || 0) * 100).toFixed(2)}%
              </strong>
              <small>Of original schedule</small>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Runtime</span>
              <strong className="kpi-num mono">
                {replanLatency !== null ? `${replanLatency}ms` : '—'}
              </strong>
              <small>Sub-second replan</small>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="filter-controls-row">
            <div className="filter-group-left">
              <div className="day-button-group">
                {['ALL', 'RESCHEDULED', 'UNSCHEDULED', 'UNCHANGED'].map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`day-btn ${filterType === t ? 'active' : ''}`}
                    onClick={() => { setFilterType(t); setPage(1); }}
                  >
                    {t.toLowerCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group-right">
              <input
                type="search"
                className="search-input"
                placeholder="Search changed assignments…"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              />
            </div>
          </div>

          {/* Change Records List */}
          {filteredChanges.length === 0 ? (
            <div className="table-empty-notice">
              <p>No replanning change records match the selected filter.</p>
            </div>
          ) : (
            <div className="changes-list">
              {paginatedChanges.map((c) => {
                const oldA = c.old_assignment
                const newA = c.new_assignment
                const type = c.change_type || 'UNKNOWN'

                const roomChanged = oldA && newA && oldA.room_id !== newA.room_id
                const panelChanged = oldA && newA && oldA.panel_id !== newA.panel_id
                const timeChanged = oldA && newA && (oldA.start_time !== newA.start_time || oldA.end_time !== newA.end_time)
                const dayChanged = oldA && newA && oldA.day !== newA.day

                return (
                  <div key={c.interview_id} className={`change-card change-${type.toLowerCase()}`}>
                    <div className="change-left">
                      <div className="change-title-row">
                        <strong className="mono">{c.interview_id}</strong>
                        <span className="change-tag">{type.replace('_', ' ')}</span>
                      </div>
                      <p className="change-reason-text">{c.reason || 'Deterministic schedule adjustment.'}</p>
                    </div>

                    <div className="change-right">
                      {/* ORIGINAL SLOT */}
                      <div className="slot-box">
                        <span className="slot-tag">ORIGINAL</span>
                        {oldA ? (
                          <div className="slot-info">
                            <span className={dayChanged ? 'slot-diff-val' : ''}>{oldA.day.replace('_', ' ')}</span>
                            <span className={`mono text-muted ${timeChanged ? 'slot-diff-val' : ''}`}>
                              {oldA.start_time}–{oldA.end_time}
                            </span>
                            <span className={`mono ${roomChanged ? 'slot-diff-val' : ''}`}>
                              Room: {oldA.room_id}
                            </span>
                            <span className={`mono text-muted ${panelChanged ? 'slot-diff-val' : ''}`}>
                              Panel: {oldA.panel_id.replace('PANEL-', '')}
                            </span>
                          </div>
                        ) : (
                          <span className="slot-empty">Unscheduled</span>
                        )}
                      </div>

                      <span className="diff-arrow">→</span>

                      {/* REPLANNED SLOT */}
                      <div className="slot-box">
                        <span className="slot-tag">REPLANNED</span>
                        {newA ? (
                          <div className="slot-info">
                            <span className={dayChanged ? 'slot-diff-val' : ''}>{newA.day.replace('_', ' ')}</span>
                            <span className={`mono text-muted ${timeChanged ? 'slot-diff-val' : ''}`}>
                              {newA.start_time}–{newA.end_time}
                            </span>
                            <span className={`mono ${roomChanged ? 'slot-diff-val' : ''}`}>
                              Room: {newA.room_id}
                            </span>
                            <span className={`mono text-muted ${panelChanged ? 'slot-diff-val' : ''}`}>
                              Panel: {newA.panel_id.replace('PANEL-', '')}
                            </span>
                          </div>
                        ) : (
                          <span className="slot-empty text-warning">Unscheduled (Capacity limit reached)</span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Changes Pagination */}
          {totalPages > 1 && (
            <div className="table-pagination-row">
              <div className="pagination-count">
                Showing <strong>{(page - 1) * pageSize + 1}</strong>–
                <strong>{Math.min(page * pageSize, filteredChanges.length)}</strong> of{' '}
                <strong>{filteredChanges.length}</strong> changes
              </div>

              <div className="page-nav-btns">
                <button
                  type="button"
                  className="btn-page-nav"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </button>
                <span className="page-status">{page} / {totalPages}</span>
                <button
                  type="button"
                  className="btn-page-nav"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
