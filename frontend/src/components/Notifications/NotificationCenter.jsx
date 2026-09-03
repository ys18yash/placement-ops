import { useEffect, useRef, useState } from 'react'

export default function NotificationCenter({
  notifications = [],
  onClear,
  onMarkAllRead,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  const unreadCount = notifications.filter((n) => !n.read).length

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  function handleToggle() {
    if (!isOpen && unreadCount > 0) {
      onMarkAllRead?.()
    }
    setIsOpen(!isOpen)
  }

  return (
    <div className="notif-center-wrapper" ref={dropdownRef}>
      <button
        type="button"
        className={`btn-notif-bell ${unreadCount > 0 ? 'has-unread' : ''}`}
        onClick={handleToggle}
        title="Operational Notifications"
        aria-label={`Notifications (${unreadCount} unread)`}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
      </button>

      {isOpen && (
        <div className="notif-dropdown-panel" role="region" aria-label="Notifications panel">
          <div className="notif-dropdown-header">
            <div className="notif-header-title-row">
              <h4>Operational Activity</h4>
              <span className="notif-count-pill">{notifications.length} events</span>
            </div>
            {notifications.length > 0 && (
              <button
                type="button"
                className="btn-text-action"
                onClick={onClear}
              >
                Clear all
              </button>
            )}
          </div>

          <div className="notif-list">
            {notifications.length === 0 ? (
              <div className="notif-empty-state">
                <span className="notif-empty-icon">🔔</span>
                <p>No recent operational events logged.</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className={`notif-item notif-${n.type.toLowerCase()}`}>
                  <div className="notif-item-header">
                    <span className={`notif-type-tag tag-${n.type.toLowerCase()}`}>
                      {n.type}
                    </span>
                    <span className="notif-timestamp">{n.timestamp}</span>
                  </div>
                  <strong className="notif-title">{n.title}</strong>
                  <p className="notif-desc">{n.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
