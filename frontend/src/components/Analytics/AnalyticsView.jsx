import { useMemo } from 'react'

export default function AnalyticsView({
  metrics,
  assignments = [],
  unscheduledIds = [],
  replanResult,
  generated,
  onGenerate,
  loading,
}) {
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
        <h3>No Analytics Available</h3>
        <p>Run the scheduling engine to compute capacity utilization, hourly concurrency, and partner quotas.</p>
        <button type="button" className="btn-primary" onClick={onGenerate} disabled={loading}>
          Generate Schedule
        </button>
      </div>
    )
  }

  const total = metrics.total_interviews || 859
  const scheduled = metrics.scheduled_interviews || assignments.length
  const unscheduled = metrics.unscheduled_interviews || unscheduledIds.length
  const completionRate = (metrics.completion_rate * 100).toFixed(2)

  const replanMetrics = replanResult?.replanning_metrics

  return (
    <div className="analytics-view-container">
      {/* 1. TOP EFFICIENCY SUMMARY */}
      <div className="analytics-summary-grid">
        <div className="analytics-card">
          <div className="card-top-row">
            <h4>Workload Allocation</h4>
            <span className="text-muted">{completionRate}% Completed</span>
          </div>

          <div className="progress-bar-track">
            <div
              className="progress-bar-fill fill-scheduled"
              style={{ width: `${(scheduled / total) * 100}%` }}
              title={`Scheduled: ${scheduled} (${completionRate}%)`}
            />
            <div
              className="progress-bar-fill fill-unscheduled"
              style={{ width: `${(unscheduled / total) * 100}%` }}
              title={`Unscheduled: ${unscheduled} (${(100 - completionRate).toFixed(2)}%)`}
            />
          </div>

          <div className="allocation-legend-row">
            <div className="legend-entry">
              <span className="bullet-dot bg-scheduled" />
              <span>Scheduled: <strong>{scheduled}</strong> ({completionRate}%)</span>
            </div>
            <div className="legend-entry">
              <span className="bullet-dot bg-unscheduled" />
              <span>Unscheduled: <strong>{unscheduled}</strong> ({(100 - completionRate).toFixed(2)}%)</span>
            </div>
          </div>
        </div>

        <div className="analytics-card">
          <div className="card-top-row">
            <h4>Infrastructure Utilization</h4>
            <span className="text-muted">4 Placement Days</span>
          </div>

          <div className="utilization-metrics-row">
            <div className="util-metric-item">
              <span className="util-label">Room Utilization</span>
              <strong className="util-value mono">{(metrics.room_utilization * 100).toFixed(2)}%</strong>
              <small>Across 20 physical suites</small>
            </div>

            <div className="util-metric-item">
              <span className="util-label">Panel Utilization</span>
              <strong className="util-value mono">{(metrics.panel_utilization * 100).toFixed(2)}%</strong>
              <small>Across 85 interviewer panels</small>
            </div>
          </div>
        </div>
      </div>

      {/* 2. CHARTS GRID */}
      <div className="analytics-charts-grid">
        {/* Interviews by Day */}
        <div className="analytics-card">
          <div className="card-top-row">
            <h4>Interviews by Placement Day</h4>
            <span className="text-muted">Daily Workload</span>
          </div>

          <div className="histogram-chart">
            {dayStats.map((item) => (
              <div key={item.day} className="histogram-bar-group">
                <div className="histogram-bar-track">
                  <div className="histogram-bar-fill" style={{ height: `${item.pct}%` }}>
                    <span className="hist-value mono">{item.count}</span>
                  </div>
                </div>
                <div className="histogram-label-block">
                  <strong>{item.day.replace('_', ' ')}</strong>
                  <span className="mono text-muted">{item.hours}h</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Hourly Concurrency */}
        <div className="analytics-card">
          <div className="card-top-row">
            <h4>Hourly Workload Concurrency</h4>
            <span className="text-muted">09:00–18:00</span>
          </div>

          <div className="concurrency-bar-list">
            {hourlyStats.map((item) => (
              <div key={item.hour} className="concurrency-row">
                <span className="hour-tag mono">{item.hour}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${item.pct}%` }} />
                </div>
                <span className="count-tag mono">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Corporate Workload */}
        <div className="analytics-card">
          <div className="card-top-row">
            <h4>Top Corporate Workload</h4>
            <span className="text-muted">Top 10 Partners</span>
          </div>

          <div className="ranking-bar-list">
            {companyRankings.map((item, idx) => (
              <div key={item.companyId} className="ranking-row">
                <span className="rank-index mono">#{idx + 1}</span>
                <span className="rank-name cell-company">{item.companyId}</span>
                <div className="bar-track">
                  <div className="bar-fill fill-accent" style={{ width: `${item.pct}%` }} />
                </div>
                <span className="rank-count mono">{item.count} slots</span>
              </div>
            ))}
          </div>
        </div>

        {/* Room Workload */}
        <div className="analytics-card">
          <div className="card-top-row">
            <h4>Room Workload Rankings</h4>
            <span className="text-muted">Top 10 Suites</span>
          </div>

          <div className="ranking-bar-list">
            {roomRankings.slice(0, 10).map((item, idx) => (
              <div key={item.roomId} className="ranking-row">
                <span className="rank-index mono">#{idx + 1}</span>
                <span className="rank-name mono">{item.roomId}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${item.pct}%` }} />
                </div>
                <span className="rank-count mono">{item.hours}h</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. REPLANNING IMPACT (if replan was executed) */}
      {replanResult && (
        <div className="analytics-card replan-summary-card">
          <div className="card-top-row">
            <h4>Replanning Operational Impact</h4>
            <span className="text-warning">Simulated Disruption</span>
          </div>

          <div className="replan-impact-grid">
            <div className="replan-impact-item">
              <span className="impact-label">Total Adjustments</span>
              <strong className="impact-number mono">{replanMetrics?.schedule_change_count ?? 0}</strong>
              <small>Rescheduled + Unscheduled</small>
            </div>

            <div className="replan-impact-item">
              <span className="impact-label">Rescheduled</span>
              <strong className="impact-number mono text-success">{replanMetrics?.moved_interviews ?? 0}</strong>
              <small>Preserved in valid slots</small>
            </div>

            <div className="replan-impact-item">
              <span className="impact-label">Newly Unscheduled</span>
              <strong className="impact-number mono text-warning">{replanMetrics?.newly_unscheduled_interviews ?? 0}</strong>
              <small>Capacity limits reached</small>
            </div>

            <div className="replan-impact-item">
              <span className="impact-label">Unchanged Stable</span>
              <strong className="impact-number mono">{replanMetrics?.unchanged_interviews ?? 0}</strong>
              <small>Original slots retained</small>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
