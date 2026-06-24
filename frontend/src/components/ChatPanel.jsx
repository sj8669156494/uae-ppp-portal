import { useState, useRef, useEffect } from 'react'
import { Send, Trash2, Bot, User } from 'lucide-react'
import { useChat } from '../hooks/useChat'

const SUGGESTIONS = [
  'Show me road projects in Dubai',
  'Which water projects are tendering?',
  'Energy projects above AED 10 billion',
  'Healthcare projects in Abu Dhabi',
  'Projects under execution in Sharjah',
]

export function ChatPanel({ onFiltersChanged }) {
  const { messages, loading, sendMessage, clearChat } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const submit = async (text) => {
    const query = text || input.trim()
    if (!query) return
    setInput('')
    const result = await sendMessage(query)
    if (result?.filters_applied && onFiltersChanged) {
      onFiltersChanged(result.filters_applied)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-800 text-white">
        <div className="flex items-center gap-2">
          <Bot size={18} className="text-blue-300" />
          <span className="font-semibold text-sm">UAE PPP AI Assistant</span>
        </div>
        <button onClick={clearChat} className="text-slate-400 hover:text-white transition-colors" title="Clear chat">
          <Trash2 size={16} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
            <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${m.role === 'user' ? 'bg-blue-600' : 'bg-slate-700'}`}>
              {m.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-blue-300" />}
            </div>
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-blue-600 text-white rounded-tr-none'
                : 'bg-slate-100 text-slate-800 rounded-tl-none'
            }`}>
              {m.content}
              {m.meta?.resultCount !== undefined && (
                <div className="mt-1 text-xs opacity-70">
                  {m.meta.resultCount} project{m.meta.resultCount !== 1 ? 's' : ''} found
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
              <Bot size={14} className="text-blue-300" />
            </div>
            <div className="bg-slate-100 rounded-xl rounded-tl-none px-3 py-2">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {SUGGESTIONS.map(s => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-full px-3 py-1 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={e => { e.preventDefault(); submit() }}
        className="border-t border-slate-100 p-3 flex gap-2"
      >
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask about UAE PPP projects…"
          disabled={loading}
          className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="bg-blue-600 text-white rounded-lg px-3 py-2 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  )
}
