import { useState, useRef } from 'react'
import './App.css'

interface LogEntry {
  type: 'browser' | 'os' | 'info' | 'error' | 'plan';
  message: string;
  timestamp: string;
}

const CATEGORY_LABELS: Record<string, { label: string; css: string }> = {
  web_search:    { label: 'Web Search',       css: 'badge-browser' },
  web_form:      { label: 'Web Form',          css: 'badge-browser' },
  media_playback:{ label: 'Media Playback',   css: 'badge-browser' },
  gov_portal:    { label: 'Gov Portal',        css: 'badge-browser' },
  file_ops:      { label: 'File Operations',  css: 'badge-os' },
  app_launch:    { label: 'App Launch',        css: 'badge-os' },
  hardware:      { label: 'Hardware',          css: 'badge-os' },
  settings:      { label: 'Settings',          css: 'badge-os' },
  process_mgmt:  { label: 'Process',           css: 'badge-os' },
  security:      { label: 'Security',          css: 'badge-os' },
  diagnostics:   { label: 'Diagnostics',       css: 'badge-os' },
  unknown:       { label: 'Unknown',           css: 'badge-warn' },
}

function App() {
  const [input, setInput] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [status, setStatus] = useState('Idle')
  const [classification, setClassification] = useState<{
    sub_category: string;
    plain_english_plan: string;
    needs_hitl: boolean;
    category: string;
  } | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const executionIdRef = useRef<string | null>(null)

  const addLog = (message: string, type: LogEntry['type'] = 'info') => {
    setLogs(prev => [{
      type,
      message,
      timestamp: new Date().toLocaleTimeString()
    }, ...prev])
  }

  const handleStop = async () => {
    // 1. Send stop via WebSocket (fastest path)
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'stop' }))
    }
    // 2. Also call REST endpoint as a fallback
    const execId = executionIdRef.current
    if (execId) {
      try {
        await fetch(`http://localhost:8765/executions/${execId}/stop`, { method: 'POST' })
      } catch (_) { /* ignore */ }
    }
    setIsRunning(false)
    setStatus('Stopped')
    addLog('Task stopped by user.', 'error')
  }

  const handleRun = async () => {
    if (!input.trim()) return

    setIsRunning(true)
    setLogs([])
    setClassification(null)
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
      executionIdRef.current = executionId

      ws.current = new WebSocket(`ws://localhost:8765/ws/execution/${executionId}`)

      ws.current.onopen = () => {
        ws.current?.send(JSON.stringify({ type: 'start', task: input }))
      }

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'classification': {
            const sub = data.sub_category || data.category || 'unknown'
            const cat = data.category || 'os'
            setClassification({
              sub_category: sub,
              plain_english_plan: data.plain_english_plan || '',
              needs_hitl: data.needs_hitl ?? false,
              category: cat,
            })
            const meta = CATEGORY_LABELS[sub] || CATEGORY_LABELS['unknown']
            addLog(`Routed to: ${meta.label}`, cat === 'browser' ? 'browser' : 'os')
            if (data.plain_english_plan) {
              addLog(`Plan: ${data.plain_english_plan}`, 'plan')
            }
            break
          }
          case 'step_start':
            setStatus('Executing...')
            addLog(data.description, 'info')
            break
          case 'step_done':
            addLog(data.description, 'info')
            break
          case 'step_error':
            addLog(`Error: ${data.error}`, 'error')
            setIsRunning(false)
            setStatus('Error')
            break
          case 'complete':
            setStatus('Completed')
            setIsRunning(false)
            addLog(`Result: ${data.summary}`, 'info')
            ws.current?.close()
            break
          case 'stopped':
            setStatus('Stopped')
            setIsRunning(false)
            addLog(data.message || 'Task stopped.', 'error')
            ws.current?.close()
            break
        }
      }

      ws.current.onerror = () => {
        addLog('Connection error — is the backend running?', 'error')
        setIsRunning(false)
        setStatus('Error')
      }

    } catch (error) {
      addLog(`Failed to start execution: ${error}`, 'error')
      setIsRunning(false)
      setStatus('Error')
    }
  }

  const sub = classification?.sub_category
  const meta = sub ? (CATEGORY_LABELS[sub] || CATEGORY_LABELS['unknown']) : null

  return (
    <div className="container">
      <h1 style={{ marginBottom: '0.5rem', color: '#38bdf8' }}>AutoOS Gateway</h1>
      <p style={{ marginBottom: '2rem', color: '#94a3b8' }}>Unified AI Control for Web &amp; Desktop</p>

      <div className="card">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What would you like me to do? (e.g. 'Open Valorant' or 'Find my report')"
          disabled={isRunning}
          onKeyDown={(e) => e.key === 'Enter' && handleRun()}
        />
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            id="btn-execute"
            onClick={handleRun}
            disabled={isRunning || !input}
          >
            {isRunning ? 'Running...' : 'Execute Task'}
          </button>

          {isRunning && (
            <button
              id="btn-stop"
              className="btn-stop"
              onClick={handleStop}
            >
              Stop
            </button>
          )}
        </div>
      </div>

      {classification && meta && (
        <div className={`classification-banner ${meta.css}`}>
          <div className="banner-left">
            <div className="badge-label">{meta.label}</div>
            {classification.plain_english_plan && (
              <div className="badge-plan">{classification.plain_english_plan}</div>
            )}
          </div>
          {classification.needs_hitl && (
            <span className="hitl-warning">Needs confirmation</span>
          )}
        </div>
      )}

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
