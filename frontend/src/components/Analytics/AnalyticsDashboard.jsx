import { useMemo } from 'react'

export default function AnalyticsDashboard({
  metrics,
  assignments = [],
  unscheduledIds = [],
  replanResult,
  generated,
}) {
  // 1. Day breakdown
  const dayStats = useMemo(() => {
    const days = { DAY_1: 0, DAY_2: 0, DAY_3: 0, DAY_4: 0 }
    const dayMins = { DAY_1: 0, DAY_2: 0, DAY_3: 0, DAY_4: 0 }

    for (const a of assignments) {
      if (days[a.day] !== undefined) {
        days[a.day]++
        const [sh, sm] = a.start_time.split(':').map(Number)
        const [eh, em] = a.end_time.split(':').map(Number)
        dayMins[a.day] += (eh * 60 + em) - (sh * 60 + sm)
      }
    }
    const maxCount = Math.max(...Object.values(days), 1)
    return Object.entries(days).map(([day, count]) => ({
      day,
      count,
      minutes: dayMins[day] || 0,
      hours: ((dayMins[day] || 0) / 60).toFixed(1),
      pct: (count / maxCount) * 100,
    }))
  }, [assignments])

  // 2. Hourly Time-Window Concurrency
  const hourlyStats = useMemo(() => {
    const hours = {
      '09:00': 0, '10:00': 0, '11:00': 0, '12:00': 0,
      '13:00': 0, '14:00': 0, '15:00': 0, '16:00': 0, '17:00': 0,
    }

    for (const a of assignments) {
      const [sh] = a.start_time.split(':').map(Number)
      const hourKey = `${String(sh).padStart(2, '0')}:00`
      if (hours[hourKey] !== undefined) {
        hours[hourKey]++
      }
    }

    const maxHour = Math.max(...Object.values(hours), 1)
    return Object.entries(hours).map(([hour, count]) => ({
      hour,
      count,
      pct: (count / maxHour) * 100,
    }))
  }, [assignments])

  // 3. Room Utilization Ranking (top & all rooms)
  const roomRankings = useMemo(() => {
    const roomMins = {}
    for (const a of assignments) {
      const [sh, sm] = a.start_time.split(':').map(Number)
      const [eh, em] = a.end_time.split(':').map(Number)
      const dur = (eh * 60 + em) - (sh * 60 + sm)
      roomMins[a.room_id] = (roomMins[a.room_id] || 0) + dur
    }

    const sorted = Object.entries(roomMins).sort((a, b) => b[1] - a[1])
    const maxMins = sorted[0]?.[1] || 1

    return sorted.map(([roomId, mins]) => ({
      roomId,
      minutes: mins,
      hours: (mins / 60).toFixed(1),
      pct: (mins / maxMins) * 100,
    }))
  }, [assignments])

  // 4. Company Workload Ranking
  const companyRankings = useMemo(() => {
    const compCounts = {}
    for (const a of assignments) {
      compCounts[a.company_id] = (compCounts[a.company_id] || 0) + 1
    }

    const sorted = Object.entries(compCounts).sort((a, b) => b[1] - a[1])
    const maxCount = sorted[0]?.[1] || 1

    return sorted.slice(0, 10).map(([companyId, count]) => ({
      companyId,
      count,
      pct: (count / maxCount) * 100,
    }))
  }, [assignments])

  if (!generated) {
    return (
      <div className="empty-state-card">
        <div className="empty-state-icon">📈</div>
        <h3>No Analytics Generated Yet</h3>
        <p>Generate a placement schedule to view interactive operational distributions, hourly concurrency, room ranking, and partner analytics.</p>
      </div>
    )
  }

  const total = metrics.total_interviews || 859
  const scheduled = metrics.scheduled_interviews || assignments.length
  const unscheduled = metrics.unscheduled_interviews || unscheduledIds.length
  const completionRate = (metrics.completion_rate * 100).toFixed(2)

  const replanMetrics = replanResult?.replanning_metrics

  return (
    <div className="analytics-suite">
      {/* 1. TOP SUMMARY CARDS */}
      <div className="analytics-overview-row">
        <div className="analytics-card card-half">
          <div className="analytics-card-header">
            <h4>Workload Allocation Distribution</h4>
            <span className="kpi-tag tag-success">{completionRate}% Completed</span>
          </div>

          <div className="allocation-progress-wrapper">
            <div className="allocation-segmented-bar">
              <div
                className="segment-fill fill-scheduled"
                style={{ width: `${(scheduled / total) * 100}%` }}
                title={`Scheduled: ${scheduled} (${completionRate}%)`}
              />
              <div
                className="segment-fill fill-unscheduled"
                style={{ width: `${(unscheduled / total) * 100}%` }}
                title={`Unscheduled: ${unscheduled} (${(100 - completionRate).toFixed(2)}%)`}
              />
            </div>

            <div className="allocation-legend-row">
              <div className="legend-entry">
                <span className="dot-indicator dot-scheduled" />
                <span className="legend-label">Scheduled:</span>
                <strong>{scheduled}</strong>
                <small className="legend-percent">({completionRate}%)</small>
              </div>

              <div className="legend-entry">
                <span className="dot-indicator dot-unscheduled" />
                <span className="legend-label">Unscheduled:</span>
                <strong>{unscheduled}</strong>
                <small className="legend-percent">({(100 - completionRate).toFixed(2)}%)</small>
              </div>
            </div>
          </div>
        </div>

        {/* Schedule Span & Hours */}
        <div className="analytics-card card-half">
          <div className="analytics-card-header">
            <h4>Physical & Panel Infrastructure Efficiency</h4>
            <span className="kpi-tag">Operational</span>
          </div>

          <div className="efficiency-metrics-grid">
            <div className="efficiency-metric">
              <span className="eff-label">Room Capacity Utilization</span>
              <strong className="eff-val">{(metrics.room_utilization * 100).toFixed(2)}%</strong>
              <small>Across 20 physical interview suites</small>
            </div>

            <div className="efficiency-metric">
              <span className="eff-label">Panel Capacity Utilization</span>
              <strong className="eff-val">{(metrics.panel_utilization * 100).toFixed(2)}%</strong>
              <small>Across 85 corporate partner panels</small>
            </div>
          </div>
        </div>
      </div>

      {/* 2. CHARTS GRID */}
      <div className="analytics-charts-grid">
        {/* CHART A: Day-by-Day Workload Histogram */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <h4>Workload Distribution by Placement Day</h4>
            <span className="kpi-tag">4 Days</span>
          </div>

          <div className="histogram-container">
            {dayStats.map((item) => (
              <div key={item.day} className="histogram-col">
                <div className="histogram-bar-track">
                  <div className="histogram-bar-fill" style={{ height: `${item.pct}%` }}>
                    <span className="bar-val-bubble">{item.count}</span>
                  </div>
                </div>
                <div className="histogram-label-box">
                  <strong>{item.day.replace('_', ' ')}</strong>
                  <span>{item.hours}h ({item.minutes}m)</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CHART B: Hourly Concurrency Distribution */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <h4>Hourly Workload Concurrency (09:00–18:00)</h4>
            <span className="kpi-tag">Time Grid</span>
          </div>

          <div className="concurrency-bars-container">
            {hourlyStats.map((item) => (
              <div key={item.hour} className="concurrency-row">
                <span className="concurrency-hour">{item.hour}</span>
                <div className="concurrency-track">
                  <div className="concurrency-fill" style={{ width: `${item.pct}%` }} />
                </div>
                <span className="concurrency-count">{item.count} slots</span>
              </div>
            ))}
          </div>
        </div>

        {/* CHART C: Top Corporate Partners by Interview Volume */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <h4>Top Corporate Partners (Interview Slots)</h4>
            <span className="kpi-tag">Top 10</span>
          </div>

          <div className="ranking-list">
            {companyRankings.map((item, idx) => (
              <div key={item.companyId} className="ranking-row">
                <span className="ranking-index">#{idx + 1}</span>
                <span className="ranking-name company-tag">{item.companyId}</span>
                <div className="ranking-track">
                  <div className="ranking-fill fill-blue" style={{ width: `${item.pct}%` }} />
                </div>
                <span className="ranking-val">{item.count} interviews</span>
              </div>
            ))}
          </div>
        </div>

        {/* CHART D: Room Utilization Ranking */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <h4>Room Workload Allocation (Top 10)</h4>
            <span className="kpi-tag">20 Suites</span>
          </div>

          <div className="ranking-list">
            {roomRankings.slice(0, 10).map((item, idx) => (
              <div key={item.roomId} className="ranking-row">
                <span className="ranking-index">#{idx + 1}</span>
                <span className="ranking-name room-tag">{item.roomId}</span>
                <div className="ranking-track">
                  <div className="ranking-fill fill-slate" style={{ width: `${item.pct}%` }} />
                </div>
                <span className="ranking-val">{item.minutes}m ({item.hours}h)</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. REPLANNING IMPACT ANALYTICS (if replan was executed) */}
      {replanResult && (
        <div className="analytics-card replan-analytics-card">
          <div className="analytics-card-header">
            <h4>Replanning Operational Impact Analysis</h4>
            <span className="kpi-tag tag-warning">Active Simulation</span>
          </div>

          <div className="replan-analytics-grid">
            <div className="replan-stat-block">
              <span className="replan-stat-label">Total Schedule Changes</span>
              <strong className="replan-stat-value">{replanMetrics?.schedule_change_count ?? 0}</strong>
              <small>Interviews moved or unscheduled</small>
            </div>

            <div className="replan-stat-block">
              <span className="replan-stat-label">Rescheduled to Alternate Slots</span>
              <strong className="replan-stat-value val-rescheduled">{replanMetrics?.moved_interviews ?? 0}</strong>
              <small>Preserved candidate placement</small>
            </div>

            <div className="replan-stat-block">
              <span className="replan-stat-label">Newly Unscheduled Slots</span>
              <strong className="replan-stat-value val-unscheduled">{replanMetrics?.newly_unscheduled_interviews ?? 0}</strong>
              <small>Due to resource exhaustion</small>
            </div>

            <div className="replan-stat-block">
              <span className="replan-stat-label">Unchanged Stable Assignments</span>
              <strong className="replan-stat-value">{replanMetrics?.unchanged_interviews ?? 0}</strong>
              <small>Retained original room/panel</small>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
