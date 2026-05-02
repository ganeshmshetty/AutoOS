import { useState, useRef, useEffect } from 'react'
import { MessageSquare, Plus, PanelLeftClose, PanelLeftOpen, Send, XCircle, Sparkles } from 'lucide-react'
import { Message } from './types'

interface ChatViewProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  threadId: string;
  setThreadId: (id: string) => void;
  threadHistory: any[];
  isRunning: boolean;
  status: 'idle' | 'analyzing' | 'executing';
  handleRun: (task: string) => void;
  handleStop: () => void;
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

function ChatView({ 
  messages, 
  setMessages, 
  threadId, 
  setThreadId, 
  threadHistory, 
  isRunning, 
  status, 
  handleRun, 
  handleStop 
}: ChatViewProps) {
  const [input, setInput] = useState('')
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  const onSend = () => {
    if (!input.trim() || isRunning) return
    handleRun(input)
    setInput('')
  }

  const handleNewChat = () => {
    setThreadId("chat-" + Date.now().toString(36))
    setMessages([])
    setInput('')
  }

  return (
    <div className="main-layout">
      <aside className={`sidebar ${!isSidebarOpen ? 'collapsed' : ''}`}>
        <button 
          className="toggle-sidebar-btn" 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        >
          {isSidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
        </button>

        <button className="new-chat-btn" onClick={handleNewChat}>
          <Plus size={16} /> New Chat
        </button>
        <div className="history-list">
          {threadHistory.map((thread: any) => (
            <div key={thread.id} className={`history-item ${threadId === thread.id ? 'active' : ''}`}>
              <MessageSquare size={14} style={{ marginRight: '8px' }} />
              {thread.preview}
            </div>
          ))}
        </div>
      </aside>

      <main className="app-container">
        <div className="chat-window">
          {messages.length === 0 && (
            <div style={{ marginTop: '20vh', textAlign: 'center', color: '#64748b' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
                <div style={{ background: 'rgba(14, 165, 233, 0.1)', padding: '1rem', borderRadius: '50%' }}>
                  <Sparkles size={40} color="#0ea5e9" />
                </div>
              </div>
              <h2 style={{ color: '#38bdf8', marginBottom: '0.5rem' }}>AutoOS Gateway</h2>
              <p>Directly control your computer via natural language.</p>
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
              onChange={(e) => setInput(e.target.value)}
              placeholder="How can I help you today?"
              disabled={isRunning}
              onKeyDown={(e) => e.key === 'Enter' && onSend()}
              autoFocus
            />
            {isRunning ? (
              <button className="btn-stop" onClick={handleStop}><XCircle size={18} /> Stop</button>
            ) : (
              <button className="btn-send" onClick={onSend} disabled={!input.trim()}>
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
