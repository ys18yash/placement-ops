export default function ToastContainer({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null

  return (
    <div className="toast-container" aria-live="polite" aria-atomic="true">
      {toasts.map((t) => (
        <div key={t.id} className={`toast-card toast-${t.type.toLowerCase()}`}>
          <div className="toast-icon">
            {t.type === 'SUCCESS' && '✓'}
            {t.type === 'WARNING' && '⚠️'}
            {t.type === 'ERROR' && '✕'}
            {t.type === 'INFO' && 'ℹ'}
          </div>
          <div className="toast-content">
            <strong className="toast-title">{t.title}</strong>
            <p className="toast-msg">{t.message}</p>
          </div>
          <button
            type="button"
            className="toast-close"
            onClick={() => onDismiss(t.id)}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
