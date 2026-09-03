import { useEffect, useRef, useState } from 'react'

const SUGGESTED_QUERIES = [
  'How many interviews are scheduled?',
  'Which room has the minimum utilization?',
  'Which room has the highest utilization?',
  'Which day has the most interviews?',
]

let assistantMsgCounter = 0
function getNextMsgId(sender) {
  assistantMsgCounter += 1
  return `msg-${sender}-${assistantMsgCounter}`
}

export default function AssistantDrawer({
  isOpen,
  onClose,
  scheduleState,
}) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello. Ask any operational question regarding interview allocations, room or panel utilization, company quotas, or disruption adjustments.',
      timestamp: '09:00',
    },
  ])
  const [inputQuery, setInputQuery] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [lastError, setLastError] = useState(null)
  const chatBottomRef = useRef(null)
  const abortControllerRef = useRef(null)

  useEffect(() => {
    if (isOpen) {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen, streaming])

  function handleStop() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setStreaming(false)
  }

  // Build complete structured context from real schedule state
  function getCompactContext() {
    const {
      generated,
      metrics,
      assignments = [],
      unscheduledIds = [],
      replanResult,
      seed,
    } = scheduleState

    if (!generated) {
      return {
        status: 'SCHEDULE_NOT_GENERATED',
        total_workload: 859,
        seed: seed || 20260829,
      }
    }

    const dayCounts = { DAY_1: 0, DAY_2: 0, DAY_3: 0, DAY_4: 0 }
    const companyCounts = {}
    const roomMins = {}
    // Initialize all 20 physical suites
    for (let i = 1; i <= 20; i++) {
      const rId = `ROOM${String(i).padStart(3, '0')}`
      roomMins[rId] = 0
    }

    for (const a of assignments) {
      if (dayCounts[a.day] !== undefined) dayCounts[a.day]++
      companyCounts[a.company_id] = (companyCounts[a.company_id] || 0) + 1

      const [sh, sm] = a.start_time.split(':').map(Number)
      const [eh, em] = a.end_time.split(':').map(Number)
      const dur = (eh * 60 + em) - (sh * 60 + sm)
      roomMins[a.room_id] = (roomMins[a.room_id] || 0) + dur
    }

    const allRoomsList = Object.entries(roomMins).map(([room, mins]) => ({
      room,
      scheduled_minutes: mins,
      scheduled_hours: (mins / 60).toFixed(1),
    }))

    const sortedCompanies = Object.entries(companyCounts)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => ({ company: k, scheduled_interviews: v }))

    return {
      status: 'SCHEDULE_GENERATED',
      seed: seed || 20260829,
      metrics: {
        total_workload: metrics.total_interviews || 859,
        scheduled_interviews: metrics.scheduled_interviews || assignments.length,
        unscheduled_interviews: metrics.unscheduled_interviews || unscheduledIds.length,
        completion_rate: metrics.completion_rate,
        room_utilization: metrics.room_utilization,
        panel_utilization: metrics.panel_utilization,
        schedule_span: metrics.schedule_span,
      },
      day_breakdown: dayCounts,
      all_rooms_utilization: allRoomsList,
      top_companies: sortedCompanies,
      unscheduled_sample_ids: unscheduledIds.slice(0, 20),
      has_replan: Boolean(replanResult),
      replan_summary: replanResult
        ? {
            disruption: replanResult.disruption,
            metrics: replanResult.replanning_metrics,
            sample_changes: (replanResult.changes || []).slice(0, 10),
          }
        : null,
    }
  }

  async function handleSend(queryText) {
    const textToSend = (queryText || inputQuery).trim()
    if (!textToSend || streaming) return

    setLastError(null)
    const userMsg = {
      id: getNextMsgId('user'),
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    const botMsgId = getNextMsgId('assistant')
    const initialBotMsg = {
      id: botMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    const updatedMessages = [...messages, userMsg]
    setMessages([...updatedMessages, initialBotMsg])
    setInputQuery('')
    setStreaming(true)

    const controller = new AbortController()
    abortControllerRef.current = controller

    try {
      const historyPayload = updatedMessages
        .filter((m) => m.id !== 'welcome')
        .map((m) => ({ role: m.role, content: m.content }))

      const response = await fetch('/api/assistant/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          question: textToSend,
          messages: historyPayload,
          context: getCompactContext(),
        }),
      })

      if (!response.ok) {
        throw new Error(`Assistant query failed (${response.status})`)
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported in response.')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      let receivedAny = false

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || !trimmed.startsWith('data:')) continue

          const jsonStr = trimmed.slice(5).trim()
          if (jsonStr === '[DONE]') break

          try {
            const data = JSON.parse(jsonStr)
            if (data.type === 'delta' && data.text) {
              receivedAny = true
              const delta = data.text
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === botMsgId ? { ...msg, content: msg.content + delta } : msg
                )
              )
            } else if (data.type === 'error') {
              receivedAny = true
              const errMsg = data.error || 'PlacementOps Assistant is temporarily unavailable.'
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === botMsgId
                    ? { ...msg, content: errMsg, isError: true }
                    : msg
                )
              )
            }
          } catch {
            // ignore non-json SSE lines
          }
        }
      }

      if (!receivedAny) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId && !msg.content
              ? {
                  ...msg,
                  content: 'PlacementOps Assistant is temporarily unavailable.',
                  isError: true,
                }
              : msg
          )
        )
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        // User aborted intentionally
        return
      }
      setLastError(textToSend)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMsgId
            ? {
                ...msg,
                content: 'PlacementOps Assistant is temporarily unavailable.',
                isError: true,
              }
            : msg
        )
      )
    } finally {
      setStreaming(false)
      abortControllerRef.current = null
    }
  }

  if (!isOpen) return null

  return (
    <div className="drawer-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <aside className="assistant-drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="assistant-drawer-header">
          <div>
            <h3 className="drawer-title">Ask PlacementOps</h3>
            <span className="drawer-sub">Scheduling assistant</span>
          </div>
          <button type="button" className="btn-close-drawer" onClick={onClose} aria-label="Close assistant">
            ✕
          </button>
        </div>

        {/* Suggested Queries */}
        <div className="assistant-suggestions-bar">
          <div className="suggestions-list">
            {SUGGESTED_QUERIES.map((q) => (
              <button
                key={q}
                type="button"
                className="btn-suggestion"
                onClick={() => handleSend(q)}
                disabled={streaming}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Messages Body */}
        <div className="assistant-messages-container">
          {messages.map((m) => (
            <div key={m.id} className={`chat-message role-${m.role} ${m.isError ? 'msg-error' : ''}`}>
              <div className="msg-bubble">
                <p>{m.content || (streaming && m.role === 'assistant' ? 'Thinking…' : '')}</p>
              </div>
              <span className="msg-time mono">{m.timestamp}</span>
            </div>
          ))}

          {lastError && !streaming && (
            <div className="assistant-error-banner">
              <span>Could not complete inquiry.</span>
              <button
                type="button"
                className="btn-retry-action"
                onClick={() => handleSend(lastError)}
              >
                Retry
              </button>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar */}
        <form
          className="assistant-input-bar"
          onSubmit={(e) => {
            e.preventDefault()
            if (streaming) {
              handleStop()
            } else {
              handleSend()
            }
          }}
        >
          <input
            type="text"
            className="assistant-text-input"
            placeholder="Ask about schedule metrics, room utilization, or replanning…"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={streaming}
          />
          {streaming ? (
            <button
              type="button"
              className="btn-secondary btn-assistant-send"
              onClick={handleStop}
              title="Stop response generation"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="btn-primary btn-assistant-send"
              disabled={!inputQuery.trim()}
            >
              Send
            </button>
          )}
        </form>
      </aside>
    </div>
  )
}

