import ReactMarkdown from "react-markdown"
import { useState } from "react"

export default function ArtifactViewer({ artifact, onClose }) {
  const [view, setView] = useState("preview")
  const isHTML = artifact.type === "html"
  return (
    <div className="w-[45%] border-l border-gray-800 flex flex-col bg-gray-900">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">{artifact.type.toUpperCase()}</span>
          {["preview", "source"].map(v => (
            <button key={v} onClick={() => setView(v)} className={`text-xs px-2 py-0.5 rounded ${view === v ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"}`}>
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => navigator.clipboard.writeText(artifact.content)} className="text-xs text-gray-400 hover:text-white">Copy</button>
          <button onClick={onClose} className="text-xs text-gray-400 hover:text-white">✕</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {view === "source" ? (
          <pre className="text-xs text-gray-300 whitespace-pre-wrap">{artifact.content}</pre>
        ) : isHTML ? (
          <iframe title="artifact" srcDoc={artifact.content} className="w-full h-full bg-white rounded" />
        ) : (
          <div className="prose prose-invert prose-sm max-w-none"><ReactMarkdown>{artifact.content}</ReactMarkdown></div>
        )}
      </div>
    </div>
  )
}
