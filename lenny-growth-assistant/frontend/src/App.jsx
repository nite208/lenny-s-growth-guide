import { useState, useEffect } from "react"
import ChatPane from "./components/ChatPane"
import ArtifactViewer from "./components/ArtifactViewer"
import SessionSidebar from "./components/SessionSidebar"
import { listSessions } from "./api/client"

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [artifact, setArtifact] = useState(null)
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    listSessions().then(setSessions).catch(() => {})
  }, [sessionId])

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans">
      <SessionSidebar sessions={sessions} activeSession={sessionId} onSelect={setSessionId} onNew={() => setSessionId(null)} />
      <div className="flex flex-1 overflow-hidden">
        <ChatPane sessionId={sessionId} setSessionId={setSessionId} setArtifact={setArtifact} />
        {artifact && <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />}
      </div>
    </div>
  )
}
