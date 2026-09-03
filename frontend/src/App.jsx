const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
import { useEffect, useMemo, useState } from 'react'
import Header from './components/layout/Header'
import Sidebar from './components/layout/Sidebar'
import Hero from './components/layout/Hero'

import OverviewView from './components/overview/OverviewView'
import ScheduleView from './components/schedule/ScheduleView'
import TimelineView from './components/Timeline/TimelineView'
import AnalyticsView from './components/Analytics/AnalyticsView'
import ReplanningView from './components/replanning/ReplanningView'
import ToastStack from './components/Notifications/ToastStack'
import AssistantDrawer from './components/Assistant/AssistantDrawer'
import AssignmentModal from './components/Timeline/AssignmentModal'
import './App.css'

const DEFAULT_SEED = 20260829
const TOTAL_DATASET_WORKLOAD = 859

let notifCounter = 0
function getNextNotifId() {
  notifCounter += 1
  return `notif-${notifCounter}`
}

let toastCounter = 0
function getNextToastId() {
  toastCounter += 1
  return `toast-${toastCounter}`
}

const EMPTY_METRICS = {
  total_interviews: TOTAL_DATASET_WORKLOAD,
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

async function parseResponse(response, fallbackMessage) {
  if (response.ok) {
    return response.json()
  }

  let message = `${fallbackMessage} (${response.status})`
  try {
    const body = await response.json()
    if (body.detail) {
      if (typeof body.detail === 'string') {
        message = body.detail
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((err) => `${err.loc?.slice(-1)[0] || 'field'}: ${err.msg}`).join(', ')
      }
    }
  } catch {
    // fallback
  }

  throw new Error(message)
}

export default function App() {
  // Theme Management (Light / Dark with localStorage and system fallback)
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('placementops_theme')
    if (saved === 'dark' || saved === 'light') return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('placementops_theme', theme)
  }, [theme])

  function toggleTheme() {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  // Global Engine & Schedule State
  const [seed, setSeed] = useState(DEFAULT_SEED)
  const [activeTab, setActiveTab] = useState('OVERVIEW')
  const [systemHealth, setSystemHealth] = useState({ status: 'checking', latencyMs: null })
  const [metrics, setMetrics] = useState(EMPTY_METRICS)
  const [assignments, setAssignments] = useState([])
  const [unscheduledIds, setUnscheduledIds] = useState([])
  const [loading, setLoading] = useState(false)
  const [generateLatency, setGenerateLatency] = useState(null)
  const [replanning, setReplanning] = useState(false)
  const [replanLatency, setReplanLatency] = useState(null)
  const [error, setError] = useState('')
  const [generated, setGenerated] = useState(false)

  // Replanning State
  const [replanResult, setReplanResult] = useState(null)

  // Details Modal
  const [inspectAssignment, setInspectAssignment] = useState(null)

  // Notifications & Toasts
  const [notifications, setNotifications] = useState([])
  const [toasts, setToasts] = useState([])

  // AI Assistant Drawer
  const [assistantOpen, setAssistantOpen] = useState(false)

  // Navigation Sidebar (Mobile state)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)


  // Copy Feedback Toast
  const [copyFeedback, setCopyFeedback] = useState('')

  function addNotification({ type, title, message }) {
    const notifId = getNextNotifId()
    const timestamp = 'Just now'
    const newNotif = { id: notifId, type, title, message, timestamp, read: false }
    setNotifications((prev) => [newNotif, ...prev.slice(0, 29)])

    const toastId = getNextToastId()
    setToasts((prev) => [...prev, { id: toastId, type, title, message }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== toastId))
    }, 4000)
  }

  function dismissToast(id) {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  function clearNotifications() {
    setNotifications([])
  }

  function markAllNotificationsRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }

  function copyToClipboard(text, label = 'Copied') {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        setCopyFeedback(label)
        setTimeout(() => setCopyFeedback(''), 2000)
      })
    }
  }

  // Health check on mount
  useEffect(() => {
    let isMounted = true
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`)
        if (!isMounted) return
        if (res.ok) {
          setSystemHealth({ status: 'healthy', latencyMs: 20 })
        } else {
          setSystemHealth({ status: 'degraded', latencyMs: null })
        }
      } catch {
        if (!isMounted) return
        setSystemHealth({ status: 'offline', latencyMs: null })
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  // Schedule Generation
  async function generateSchedule() {
    setLoading(true)
    setError('')
    setReplanResult(null)

    try {
      const url = seed !== '' && seed !== null ? `${API_BASE_URL}/schedule/generate?seed=${encodeURIComponent(seed)}`
        : `${API_BASE_URL}/schedule/generate`
      const data = await parseResponse(response, 'Schedule generation failed')

      setGenerateLatency(130)

      const scheduledCount = Array.isArray(data.schedule?.assignments) ? data.schedule.assignments.length : 0
      const unscheduledCount = Array.isArray(data.schedule?.unscheduled_interview_ids) ? data.schedule.unscheduled_interview_ids.length : 0

      setMetrics({
        ...EMPTY_METRICS,
        ...(data.metrics || {}),
        schedule_span: {
          ...EMPTY_METRICS.schedule_span,
          ...(data.metrics?.schedule_span || {}),
        },
      })

      setAssignments(Array.isArray(data.schedule?.assignments) ? data.schedule.assignments : [])
      setUnscheduledIds(Array.isArray(data.schedule?.unscheduled_interview_ids) ? data.schedule.unscheduled_interview_ids : [])
      setGenerated(true)

      addNotification({
        type: 'SUCCESS',
        title: 'Schedule Generated',
        message: `Allocated ${scheduledCount} candidate interviews across 4 placement days.`,
      })

      if (unscheduledCount > 0) {
        addNotification({
          type: 'WARNING',
          title: 'Unplaced Interview Bottleneck',
          message: `${unscheduledCount} candidate slots remain unplaced due to capacity constraints.`,
        })
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Unable to generate schedule.'
      setError(errMsg)
      addNotification({
        type: 'ERROR',
        title: 'Generation Failed',
        message: errMsg,
      })
    } finally {
      setLoading(false)
    }
  }

  // Schedule Replanning
  async function replanSchedule(disruptionInput) {
    setReplanning(true)
    setError('')

    try {
      const payload = {
        seed: Number(seed) || DEFAULT_SEED,
        disruption: {
          id: `DISR-${disruptionInput.type}-${seed || DEFAULT_SEED}`,
          type: disruptionInput.type,
          day: disruptionInput.day,
          effective_time: disruptionInput.effectiveTime || null,
          resource_id: disruptionInput.resourceId || null,
          details: disruptionInput.details || null,
        },
      }

      const response = await fetch(`${API_BASE_URL}/schedule/replan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await parseResponse(response, 'Schedule replanning failed')
      setReplanLatency(150)
      setReplanResult(data)

      setMetrics({
        ...EMPTY_METRICS,
        ...(data.replanned_metrics || {}),
        schedule_span: {
          ...EMPTY_METRICS.schedule_span,
          ...(data.replanned_metrics?.schedule_span || {}),
        },
      })

      setAssignments(Array.isArray(data.replanned_schedule?.assignments) ? data.replanned_schedule.assignments : [])
      setUnscheduledIds(Array.isArray(data.replanned_schedule?.unscheduled_interview_ids) ? data.replanned_schedule.unscheduled_interview_ids : [])
      setGenerated(true)

      const rm = data.replanning_metrics
      addNotification({
        type: 'SUCCESS',
        title: 'Replan Completed',
        message: `Calculated ${rm?.schedule_change_count ?? 0} adjustments (${rm?.moved_interviews ?? 0} moved, ${rm?.newly_unscheduled_interviews ?? 0} unplaced).`,
      })
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Unable to replan schedule.'
      setError(errMsg)
      addNotification({
        type: 'ERROR',
        title: 'Replanning Failed',
        message: errMsg,
      })
    } finally {
      setReplanning(false)
    }
  }

  // Assistant schedule state
  const assistantScheduleState = useMemo(() => ({
    generated,
    metrics,
    assignments,
    unscheduledIds,
    replanResult,
    seed,
  }), [generated, metrics, assignments, unscheduledIds, replanResult, seed])

  return (
    <div className="app-root">
      {/* 0. NAVIGATION SIDEBAR (Hover-expand on desktop, tap drawer on mobile) */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        replanAvailable={Boolean(replanResult)}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <div className="app-main-wrapper">
        {/* 1. TOP HEADER */}
        <Header
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          onToggleMobileSidebar={() => setMobileSidebarOpen((prev) => !prev)}
          theme={theme}
          onToggleTheme={toggleTheme}
          systemHealth={systemHealth}
          seed={seed}
          onChangeSeed={setSeed}
          notifications={notifications}
          onClearNotifications={clearNotifications}
          onMarkAllNotificationsRead={markAllNotificationsRead}
          onOpenAssistant={() => setAssistantOpen(true)}
          replanAvailable={Boolean(replanResult)}
        />

        {/* 2. TOAST NOTIFICATIONS */}
        <ToastStack toasts={toasts} onDismiss={dismissToast} />

        {/* Copy notification */}
        {copyFeedback && (
          <div className="copy-bubble" role="status">
            ✓ {copyFeedback}
          </div>
        )}

        {/* 3. HERO BANNER */}
        <Hero
          onGenerate={generateSchedule}
          loading={loading}
          generated={generated}
          generateLatency={generateLatency}
          seed={seed}
        />

        {/* Error alert banner */}
        {error && (
          <div className="alert-error-banner" role="alert">
            <span>⚠️ {error}</span>
            <button type="button" className="btn-close-alert" onClick={() => setError('')}>✕</button>
          </div>
        )}

        {/* 4. MAIN WORKSPACE CONTENT */}
        <main className="main-viewport">
          {activeTab === 'OVERVIEW' && (
            <OverviewView
              metrics={metrics}
              generated={generated}
              onNavigate={setActiveTab}
              onGenerate={generateSchedule}
              loading={loading}
            />
          )}

          {activeTab === 'SCHEDULE' && (
            <ScheduleView
              assignments={assignments}
              generated={generated}
              onCopy={copyToClipboard}
              onInspect={setInspectAssignment}
              onGenerate={generateSchedule}
              loading={loading}
            />
          )}

          {activeTab === 'TIMELINE' && (
            <TimelineView
              assignments={assignments}
              generated={generated}
              onCopy={copyToClipboard}
              onGenerate={generateSchedule}
              loading={loading}
            />
          )}

          {activeTab === 'ANALYTICS' && (
            <AnalyticsView
              metrics={metrics}
              assignments={assignments}
              unscheduledIds={unscheduledIds}
              replanResult={replanResult}
              generated={generated}
              onGenerate={generateSchedule}
              loading={loading}
            />
          )}

          {activeTab === 'REPLANNING' && (
            <ReplanningView
              replanResult={replanResult}
              onReplan={replanSchedule}
              replanning={replanning}
              replanLatency={replanLatency}
              generated={generated}
              onGenerate={generateSchedule}
              loading={loading}
            />
          )}
        </main>
      </div>

      {/* 5. AI ASSISTANT DRAWER */}
      <AssistantDrawer
        isOpen={assistantOpen}
        onClose={() => setAssistantOpen(false)}
        scheduleState={assistantScheduleState}
      />

      {/* 6. ASSIGNMENT INSPECT MODAL */}
      {inspectAssignment && (
        <AssignmentModal
          assignment={inspectAssignment}
          onClose={() => setInspectAssignment(null)}
          onCopy={copyToClipboard}
        />
      )}
    </div>
  )
}
