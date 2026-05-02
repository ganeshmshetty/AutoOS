import { useState, useEffect, useRef } from 'react'
import './App.css'

interface LogEntry {
  type: 'browser' | 'os' | 'info' | 'error';
  message: string;
  timestamp: string;
}

function App() {
  const [input, setInput] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [status, setStatus] = useState('Idle')
  const ws = useRef<WebSocket | null>(null)

  const addLog = (message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prev => [{
      type,
      message,
      timestamp: new Date().toLocaleTimeString()
    }, ...prev])
  }

  const handleRun = async () => {
    if (!input.trim()) return
    
    setIsRunning(true)
    setLogs([])
    setStatus('Analyzing...')
    addLog(`Starting task: ${input}`)

    try {
      const response = await fetch('http://localhost:8765/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: input })
      })
      
      const data = await response.json()
      const executionId = data.id

      // Connect to WebSocket for real-time updates
      ws.current = new WebSocket(`ws://localhost:8765/ws/execution/${executionId}`)
      
      ws.current.onopen = () => {
        ws.current?.send(JSON.stringify({ type: 'start', task: input }))
      }

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'step_start':
            setStatus(`Executing: ${data.description}`)
            addLog(data.description, 'info')
            break
          case 'step_done':
            addLog(`Completed: ${data.description}`, 'info')
            break
          case 'step_error':
            addLog(`Error: ${data.error}`, 'error')
            break
          case 'complete':
            setStatus('Completed')
            setIsRunning(false)
            addLog(`Task Finished: ${data.summary}`, 'info')
            ws.current?.close()
            break
          case 'classification':
            addLog(`Routed to: ${data.category.toUpperCase()}`, data.category === 'browser' ? 'browser' : 'os')
            break
        }
      }

      ws.current.onerror = () => {
        addLog('WebSocket Connection Error', 'error')
        setIsRunning(false)
      }

    } catch (error) {
      addLog(`Failed to start execution: ${error}`, 'error')
      setIsRunning(false)
    }
  }

  return (
    <div className="container">
      <header style={{ marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3.5rem', fontWeight: 800, marginBottom: '0.5rem', background: 'linear-gradient(to right, #38bdf8, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AutoOS
        </h1>
        <p style={{ fontSize: '1.2rem', color: '#94a3b8', letterSpacing: '0.05em' }}>
          INTELLIGENT DESKTOP COMPANION
        </p>
      </header>

      <div className="card">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="How can I help you today?"
          disabled={isRunning}
          onKeyDown={(e) => e.key === 'Enter' && handleRun()}
        />
        <div className="button-group">
          <button onClick={handleRun} disabled={isRunning || !input}>
            {isRunning ? 'Running...' : 'Execute Task'}
          </button>
          <button className="secondary" disabled={isRunning}>
            🎤 Voice Control
          </button>
        </div>
      </div>

      {logs.length > 0 && (
        <div className="status-log">
          <div style={{ paddingBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 700, fontSize: '1.2rem', color: '#38bdf8' }}>
              {isRunning ? '● ' : ''}Status: {status}
            </span>
            <span style={{ color: '#64748b', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              Activity Feed
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {logs.map((log, i) => (
              <div key={i} className={`status-entry type-${log.type}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.8rem', opacity: 0.8, textTransform: 'uppercase' }}>
                    {log.type}
                  </span>
                  <span style={{ color: '#64748b', fontSize: '0.8rem' }}>
                    {log.timestamp}
                  </span>
                </div>
                {log.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
