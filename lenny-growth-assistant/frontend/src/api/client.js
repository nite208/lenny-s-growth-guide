const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

function normalizeError(detail, fallback) {
  if (typeof detail === "string" && detail.trim().length > 0) return detail;
  return fallback;
}

async function parseError(res, fallback) {
  try {
    const payload = await res.json();
    return normalizeError(payload?.detail, fallback);
  } catch {
    return fallback;
  }
}

export async function sendMessage({ message, session_id, mode }) {
  const res = await fetch(`${BASE}/api/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id, mode }),
  });
  if (!res.ok) {
    const detail = await parseError(res, "Backend unreachable");
    throw new Error(detail);
  }
  return res.json();
}

export async function listSessions() {
  const res = await fetch(`${BASE}/api/sessions/`);
  if (!res.ok) throw new Error(await parseError(res, "Backend unreachable"));
  return res.json();
}

export async function createSession(title = "New Chat") {
  const res = await fetch(`${BASE}/api/sessions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(await parseError(res, "Backend unreachable"));
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${BASE}/api/health/`);
  if (!res.ok) throw new Error(await parseError(res, "Backend unreachable"));
  return res.json();
}
