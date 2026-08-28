import { useState, useEffect } from "react"
import ChatPane from "./components/ChatPane"
import ArtifactViewer from "./components/ArtifactViewer"
import SessionSidebar from "./components/SessionSidebar"
import { listSessions, getHealth } from "./api/client"

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [artifact, setArtifact] = useState(null)
  const [sessions, setSessions] = useState([])
  const [health, setHealth] = useState({
    provider: "",
    llm_connected: false,
    chroma_docs: 0,
    chroma_ready: false,
    db_connected: false,
  })

  useEffect(() => {
    listSessions().then(setSessions).catch(() => {})
  }, [sessionId])

  useEffect(() => {
    let active = true
    getHealth()
      .then((data) => {
        if (active) setHealth(data)
      })
      .catch(() => {
        if (active) {
          setHealth({
            provider: "",
            llm_connected: false,
            chroma_docs: 0,
            chroma_ready: false,
            db_connected: false,
          })
        }
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans">
      <SessionSidebar sessions={sessions} activeSession={sessionId} onSelect={setSessionId} onNew={() => setSessionId(null)} />
      <div className="flex flex-1 overflow-hidden">
        <ChatPane
          sessionId={sessionId}
          setSessionId={setSessionId}
          setArtifact={setArtifact}
          health={health}
        />
        {artifact && <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />}
      </div>
    </div>
  )
}
