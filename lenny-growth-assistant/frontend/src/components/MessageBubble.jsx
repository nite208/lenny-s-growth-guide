import ReactMarkdown from "react-markdown"

export default function MessageBubble({ message }) {
  const isUser = message.role === "user"
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${isUser ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100"}`}>
        <div className="prose prose-invert prose-sm max-w-none"><ReactMarkdown>{message.content}</ReactMarkdown></div>
        {message.sources?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <p className="text-xs text-gray-400">Sources: {message.sources.join(", ")}</p>
          </div>
        )}
      </div>
    </div>
  )
}
