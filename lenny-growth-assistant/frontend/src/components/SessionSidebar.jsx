export default function SessionSidebar({ sessions, activeSession, onSelect, onNew }) {
  return (
    <div className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-3 border-b border-gray-800">
        <button onClick={onNew} className="w-full bg-blue-600 hover:bg-blue-500 text-white text-sm py-2 rounded-lg">+ New Chat</button>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {sessions.map(s => (
          <button key={s.id || s.session_id} onClick={() => onSelect(s.id || s.session_id)}
            className={`w-full text-left px-3 py-2 text-sm truncate hover:bg-gray-800 ${activeSession === (s.id || s.session_id) ? "bg-gray-800 text-white" : "text-gray-400"}`}>
            {s.title || "New Chat"}
          </button>
        ))}
      </div>
    </div>
  )
}
