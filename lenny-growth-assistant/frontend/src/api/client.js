const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

export async function sendMessage({ message, session_id, mode }) {
  const res = await fetch(`${BASE}/api/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id, mode })
  })
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Failed") }
  return res.json()
}

export async function listSessions() {
  const res = await fetch(`${BASE}/api/sessions/`)
  return res.json()
}

export async function createSession(title = "New Chat") {
  const res = await fetch(`${BASE}/api/sessions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title })
  })
  return res.json()
}
