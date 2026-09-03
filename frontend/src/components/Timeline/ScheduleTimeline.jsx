import { useMemo, useState } from 'react'
import AssignmentDrawer from './AssignmentDrawer'

const TIMELINE_START_MINUTES = 540 // 09:00
const TIMELINE_TOTAL_MINUTES = 420 // 09:00 to 16:00 (7 hours)
const TIME_TICKS = [
  '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'
]



function timeToMinutes(timeStr) {
  if (!timeStr) return 0
  const [h, m] = timeStr.split(':').map(Number)
  return h * 60 + m
}

export default function ScheduleTimeline({ assignments = [], generated, onCopy }) {
  const [selectedDay, setSelectedDay] = useState('DAY_1')
  const [resourceMode, setResourceMode] = useState('ROOMS') // 'ROOMS' | 'PANELS'
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAssignment, setSelectedAssignment] = useState(null)

  // Filter assignments for selected day
  const dayAssignments = useMemo(() => {
    return assignments.filter((a) => a.day === selectedDay)
  }, [assignments, selectedDay])

  // Extract resources based on mode
  const resources = useMemo(() => {
    if (resourceMode === 'ROOMS') {
      // 20 physical rooms
      const set = new Set(assignments.map((a) => a.room_id))
      const list = Array.from(set).sort()
      if (list.length === 0) {
        return Array.from({ length: 20 }, (_, i) => `ROOM${String(i + 1).padStart(3, '0')}`)
      }
      return list
    } else {
      // Active panels on this day
      const set = new Set(dayAssignments.map((a) => a.panel_id))
      return Array.from(set).sort()
    }
  }, [assignments, dayAssignments, resourceMode])

  // Group assignments by resource
  const assignmentsByResource = useMemo(() => {
    const map = {}
    for (const r of resources) {
      map[r] = []
    }
    for (const a of dayAssignments) {
      const key = resourceMode === 'ROOMS' ? a.room_id : a.panel_id
      if (map[key]) {
        map[key].push(a)
      } else {
        map[key] = [a]
      }
    }
    // Sort assignments inside each row by start_time
    for (const key of Object.keys(map)) {
      map[key].sort((a, b) => timeToMinutes(a.start_time) - timeToMinutes(b.start_time))
    }
    return map
  }, [dayAssignments, resources, resourceMode])

  if (!generated || assignments.length === 0) {
    return (
      <div className="empty-state-card">
        <div className="empty-state-icon">📊</div>
        <h3>No Timeline Available</h3>
        <p>Generate a valid schedule to visualize time allocation blocks across physical rooms and interview panels.</p>
      </div>
    )
  }

  const q = searchQuery.trim().toLowerCase()

  return (
    <div className="timeline-container">
      {/* Timeline Controls Header */}
      <div className="timeline-toolbar">
        <div className="timeline-toolbar-left">
          {/* Day Chips */}
          <div className="chip-filter-group">
            <span className="filter-group-label">Day:</span>
            {['DAY_1', 'DAY_2', 'DAY_3', 'DAY_4'].map((day) => {
              const count = assignments.filter((a) => a.day === day).length
              return (
                <button
                  key={day}
                  type="button"
                  className={`chip-filter ${selectedDay === day ? 'active' : ''}`}
                  onClick={() => setSelectedDay(day)}
                >
                  {day.replace('_', ' ')} ({count})
                </button>
              )
            })}
          </div>

          {/* Mode Switcher */}
          <div className="mode-toggle-group">
            <span className="filter-group-label">Resource:</span>
            <button
              type="button"
              className={`mode-btn ${resourceMode === 'ROOMS' ? 'active' : ''}`}
              onClick={() => setResourceMode('ROOMS')}
            >
              Rooms ({resourceMode === 'ROOMS' ? resources.length : 20})
            </button>
            <button
              type="button"
              className={`mode-btn ${resourceMode === 'PANELS' ? 'active' : ''}`}
              onClick={() => setResourceMode('PANELS')}
            >
              Panels ({resourceMode === 'PANELS' ? resources.length : 'Day Panels'})
            </button>
          </div>
        </div>

        <div className="timeline-toolbar-right">
          <input
            type="search"
            className="search-control search-control-sm"
            placeholder="Highlight student, company, panel…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Visual Gantt Timeline Grid */}
      <div className="timeline-scroll-wrapper">
        <div className="timeline-grid">
          {/* Time Header Axis */}
          <div className="timeline-header-row">
            <div className="timeline-resource-col-header">
              {resourceMode === 'ROOMS' ? 'Room Suite' : 'Interview Panel'}
            </div>
            <div className="timeline-time-axis">
              {TIME_TICKS.map((tick) => (
                <div key={tick} className="time-tick-col">
                  <span className="time-tick-label">{tick}</span>
                  <span className="time-tick-line" />
                </div>
              ))}
            </div>
          </div>

          {/* Resource Rows */}
          <div className="timeline-body">
            {resources.map((resKey) => {
              const rowAssignments = assignmentsByResource[resKey] || []
              return (
                <div key={resKey} className="timeline-row">
                  <div className="timeline-resource-label">
                    <span className="mono-text bold">{resourceMode === 'PANELS' ? resKey.replace('PANEL-', '') : resKey}</span>
                    <small className="resource-sub-count">{rowAssignments.length} slots</small>
                  </div>

                  <div className="timeline-track">
                    {/* Background grid vertical guidelines */}
                    {TIME_TICKS.map((tick) => (
                      <div key={tick} className="track-grid-line" />
                    ))}

                    {/* Proportional Interview Blocks */}
                    {rowAssignments.map((a) => {
                      const startMin = timeToMinutes(a.start_time)
                      const endMin = timeToMinutes(a.end_time)
                      const durMin = endMin - startMin

                      const leftPct = Math.max(0, Math.min(100, ((startMin - TIMELINE_START_MINUTES) / TIMELINE_TOTAL_MINUTES) * 100))
                      const widthPct = Math.max(1, Math.min(100 - leftPct, (durMin / TIMELINE_TOTAL_MINUTES) * 100))

                      const isMatch = q ? (
                        a.interview_id.toLowerCase().includes(q) ||
                        a.student_id.toLowerCase().includes(q) ||
                        a.company_id.toLowerCase().includes(q) ||
                        a.panel_id.toLowerCase().includes(q) ||
                        a.room_id.toLowerCase().includes(q)
                      ) : false

                      const isDimmed = q && !isMatch

                      return (
                        <div
                          key={a.interview_id}
                          className={`timeline-block ${isMatch ? 'block-matched' : ''} ${isDimmed ? 'block-dimmed' : ''}`}
                          style={{
                            left: `${leftPct}%`,
                            width: `${widthPct}%`,
                          }}
                          onClick={() => setSelectedAssignment(a)}
                          title={`${a.interview_id} · ${a.student_id} (${a.company_id})\n${a.start_time} - ${a.end_time} (${durMin}m)\nRoom: ${a.room_id} | Panel: ${a.panel_id}\nClick to inspect details`}
                        >
                          <div className="block-header-line">
                            <span className="block-id">{a.interview_id}</span>
                            <span className="block-time">{a.start_time}</span>
                          </div>
                          <div className="block-meta-line">
                            <span className="block-company">{a.company_id}</span>
                            <span className="block-student">{a.student_id}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Timeline Footer Legend */}
      <div className="timeline-footer-legend">
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-chip chip-block" />
            <span>Scheduled Slot (45–60 min)</span>
          </div>
          <div className="legend-item">
            <span className="legend-chip chip-highlight" />
            <span>Search Match</span>
          </div>
          <div className="legend-item">
            <span className="legend-chip chip-hover" />
            <span>Click any block to open details inspector</span>
          </div>
        </div>

        <span className="legend-note">
          Placement Window: 09:00 – 16:00 (15-min deterministic time grid)
        </span>


      </div>

      {/* Detail Modal / Drawer */}
      {selectedAssignment && (
        <AssignmentDrawer
          assignment={selectedAssignment}
          onClose={() => setSelectedAssignment(null)}
          onCopy={onCopy}
        />
      )}
    </div>
  )
}
