import { useMemo, useState } from 'react'
import AssignmentModal from './AssignmentModal'

const START_MIN = 540 // 09:00
const TOTAL_MIN = 420 // 7 hours (09:00 to 16:00)
const TIME_HOURS = [
  '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'
]



const ALL_20_ROOMS = Array.from({ length: 20 }, (_, i) => `ROOM${String(i + 1).padStart(3, '0')}`)

function timeToMin(timeStr) {
  if (!timeStr) return 0
  const [h, m] = timeStr.split(':').map(Number)
  return h * 60 + m
}

export default function TimelineView({
  assignments = [],
  generated,
  onCopy,
  onGenerate,
  loading,
}) {
  const [selectedDay, setSelectedDay] = useState('DAY_1')
  const [resourceMode, setResourceMode] = useState('ROOMS') // 'ROOMS' | 'PANELS'
  const [search, setSearch] = useState('')
  const [selectedAssignment, setSelectedAssignment] = useState(null)

  const dayAssignments = useMemo(() => {
    return assignments.filter((a) => a.day === selectedDay)
  }, [assignments, selectedDay])

  const resources = useMemo(() => {
    if (resourceMode === 'ROOMS') {
      const activeRooms = Array.from(new Set(assignments.map((a) => a.room_id))).sort()
      return activeRooms.length > 0 ? activeRooms : ALL_20_ROOMS
    } else {
      const activePanels = Array.from(new Set(dayAssignments.map((a) => a.panel_id))).sort()
      return activePanels
    }
  }, [assignments, dayAssignments, resourceMode])

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
    for (const k of Object.keys(map)) {
      map[k].sort((a, b) => timeToMin(a.start_time) - timeToMin(b.start_time))
    }
    return map
  }, [dayAssignments, resources, resourceMode])

  if (!generated) {
    return (
      <div className="empty-state-card">
        <h3>No Timeline Generated Yet</h3>
        <p>Run the scheduling engine to visualize real-time allocation blocks across physical rooms and interviewer panels.</p>
        <button type="button" className="btn-primary" onClick={onGenerate} disabled={loading}>
          Generate Schedule
        </button>
      </div>
    )
  }

  const q = search.trim().toLowerCase()

  return (
    <div className="timeline-view-container">
      {/* 1. TOOLBAR */}
      <div className="timeline-toolbar">
        <div className="toolbar-left">
          <div className="day-button-group">
            {['DAY_1', 'DAY_2', 'DAY_3', 'DAY_4'].map((day) => {
              const count = assignments.filter((a) => a.day === day).length
              return (
                <button
                  key={day}
                  type="button"
                  className={`day-btn ${selectedDay === day ? 'active' : ''}`}
                  onClick={() => setSelectedDay(day)}
                >
                  {day.replace('_', ' ')} ({count})
                </button>
              )
            })}
          </div>

          <div className="resource-mode-group">
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

        <div className="toolbar-right">
          <input
            type="search"
            className="search-input"
            placeholder="Highlight Candidate, Panel, Company…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* 2. GANTT TIMELINE GRID */}
      <div className="timeline-grid-wrapper">
        <div className="timeline-grid">
          {/* Time Header */}
          <div className="timeline-header-row">
            <div className="resource-header-cell">
              {resourceMode === 'ROOMS' ? 'Room Suite' : 'Interviewer Panel'}
            </div>
            <div className="time-scale-row">
              {TIME_HOURS.map((hour) => (
                <div key={hour} className="time-hour-cell mono">
                  {hour}
                </div>
              ))}
            </div>
          </div>

          {/* Resource Tracks */}
          <div className="timeline-rows-container">
            {resources.map((resKey) => {
              const rowSlots = assignmentsByResource[resKey] || []
              return (
                <div key={resKey} className="timeline-resource-row">
                  <div className="resource-label-cell">
                    <strong className="mono">{resourceMode === 'PANELS' ? resKey.replace('PANEL-', '') : resKey}</strong>
                    <span className="slot-count">{rowSlots.length} slots</span>
                  </div>

                  <div className="timeline-track">
                    {/* Hour grid lines */}
                    {TIME_HOURS.map((hour, idx) => (
                      <div
                        key={hour}
                        className="track-grid-line"
                        style={{ left: `${(idx / (TIME_HOURS.length - 1)) * 100}%` }}
                      />
                    ))}

                    {/* Interview Blocks */}
                    {rowSlots.map((a) => {
                      const start = timeToMin(a.start_time)
                      const end = timeToMin(a.end_time)
                      const dur = end - start

                      const leftPct = Math.max(0, Math.min(100, ((start - START_MIN) / TOTAL_MIN) * 100))
                      const widthPct = Math.max(2, Math.min(100 - leftPct, (dur / TOTAL_MIN) * 100))

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
                          className={`timeline-block ${isMatch ? 'block-highlight' : ''} ${isDimmed ? 'block-dimmed' : ''}`}
                          style={{
                            left: `${leftPct}%`,
                            width: `${widthPct}%`,
                          }}
                          onClick={() => setSelectedAssignment(a)}
                          title={`${a.interview_id} · ${a.student_id} (${a.company_id})\n${a.start_time} - ${a.end_time} (${dur}m)\nRoom: ${a.room_id} | Panel: ${a.panel_id}\nClick to inspect details`}
                        >
                          <div className="block-header mono">
                            <span className="block-id">{a.interview_id}</span>
                            <span className="block-time">{a.start_time}</span>
                          </div>
                          <div className="block-meta">
                            <span className="block-company">{a.company_id}</span>
                            <span className="block-student mono">{a.student_id}</span>
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

      {/* 3. FOOTER LEGEND */}
      <div className="timeline-footer-row">
        <div className="timeline-legend">
          <div className="legend-item">
            <span className="legend-sample sample-normal" />
            <span>Scheduled Interview (45–60 min)</span>
          </div>
          <div className="legend-item">
            <span className="legend-sample sample-highlight" />
            <span>Search Highlight</span>
          </div>
        </div>

        <span className="time-horizon-text mono">
          Placement Horizon: 09:00 – 16:00 (15-min deterministic time grid)
        </span>


      </div>

      {/* Details Modal */}
      {selectedAssignment && (
        <AssignmentModal
          assignment={selectedAssignment}
          onClose={() => setSelectedAssignment(null)}
          onCopy={onCopy}
        />
      )}
    </div>
  )
}
