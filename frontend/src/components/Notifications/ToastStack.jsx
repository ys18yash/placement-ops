export default function ToastStack({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null

  return (
    <div className="toast-stack" aria-live="polite" aria-atomic="true">
      {toasts.map((t) => (
        <div key={t.id} className={`toast-item toast-${t.type.toLowerCase()}`}>
          <div className="toast-body">
            <strong className="toast-title">{t.title}</strong>
            <p className="toast-message">{t.message}</p>
          </div>
          <button
            type="button"
            className="toast-close"
            onClick={() => onDismiss(t.id)}
            aria-label="Dismiss toast"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}
