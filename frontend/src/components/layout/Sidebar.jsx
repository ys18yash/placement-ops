import { useState } from 'react'

export default function Sidebar({
  activeTab,
  onSelectTab,
  replanAvailable,
  mobileOpen,
  onCloseMobile,
}) {
  const [isHovered, setIsHovered] = useState(false)

  const navItems = [
    {
      id: 'OVERVIEW',
      label: 'Overview',
      desc: 'System summary & quotas',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="3" y="3" width="7" height="7"></rect>
          <rect x="14" y="3" width="7" height="7"></rect>
          <rect x="14" y="14" width="7" height="7"></rect>
          <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
      ),
    },
    {
      id: 'SCHEDULE',
      label: 'Schedule',
      desc: 'Tabular allocations',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="10" x2="21" y2="10"></line>
          <line x1="8" y1="2" x2="8" y2="6"></line>
          <line x1="16" y1="2" x2="16" y2="6"></line>
          <line x1="8" y1="14" x2="16" y2="14"></line>
          <line x1="8" y1="18" x2="13" y2="18"></line>
        </svg>
      ),
    },
    {
      id: 'TIMELINE',
      label: 'Timeline',
      desc: '09:00–16:00 Gantt lanes',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="4" y1="6" x2="20" y2="6"></line>
          <line x1="4" y1="12" x2="20" y2="12"></line>
          <line x1="4" y1="18" x2="20" y2="18"></line>
          <rect x="6" y="4" width="6" height="4" rx="1"></rect>
          <rect x="10" y="10" width="8" height="4" rx="1"></rect>
          <rect x="5" y="16" width="7" height="4" rx="1"></rect>
        </svg>
      ),
    },
    {
      id: 'ANALYTICS',
      label: 'Analytics',
      desc: 'Resource utilization',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="18" y1="20" x2="18" y2="10"></line>
          <line x1="12" y1="20" x2="12" y2="4"></line>
          <line x1="6" y1="20" x2="6" y2="14"></line>
        </svg>
      ),
    },
    {
      id: 'REPLANNING',
      label: 'Replanning',
      desc: 'Incident simulation',
      badge: replanAvailable ? 'Active' : null,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="23 4 23 10 17 10"></polyline>
          <polyline points="1 20 1 14 7 14"></polyline>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
        </svg>
      ),
    },
  ]

  function handleItemClick(id) {
    onSelectTab(id)
    if (onCloseMobile) {
      onCloseMobile()
    }
  }

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-mobile-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={`app-sidebar ${isHovered ? 'sidebar-expanded' : ''} ${mobileOpen ? 'sidebar-mobile-open' : ''}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        aria-label="Application sidebar"
      >
        {/* Sidebar Header Brand */}
        <div className="sidebar-brand-row" onClick={() => handleItemClick('OVERVIEW')}>
          <div className="sidebar-brand-icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
              <line x1="8" y1="14" x2="8" y2="14.01"></line>
              <line x1="12" y1="14" x2="12" y2="14.01"></line>
              <line x1="16" y1="14" x2="16" y2="14.01"></line>
            </svg>
          </div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-name">PlacementOps</span>
            <span className="sidebar-brand-sub">Operations Engine</span>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="sidebar-nav" aria-label="Sidebar navigation">
          {navItems.map((item) => {
            const isActive = activeTab === item.id
            return (
              <button
                key={item.id}
                type="button"
                className={`sidebar-nav-item ${isActive ? 'sidebar-nav-active' : ''}`}
                onClick={() => handleItemClick(item.id)}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
                title={item.label}
              >
                <div className="sidebar-item-icon">
                  {item.icon}
                  {item.badge && <span className="sidebar-item-dot-badge" />}
                </div>

                <div className="sidebar-item-label-group">
                  <span className="sidebar-item-label">{item.label}</span>
                  {item.desc && <span className="sidebar-item-desc">{item.desc}</span>}
                </div>

                {item.badge && (
                  <span className="sidebar-item-badge">{item.badge}</span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Sidebar Footer Info (visible when expanded) */}
        <div className="sidebar-footer">
          <span className="sidebar-version mono">v2.5.0</span>
          <span className="sidebar-status-tag">Deterministic Engine</span>
        </div>
      </aside>
    </>
  )
}
