import { useState, useRef, useEffect } from 'react'
import { MessageSquare, Plus, PanelLeftClose, PanelLeftOpen, Send, XCircle } from 'lucide-react'

interface Message {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  type?: 'browser' | 'os' | 'info' | 'plan';
  subCategory?: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  web_search: 'Web Search',
  web_form: 'Web Form',
  media_playback: 'Media Playback',
  gov_portal: 'Gov Portal',
  file_ops: 'File Operations',
  app_launch: 'App Launch',
  hardware: 'Hardware',
  settings: 'Settings',
  process_mgmt: 'Process',
  security: 'Security',
  diagnostics: 'Diagnostics',
  unknown: 'Unknown',
}

function ChatView() {
  const [input, setInput] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [messages, setMessages] = useState<Message[]>([])
  const [history, setHistory] = useState<string[]>([])
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'executing'>('idle')
  const chatEndRef = useRef<HTMLDivElement>(null)
  const ws = useRef<WebSocket | null>(null)
  const executionIdRef = useRef<string | null>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, status])

  const addMessage = (role: Message['role'], content: string, extra: Partial<Message> = {}) => {
    setMessages((prev: Message[]) => [...prev, {
      id: Math.random().toString(36).substring(7),
      role,
      content,
      ...extra
    }])
  }

  const handleNewChat = () => {
    if (messages.length > 0) {
      const firstUserMsg = messages.find((m: Message) => m.role === 'user')?.content || 'New Chat'
      setHistory((prev: string[]) => [firstUserMsg, ...prev.slice(0, 9)])
    }
    setMessages([])
    setInput('')
    setIsRunning(false)
    setStatus('idle')
  }

  const handleStop = async () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'stop' }))
    }
    const execId = executionIdRef.current
    if (execId) {
      try {
        await fetch(`http://localhost:8765/executions/${execId}/stop`, { method: 'POST' })
      } catch (_) {}
    }
    setIsRunning(false)
    setStatus('idle')
    addMessage('system', 'Execution stopped.')
  }

  const handleRun = async () => {
    if (!input.trim() || isRunning) return

    const userTask = input.trim()
    setInput('')
    setIsRunning(true)
    setStatus('analyzing')
    addMessage('user', userTask)

    try {
      const response = await fetch('http://localhost:8765/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userTask })
      })

      const data = await response.json()
      const executionId = data.id
      executionIdRef.current = executionId

      ws.current = new WebSocket(`ws://localhost:8765/ws/execution/${executionId}`)

      ws.current.onopen = () => {
        ws.current?.send(JSON.stringify({ type: 'start', task: userTask }))
      }

      ws.current.onmessage = (event: MessageEvent) => {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'classification': {
            const sub = data.sub_category || 'unknown'
            const cat = data.category || 'os'
            setStatus('executing')
            if (data.plain_english_plan) {
              addMessage('agent', data.plain_english_plan, { 
                type: cat === 'browser' ? 'browser' : 'os',
                subCategory: sub 
              })
            }
            break
          }
          case 'complete':
            addMessage('agent', data.summary)
            setIsRunning(false)
            setStatus('idle')
            ws.current?.close()
            break
          case 'step_error':
            addMessage('system', `Error: ${data.error}`)
            setIsRunning(false)
            setStatus('idle')
            break
          case 'stopped':
            setIsRunning(false)
            setStatus('idle')
            ws.current?.close()
            break
        }
      }
    } catch (error) {
      addMessage('system', `Failed to start: ${error}`)
      setIsRunning(false)
      setStatus('idle')
    }
  }

  return (
    <div className="main-layout">
      <aside className={`sidebar ${!isSidebarOpen ? 'collapsed' : ''}`}>
        <button 
          className="toggle-sidebar-btn" 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
        >
          {isSidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
        </button>

        <button className="new-chat-btn" onClick={handleNewChat}>
          <Plus size={16} />
          New Chat
        </button>
        <div className="history-list">
          {history.map((item: string, i: number) => (
            <div key={i} className="history-item">
              <MessageSquare size={14} style={{ marginRight: '8px' }} />
              {item}
            </div>
          ))}
        </div>
      </aside>

      <main className="app-container">
        <div className="chat-window">
          {messages.length === 0 && (
            <div style={{ marginTop: '20vh', textAlign: 'center', color: '#64748b' }}>
              <h2 style={{ color: '#38bdf8', marginBottom: '0.5rem' }}>AutoOS</h2>
              <p>Your OS companion. Ready for your commands.</p>
            </div>
          )}

          {messages.map((m: Message) => (
            <div key={m.id} className={`message message-${m.role}`}>
              {m.subCategory && (
                <div className={`badge badge-${m.type}`}>
                  {CATEGORY_LABELS[m.subCategory] || m.subCategory}
                </div>
              )}
              {m.content}
            </div>
          ))}

          {status !== 'idle' && (
            <div className="message message-agent">
              <div className="typing-indicator">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="input-area">
          <div className="input-container">
            <input
              type="text"
              value={input}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
              placeholder="How can I help you today?"
              disabled={isRunning}
              onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleRun()}
              autoFocus
            />
            {isRunning ? (
              <button className="btn-stop" onClick={handleStop}><XCircle size={18} /> Stop</button>
            ) : (
              <button className="btn-send" onClick={handleRun} disabled={!input.trim()}>
                <Send size={18} />
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default ChatView
