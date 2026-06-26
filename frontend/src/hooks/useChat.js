import { useState, useCallback } from 'react'
import axios from 'axios'

export function useChat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Welcome to the UAE PPP Intelligence Portal. Ask me about infrastructure projects, sectors, contractors, or procurement status.',
    },
  ])
  const [sessionId, setSessionId] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastFilters, setLastFilters] = useState({})

  const sendMessage = useCallback(async (text) => {
    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    try {
      const apiBase = (typeof __API_URL__ !== 'undefined' && __API_URL__) ? `${__API_URL__}/api` : '/api'
      const { data } = await axios.post(`${apiBase}/chat`, {
        message: text,
        session_id: sessionId,
      })
      setSessionId(data.session_id)
      setLastFilters(data.filters_applied || {})
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.reply, meta: { resultCount: data.result_count, filters: data.filters_applied } },
      ])
      return data
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ])
      return null
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  const clearChat = useCallback(() => {
    setMessages([{
      role: 'assistant',
      content: 'Welcome to the UAE PPP Intelligence Portal. Ask me about infrastructure projects, sectors, contractors, or procurement status.',
    }])
    setSessionId('')
    setLastFilters({})
  }, [])

  return { messages, loading, lastFilters, sendMessage, clearChat }
}
