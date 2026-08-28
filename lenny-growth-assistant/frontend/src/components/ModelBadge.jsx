export default function ModelBadge({ provider }) {
  if (!provider) return null
  const isLocal = provider.toLowerCase().includes("ollama")
  return (
    <span className={`text-xs px-2 py-1 rounded-full ${isLocal ? "bg-green-900 text-green-300" : "bg-blue-900 text-blue-300"}`}>
      {isLocal ? "🖥️" : "☁️"} {provider}
    </span>
  )
}
