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
      <h1 style={{ marginBottom: '0.5rem', color: '#38bdf8' }}>AutoOS Gateway</h1>
      <p style={{ marginBottom: '2rem', color: '#94a3b8' }}>Unified AI Control for Web & Desktop</p>

      <div className="card">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What would you like me to do? (e.g. 'Check my email' or 'Open Notepad')"
          disabled={isRunning}
          onKeyDown={(e) => e.key === 'Enter' && handleRun()}
        />
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button onClick={handleRun} disabled={isRunning || !input}>
            {isRunning ? 'Running...' : 'Execute Task'}
          </button>
        </div>
      </div>

      {logs.length > 0 && (
        <div className="status-log">
          <div style={{ paddingBottom: '0.5rem', borderBottom: '1px solid #334155', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 'bold' }}>Status: {status}</span>
            <span style={{ color: '#94a3b8' }}>Execution Log</span>
          </div>
          {logs.map((log, i) => (
            <div key={i} className={`status-entry type-${log.type}`}>
              <span style={{ color: '#64748b', fontSize: '0.8rem', marginRight: '0.5rem' }}>[{log.timestamp}]</span>
              {log.message}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default App
