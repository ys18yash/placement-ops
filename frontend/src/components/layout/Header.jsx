import { useEffect, useRef, useState } from 'react'

export default function Header({
  activeTab,
  onSelectTab,
  onToggleMobileSidebar,
  theme,
  onToggleTheme,
  systemHealth,
  seed,
  onChangeSeed,
  notifications,
  onClearNotifications,
  onMarkAllNotificationsRead,
  onOpenAssistant,
  replanAvailable,
}) {
  const tabNames = {
    OVERVIEW: 'Overview',
    SCHEDULE: 'Schedule Matrix',
    TIMELINE: '09:00–16:00 Timeline',
    ANALYTICS: 'Analytics & Quotas',
    REPLANNING: 'Incident Replanning',
  }

  const activeLabel = tabNames[activeTab] || 'Overview'

  return (
    <header className="app-header">
      <div className="header-left">
        {/* Mobile/Quick Sidebar Toggle */}
        <button
          type="button"
          className="btn-sidebar-toggle"
          onClick={onToggleMobileSidebar}
          aria-label="Toggle navigation sidebar"
          title="Toggle Navigation"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        {/* Brand & Breadcrumb */}
        <div className="header-brand" onClick={() => onSelectTab('OVERVIEW')}>
          <span className="brand-name">PlacementOps</span>
          <span className="brand-divider">/</span>
          <span className="brand-sub">{activeLabel}</span>
          {replanAvailable && activeTab === 'REPLANNING' && (
            <span className="nav-tab-badge">Active</span>
          )}
        </div>

      </div>

      <div className="header-right">
        {/* Ask PlacementOps Assistant */}
        <button
          type="button"
          className="btn-assistant-header"
          onClick={onOpenAssistant}
          title="Open Scheduling Assistant"
        >
          <span>Ask PlacementOps</span>
        </button>

        {/* Notification Bell */}
        <NotificationCenterDropdown
          notifications={notifications}
          onClear={onClearNotifications}
          onMarkAllRead={onMarkAllNotificationsRead}
        />

        {/* Theme Toggle */}
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          )}
        </button>

        {/* Engine Status Indicator */}
        <div className="engine-status-pill" title={`Engine latency: ${systemHealth.latencyMs ? `${systemHealth.latencyMs}ms` : 'checking'}`}>
          <span
            className={`status-dot ${
              systemHealth.status === 'healthy'
                ? 'dot-healthy'
                : systemHealth.status === 'checking'
                ? 'dot-checking'
                : 'dot-offline'
            }`}
          />
          <span>{systemHealth.status === 'healthy' ? 'Live' : systemHealth.status === 'checking' ? 'Checking' : 'Offline'}</span>
        </div>

        {/* Seed Input */}
        <div className="header-seed-box">
          <span className="seed-tag">Seed</span>
          <input
            type="number"
            className="seed-input"
            value={seed}
            onChange={(e) => onChangeSeed(Number(e.target.value) || 0)}
            title="Deterministic Random Seed"
            aria-label="Deterministic Random Seed"
          />
        </div>
      </div>
    </header>
  )
}

function NotificationCenterDropdown({ notifications = [], onClear, onMarkAllRead }) {
  const [open, setOpen] = useState(false)
  const popoverRef = useRef(null)

  const unreadCount = notifications.filter((n) => !n.read).length

  useEffect(() => {
    function handleClickOutside(e) {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  function handleToggle() {
    setOpen((prev) => {
      const next = !prev
      if (next && onMarkAllRead) {
        onMarkAllRead()
      }
      return next
    })
  }

  return (
    <div className="notif-dropdown-wrapper" ref={popoverRef}>
      <button
        type="button"
        className="btn-header-icon"
        onClick={handleToggle}
        title="Notifications & Activity"
        aria-label="Notifications"
        aria-expanded={open}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        {unreadCount > 0 && <span className="notif-counter-badge">{unreadCount}</span>}
      </button>

      {open && (
        <div className="notif-popover" role="dialog" aria-label="Notifications Panel">
          <div className="notif-popover-header">
            <span className="notif-popover-title">Activity & Notifications</span>
            {notifications.length > 0 && (
              <button type="button" className="btn-link-subtle" onClick={onClear}>
                Clear
              </button>
            )}
          </div>
          <div className="notif-popover-body">
            {notifications.length === 0 ? (
              <div className="notif-empty">No activity events recorded yet.</div>
            ) : (
              notifications.map((notif) => (
                <div key={notif.id} className="notif-entry">
                  <div className="notif-entry-meta">
                    <span className="text-muted">{notif.type}</span>
                    <span className="text-muted">{notif.timestamp}</span>
                  </div>
                  <strong className="notif-entry-title">{notif.title}</strong>
                  <p className="notif-entry-msg">{notif.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
