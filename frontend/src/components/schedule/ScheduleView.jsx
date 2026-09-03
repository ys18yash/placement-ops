import { useMemo, useState } from 'react'

function calculateDurationMinutes(start, end) {
  if (!start || !end) return null
  const [sh, sm] = start.split(':').map(Number)
  const [eh, em] = end.split(':').map(Number)
  return (eh * 60 + em) - (sh * 60 + sm)
}

export default function ScheduleView({
  assignments = [],
  generated,
  onCopy,
  onInspect,
  onGenerate,
  loading,
}) {
  const [dayFilter, setDayFilter] = useState('ALL')
  const [companyFilter, setCompanyFilter] = useState('ALL')
  const [roomFilter, setRoomFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [sortField, setSortField] = useState('start_time')
  const [sortAsc, setSortAsc] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  const companies = useMemo(() => {
    return Array.from(new Set(assignments.map((a) => a.company_id))).sort()
  }, [assignments])

  const rooms = useMemo(() => {
    return Array.from(new Set(assignments.map((a) => a.room_id))).sort()
  }, [assignments])

  const dayCounts = useMemo(() => {
    const counts = { DAY_1: 0, DAY_2: 0, DAY_3: 0, DAY_4: 0 }
    for (const a of assignments) {
      if (counts[a.day] !== undefined) counts[a.day]++
    }
    return counts
  }, [assignments])

  const filtered = useMemo(() => {
    return assignments
      .filter((item) => {
        if (dayFilter !== 'ALL' && item.day !== dayFilter) return false
        if (companyFilter !== 'ALL' && item.company_id !== companyFilter) return false
        if (roomFilter !== 'ALL' && item.room_id !== roomFilter) return false
        if (search.trim()) {
          const q = search.trim().toLowerCase()
          return (
            item.interview_id.toLowerCase().includes(q) ||
            item.student_id.toLowerCase().includes(q) ||
            item.company_id.toLowerCase().includes(q) ||
            item.panel_id.toLowerCase().includes(q) ||
            item.room_id.toLowerCase().includes(q)
          )
        }
        return true
      })
      .sort((a, b) => {
        const valA = a[sortField] || ''
        const valB = b[sortField] || ''
        if (valA < valB) return sortAsc ? -1 : 1
        if (valA > valB) return sortAsc ? 1 : -1
        return 0
      })

  }, [assignments, dayFilter, companyFilter, roomFilter, search, sortField, sortAsc])

  const paginated = pageSize >= 1000000
    ? filtered
    : filtered.slice((page - 1) * pageSize, page * pageSize)

  const totalPages = pageSize >= 1000000 ? 1 : Math.max(1, Math.ceil(filtered.length / pageSize))

  function handleSort(field) {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(true)
    }
  }

  function exportCSV() {
    if (filtered.length === 0) return
    const headers = ['interview_id', 'student_id', 'company_id', 'panel_id', 'room_id', 'day', 'start_time', 'end_time']
    const rows = filtered.map((a) => [
      a.interview_id, a.student_id, a.company_id, a.panel_id, a.room_id, a.day, a.start_time, a.end_time
    ])
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', `placementops_schedule_${dayFilter}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (!generated) {
    return (
      <div className="empty-state-card">
        <h3>No Schedule Generated Yet</h3>
        <p>Run the deterministic scheduling engine to allocate candidates, rooms, and interviewer panels.</p>
        <button type="button" className="btn-primary" onClick={onGenerate} disabled={loading}>
          Generate Schedule
        </button>
      </div>
    )
  }

  return (
    <div className="schedule-view-container">
      {/* 1. FILTER CONTROLS */}
      <div className="filter-controls-row">
        <div className="filter-group-left">
          {/* Day Chips */}
          <div className="day-button-group">
            <button
              type="button"
              className={`day-btn ${dayFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => { setDayFilter('ALL'); setPage(1); }}
            >
              All Days ({assignments.length})
            </button>
            {['DAY_1', 'DAY_2', 'DAY_3', 'DAY_4'].map((d) => (
              <button
                key={d}
                type="button"
                className={`day-btn ${dayFilter === d ? 'active' : ''}`}
                onClick={() => { setDayFilter(d); setPage(1); }}
              >
                {d.replace('_', ' ')} ({dayCounts[d] || 0})
              </button>
            ))}
          </div>

          <select
            className="filter-select"
            value={companyFilter}
            onChange={(e) => { setCompanyFilter(e.target.value); setPage(1); }}
            aria-label="Filter by Company"
          >
            <option value="ALL">All Companies ({companies.length})</option>
            {companies.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={roomFilter}
            onChange={(e) => { setRoomFilter(e.target.value); setPage(1); }}
            aria-label="Filter by Room"
          >
            <option value="ALL">All Rooms ({rooms.length})</option>
            {rooms.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>

        <div className="filter-group-right">
          <input
            type="search"
            className="search-input"
            placeholder="Search by ID, Student, Company…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />

          <button
            type="button"
            className="btn-export"
            onClick={exportCSV}
            title="Download CSV"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* 2. TABLE */}
      {filtered.length === 0 ? (
        <div className="table-empty-notice">
          <p>No scheduled interviews match the current filter criteria.</p>
        </div>
      ) : (
        <div className="table-scroll-wrapper">
          <table className="schedule-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('interview_id')} className="th-sort">
                  Interview ID {sortField === 'interview_id' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('student_id')} className="th-sort">
                  Student {sortField === 'student_id' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('company_id')} className="th-sort">
                  Company {sortField === 'company_id' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('panel_id')} className="th-sort">
                  Panel {sortField === 'panel_id' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('room_id')} className="th-sort">
                  Room {sortField === 'room_id' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('day')} className="th-sort">
                  Day {sortField === 'day' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('start_time')} className="th-sort">
                  Time Window {sortField === 'start_time' && (sortAsc ? '↑' : '↓')}
                </th>
                <th>Duration</th>
                <th className="th-action">Inspect</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((a) => {
                const dur = calculateDurationMinutes(a.start_time, a.end_time)
                return (
                  <tr key={a.interview_id}>
                    <td>
                      <span
                        className="mono cell-copy"
                        onClick={() => onCopy(a.interview_id, `Copied ${a.interview_id}`)}
                        title="Click to copy"
                      >
                        {a.interview_id}
                      </span>
                    </td>
                    <td>
                      <span
                        className="mono cell-copy"
                        onClick={() => onCopy(a.student_id, `Copied ${a.student_id}`)}
                        title="Click to copy"
                      >
                        {a.student_id}
                      </span>
                    </td>
                    <td>
                      <span className="cell-company">{a.company_id}</span>
                    </td>
                    <td>
                      <span className="mono text-muted">{a.panel_id.replace('PANEL-', '')}</span>
                    </td>
                    <td>
                      <span className="mono">{a.room_id}</span>
                    </td>
                    <td>
                      <span className="cell-day">{a.day.replace('_', ' ')}</span>
                    </td>
                    <td>
                      <span className="mono">{a.start_time} – {a.end_time}</span>
                    </td>
                    <td>
                      <span className="mono text-muted">{dur ? `${dur}m` : '—'}</span>
                    </td>
                    <td className="td-action">
                      <button
                        type="button"
                        className="btn-inspect-action"
                        onClick={() => onInspect(a)}
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* 3. PAGINATION */}
      <div className="table-pagination-row">
        <div className="pagination-count">
          Showing <strong>{(page - 1) * pageSize + 1}</strong>–
          <strong>{Math.min(page * pageSize, filtered.length)}</strong> of <strong>{filtered.length}</strong> assignments
        </div>

        <div className="pagination-actions">
          <select
            className="filter-select select-page-size"
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            aria-label="Page Size"
          >
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
            <option value={1000000}>Show All</option>
          </select>

          {totalPages > 1 && (
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
          )}
        </div>
      </div>
    </div>
  )
}
