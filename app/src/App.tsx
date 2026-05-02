import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import './index.css'
import './App.css'

/* ── Icons ──────────────────────────────────────────────────────────────── */

const I = {
  Zap:      () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  Chat:     () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
  Folder:   () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>,
  Settings: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1.08-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  Mic:      () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>,
  Send:     () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
  Play:     () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>,
  Check:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
  AlertC:   () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>,
  Tool:     () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>,
  Info:     () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>,
  User:     () => <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
  Stop:     () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>,
  Globe:    () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>,
  X:        () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
}

/* ── Tool name map (no emojis) ──────────────────────────────────────────── */

const TOOL_LABEL: Record<string, string> = {
  run_terminal_command: 'Terminal',
  open_application:     'Open App',
  get_system_info:      'System Info',
  list_directory:       'List Directory',
  read_file:            'Read File',
  write_file:           'Write File',
  search_files:         'Search Files',
  get_clipboard:        'Clipboard Read',
  set_clipboard:        'Clipboard Write',
  send_notification:    'Notification',
  open_url:             'Open URL',
  browse_web:           'Web Automation',
}

/* ── Types ──────────────────────────────────────────────────────────────── */

interface Log {
  from: 'user' | 'sys'
  kind: 'tool-call' | 'tool-result' | 'thinking' | 'info' | 'error' | 'ok'
  text: string
  time: string
  tool?: string
  detail?: string
}

interface HitlReq { stepId: string; prompt: string }

interface BrowserPopup {
  task: string
  step: number
  memory: string
  actions: string[]
  visible: boolean
}

/* ── Helpers ────────────────────────────────────────────────────────────── */

const wsUrl = (path: string) => {
  const p = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${p}//${window.location.host}${path}`
}

const fmtArgs = (t: string, a: Record<string, unknown>): string => {
  if (t === 'run_terminal_command') return `$ ${a.command ?? ''}`
  if (t === 'open_application')     return String(a.app_name ?? '')
  if (t === 'list_directory')       return String(a.path ?? '~')
  if (t === 'read_file')            return String(a.path ?? '')
  if (t === 'write_file')           return String(a.path ?? '')
  if (t === 'search_files')         return `"${a.query ?? ''}" in ${a.search_path ?? '~'}`
  if (t === 'open_url')             return String(a.url ?? '')
  if (t === 'browse_web')           return String(a.task ?? '').slice(0, 100)
  if (t === 'send_notification')    return String(a.title ?? '')
  if (t === 'set_clipboard')        return String(a.text ?? '').slice(0, 60)
  return JSON.stringify(a)
}

// Convert raw tool result JSON into a clean readable string
const fmtResult = (tool: string, raw: string): string => {
  try {
    const obj = JSON.parse(raw)
    if (typeof obj !== 'object' || obj === null) return raw

    // Terminal output
    if (tool === 'run_terminal_command') {
      if (!obj.success) return `Error (exit ${obj.exit_code}): ${obj.stderr || 'unknown error'}`
      const out = (obj.stdout || '').trim()
      return out || 'Command completed successfully.'
    }

    // Directory listing
    if (tool === 'list_directory') {
      if (!obj.success) return obj.error || 'Could not list directory.'
      const entries: Array<{name: string; type: string; size_bytes?: number}> = obj.entries || []
      if (entries.length === 0) return 'Directory is empty.'
      const dirs  = entries.filter(e => e.type === 'directory').map(e => e.name + '/').slice(0, 6)
      const files = entries.filter(e => e.type === 'file').map(e => e.name).slice(0, 8)
      const lines: string[] = []
      if (dirs.length)  lines.push(dirs.join('  '))
      if (files.length) lines.push(files.join('  '))
      if (obj.count > 14) lines.push(`...and ${obj.count - 14} more`)
      return lines.join('\n')
    }

    // Search results
    if (tool === 'search_files') {
      if (!obj.success) return obj.error || 'Search failed.'
      const results: Array<{name: string; path: string}> = obj.results || []
      if (results.length === 0) return 'No files found.'
      return results.slice(0, 6).map(r => r.name).join('\n')
    }

    // Read file
    if (tool === 'read_file') {
      if (!obj.success) return obj.error || 'Could not read file.'
      const lines = (obj.content || '').split('\n').slice(0, 8)
      return lines.join('\n') + (obj.truncated ? '\n...' : '')
    }

    // System info
    if (tool === 'get_system_info') {
      const parts: string[] = []
      if (obj.cpu_percent != null) parts.push(`CPU ${obj.cpu_percent}%`)
      if (obj.memory_percent != null) parts.push(`RAM ${obj.memory_percent}%`)
      if (obj.disk_free_gb != null) parts.push(`Disk free: ${obj.disk_free_gb} GB`)
      if (obj.battery_percent != null) parts.push(`Battery: ${obj.battery_percent}%${obj.battery_plugged ? ' (charging)' : ''}`)
      return parts.join('  ·  ') || 'System info retrieved.'
    }

    // Clipboard read
    if (tool === 'get_clipboard') {
      if (!obj.success) return 'Could not read clipboard.'
      return obj.content ? `"${String(obj.content).slice(0, 120)}"` : '(clipboard is empty)'
    }

    // Browse web result
    if (tool === 'browse_web') {
      if (!obj.success) return obj.error || 'Browser task failed.'
      return (obj.result || 'Browser task completed.').slice(0, 300)
    }

    // Generic: extract message or error
    if (!obj.success && obj.error) return `Error: ${obj.error}`
    if (!obj.success && obj.message) return `Failed: ${obj.message}`
    if (obj.message) return obj.message
    if (obj.result) return String(obj.result).slice(0, 200)
    return 'Done.'
  } catch {
    // Not JSON — return as-is (terminal stdout etc.)
    return raw.trim().slice(0, 400)
  }
}

const ts = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

const bc = new BroadcastChannel('autoos-popup')

const PopupApp = () => {
  const [popup, setPopup] = useState<BrowserPopup | null>(null)

  useEffect(() => {
    // Listen for state updates from the main window
    bc.onmessage = (e) => {
      if (e.data.type === 'state') setPopup(e.data.state)
      if (e.data.type === 'close') window.close()
    }
    // Ask main window for initial state
    bc.postMessage({ type: 'ready' })
    
    return () => { bc.onmessage = null }
  }, [])

  const handleStop = () => {
    bc.postMessage({ type: 'stop' })
  }

  if (!popup) return <div className="popup-window-body" style={{ padding: '20px' }}>Connecting...</div>

  return (
    <div className="popup-window-body browser-popup-fullscreen">
      <div className="browser-popup-header">
        <span className="browser-popup-title"><I.Globe /> Browser Automation</span>
        <button className="stop-btn native-stop" onClick={handleStop} title="Stop Automation">
          <I.Stop /> Stop
        </button>
      </div>
      <div className="browser-popup-body">
        {popup.step > 0 && <div className="browser-popup-step">Step {popup.step}</div>}
        {popup.memory && <div className="browser-popup-memory">{popup.memory}</div>}
        {popup.actions.length > 0 && (
          <div className="browser-popup-actions">
            {popup.actions.map((a, i) => (
              <div key={i} className="browser-popup-action">{a}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── App ────────────────────────────────────────────────────────────────── */

type View = 'chat' | 'library' | 'settings'

export type DBWorkflow = {
  id: string
  name: string
  description?: string
  steps?: any
  events?: any
  source: string
  created_at: string
}

function App({ sharedWorkflowId, sharedData, sharedBlobId }: { sharedWorkflowId?: string | null, sharedData?: string | null, sharedBlobId?: string | null }) {
  const [view, setView]     = useState<View>('chat')
  const [input, setInput]   = useState('')
  const [busy, setBusy]     = useState(false)
  const [logs, setLogs]     = useState<Log[]>([])
  const [hitl, setHitl]     = useState<HitlReq | null>(null)
  const [hitlIn, setHitlIn] = useState('')
  const [execId, setExecId] = useState<string | null>(null)
  const [rec, setRec]       = useState(false)
  const [browserPopup, setBrowserPopup] = useState<BrowserPopup | null>(null)
  
  const [workflows, setWorkflows] = useState<DBWorkflow[]>([])
  const [sharedWorkflow, setSharedWorkflow] = useState<DBWorkflow | null>(null)
  const [saveWfIndex, setSaveWfIndex] = useState<number | null>(null)
  const [saveWfName, setSaveWfName] = useState('')

  // Settings state
  const [apiKey, setApiKey]       = useState(localStorage.getItem('autoos_api_key') ?? '')
  const [model, setModel]        = useState(localStorage.getItem('autoos_model') ?? 'gemini-2.0-flash')
  const [voiceOut, setVoiceOut]   = useState(localStorage.getItem('autoos_voice_out') !== 'false')
  const [headless, setHeadless]   = useState(localStorage.getItem('autoos_headless') === 'true')

  const wsRef    = useRef<WebSocket | null>(null)
  const endRef   = useRef<HTMLDivElement>(null)
  const recRef   = useRef<MediaRecorder | null>(null)
  const chunks   = useRef<BlobPart[]>([])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [logs])

  // Persist settings
  useEffect(() => { localStorage.setItem('autoos_api_key', apiKey) },       [apiKey])
  useEffect(() => { localStorage.setItem('autoos_model', model) },          [model])
  useEffect(() => { localStorage.setItem('autoos_voice_out', String(voiceOut)) }, [voiceOut])
  useEffect(() => { localStorage.setItem('autoos_headless', String(headless)) },  [headless])

  // BroadcastChannel for popup window
  useEffect(() => {
    const handleBcMessage = (e: MessageEvent) => {
      if (e.data.type === 'ready') {
        if (browserPopup) bc.postMessage({ type: 'state', state: browserPopup })
      }
      if (e.data.type === 'stop') {
        stopTask()
      }
    }
    bc.addEventListener('message', handleBcMessage)
    return () => bc.removeEventListener('message', handleBcMessage)
  }, [browserPopup]) // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch library workflows
  const fetchWorkflows = async () => {
    try {
      const res = await fetch('http://localhost:8765/api/workflows')
      if (res.ok) setWorkflows(await res.json())
    } catch (e) {
      console.error("Failed to fetch workflows", e)
    }
  }

  useEffect(() => {
    if (view === 'library') fetchWorkflows()
  }, [view])

  // Handle shared workflow link from normal query params (browser fallback)
  useEffect(() => {
    if (sharedBlobId) {
      fetch(`https://jsonblob.com/api/jsonBlob/${sharedBlobId}`)
        .then(res => res.json())
        .then(wf => {
          if (wf && wf.name) setSharedWorkflow(wf)
        })
        .catch(console.error)
    } else if (sharedData) {
      try {
        const wf = JSON.parse(decodeURIComponent(atob(sharedData)))
        if (wf && wf.name) setSharedWorkflow(wf)
      } catch (e) {
        console.error("Failed to parse shared workflow", e)
      }
    } else if (sharedWorkflowId) {
      fetch(`http://localhost:8765/api/workflows/${sharedWorkflowId}`)
        .then(res => res.json())
        .then(wf => {
          if (wf && wf.id) setSharedWorkflow(wf)
        })
        .catch(console.error)
    }
  }, [sharedWorkflowId, sharedData, sharedBlobId])

  // Handle native deep links (autoos://)
  useEffect(() => {
    // @ts-ignore
    if (window.electronAPI) {
      
      const processUrl = (url: string) => {
        try {
          const parsed = new URL(url);
          const blob = parsed.searchParams.get('blob');
          const data = parsed.searchParams.get('data');
          
          if (blob) {
            fetch(`https://jsonblob.com/api/jsonBlob/${blob}`)
              .then(res => res.json())
              .then(wf => { if (wf && wf.name) setSharedWorkflow(wf) })
              .catch(console.error);
          } else if (data) {
            const wf = JSON.parse(decodeURIComponent(atob(data)));
            if (wf && wf.name) setSharedWorkflow(wf);
          }
        } catch (err) {
          console.error("Failed to process deep link", err);
        }
      };

      // 1. Check if there is an initial URL waiting for us from app launch
      // @ts-ignore
      if (window.electronAPI.invoke) {
        // @ts-ignore
        window.electronAPI.invoke('get-initial-deep-link').then((url) => {
          if (url) processUrl(url);
        });
      }

      // 2. Listen for any future URLs while the app is already open
      // @ts-ignore
      if (window.electronAPI.onMessage) {
        // @ts-ignore
        window.electronAPI.onMessage('deep-link', processUrl);
      }
    }
  }, []);

  // Broadcast state updates and open window
  const popupRef = useRef<Window | null>(null)
  useEffect(() => {
    if (browserPopup?.visible) {
      if (!popupRef.current || popupRef.current.closed) {
        const w = 420; const h = 480;
        const left = window.screen.availWidth ? window.screen.availWidth - w - 20 : window.screen.width - w - 20;
        const top = 20;
        popupRef.current = window.open(
          window.location.origin + '?popup=true',
          '_blank',
          `width=${w},height=${h},left=${left},top=${top}`
        )
      }
      bc.postMessage({ type: 'state', state: browserPopup })
    } else {
      if (popupRef.current && !popupRef.current.closed) {
        bc.postMessage({ type: 'close' })
        popupRef.current = null
      }
    }
  }, [browserPopup])

  const log = (text: string, from: Log['from'], kind: Log['kind'] = 'info', extra: Partial<Log> = {}) =>
    setLogs(p => [...p, { from, kind, text, time: ts(), ...extra }])

  /* ── Stop task ────────────────────────────────────────────────────────── */

  const stopTask = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setBusy(false)
    setExecId(null)
    setBrowserPopup(null)
    log('Task stopped by user.', 'sys', 'error')
  }

  /* ── Voice recording ───────────────────────────────────────────────────── */

  const toggleRec = async () => {
    if (rec) { recRef.current?.stop(); setRec(false); return }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      recRef.current = mr; chunks.current = []
      mr.ondataavailable = e => { if (e.data.size > 0) chunks.current.push(e.data) }
      mr.onstop = async () => {
        const blob = new Blob(chunks.current, { type: 'audio/wav' })
        const fd = new FormData(); fd.append('audio', blob, 'voice.wav')
        log('Transcribing...', 'sys', 'thinking')
        try {
          const r = await fetch('/voice/transcribe', { method: 'POST', body: fd })
          if (r.ok) { const d = await r.json(); if (d.text) setInput(p => p ? p + ' ' + d.text : d.text) }
          else log('Transcription failed.', 'sys', 'error')
        } catch { log('Voice server unreachable.', 'sys', 'error') }
        finally { stream.getTracks().forEach(t => t.stop()) }
      }
      mr.start(); setRec(true)
    } catch { log('Microphone unavailable.', 'sys', 'error') }
  }

  /* ── Run task ──────────────────────────────────────────────────────────── */

  const run = async (overrideTask?: string) => {
    const taskToRun = overrideTask || input;
    if (!taskToRun.trim() || busy) return
    const task = taskToRun; setInput(''); setBusy(true)
    log(task, 'user')
    try {
      const res = await fetch('/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task }),
      })
      if (!res.ok) throw new Error()
      const { id } = await res.json()
      setExecId(id)

      const ws = new WebSocket(wsUrl(`/ws/execution/${id}`))
      wsRef.current = ws

      ws.onopen = () => {
        ws.send(JSON.stringify({ type: 'start', task }))
        // No 'Processing request...' noise — first real event from the server is enough
      }

      ws.onmessage = ({ data: raw }) => {
        const d = JSON.parse(raw)
        switch (d.type) {
          case 'thinking':
            // Only show the first thinking event per task; suppress "Understanding your request..."
            // which is redundant when a tool call follows immediately
            setLogs(p => {
              const lastSys = [...p].reverse().find(x => x.from === 'sys')
              if (lastSys?.kind === 'thinking') return p // already showing a spinner
              return [...p, { from: 'sys' as const, kind: 'thinking' as const, text: d.message || 'Working...', time: ts() }]
            })
            break

          case 'tool_call':
            // Replace last thinking bubble with the tool call (cleaner flow)
            setLogs(p => {
              const filtered = p[p.length - 1]?.kind === 'thinking' ? p.slice(0, -1) : p
              return [...filtered, {
                from: 'sys' as const, kind: 'tool-call' as const,
                text: TOOL_LABEL[d.tool] || d.tool,
                time: ts(),
                tool: d.tool,
                detail: d.args ? fmtArgs(d.tool, d.args) : undefined,
              }]
            })
            break

          case 'tool_result':
            log(TOOL_LABEL[d.tool] || d.tool, 'sys', 'tool-result', {
              tool: d.tool,
              detail: d.result ? fmtResult(d.tool, d.result) : undefined,
            })
            break

          case 'step_start':
            // Suppress — too noisy; tool_call already shows what's running
            break

          case 'step_done':
            // Suppress — tool_result covers this
            break

          case 'step_error':
            log(d.error || 'An error occurred.', 'sys', 'error'); break

          case 'complete': {
            setBusy(false); setExecId(null); setBrowserPopup(null)
            // d.summary might be an object/array from Gemini — extract text
            let summary = d.summary || 'Task completed.'
            if (typeof summary !== 'string') {
              try { summary = JSON.stringify(summary) } catch { summary = String(summary) }
            }
            log(summary, 'sys', 'ok')
            ws.close(); break
          }

          case 'hitl_request':
            setHitl({ stepId: d.step_id, prompt: d.prompt }); setBusy(false); break

          case 'browser_start':
            setBrowserPopup({ task: d.task || '', step: 0, memory: 'Starting browser...', actions: [], visible: true })
            break

          case 'browser_step':
            setBrowserPopup(prev => prev ? {
              ...prev,
              step: d.step || prev.step + 1,
              memory: d.memory || '',
              actions: d.actions || [],
            } : null)
            break

          case 'browser_end':
            setBrowserPopup(prev => prev ? { ...prev, memory: 'Browser task finished.', actions: [] } : null)
            // Auto-hide after 3 seconds
            setTimeout(() => setBrowserPopup(null), 3000)
            break

          case 'speech':
            break
        }
      }

      ws.onerror = () => { log('Connection lost. Is the server running?', 'sys', 'error'); setBusy(false); setExecId(null) }
      ws.onclose = () => { setBusy(false) }
    } catch {
      log('Cannot reach the server.', 'sys', 'error'); setBusy(false); setExecId(null)
    }
  }

  /* ── HITL submit ───────────────────────────────────────────────────────── */

  const submitHitl = async () => {
    if (!hitlIn.trim() || !execId) return
    const txt = hitlIn; setHitlIn(''); setHitl(null); setBusy(true); log(txt, 'user')
    try {
      await fetch(`/executions/${execId}/respond`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: txt }),
      })
      log('Response sent. Resuming...', 'sys', 'info')
    } catch { log('Failed to send response.', 'sys', 'error'); setBusy(false) }
  }

  /* ── Save Workflow ─────────────────────────────────────────────────────── */
  
  const handleSaveWorkflow = async (name: string, i: number) => {
    const precedingLogs = logs.slice(0, i).reverse();
    const lastUserLogIndex = precedingLogs.findIndex(x => x.from === 'user');
    const lastUserTask = precedingLogs[lastUserLogIndex]?.text || 'AutoOS Task';
    
    const relevantLogs = precedingLogs.slice(0, lastUserLogIndex).reverse();
    const steps = relevantLogs.filter(l => l.kind === 'tool-call' || l.kind === 'tool-result').map(l => ({
      tool: l.tool || l.text,
      detail: l.detail
    }));

    try {
      await fetch('http://localhost:8765/api/workflows', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name, 
          description: lastUserTask, 
          steps: steps,
          source: 'chat' 
        })
      });
      setSaveWfIndex(null);
      alert('Saved to your Library!');
    } catch (err) { alert('Failed to save.'); }
  }

  /* ── Render a single log entry ─────────────────────────────────────────── */

  const renderLog = (l: Log, i: number) => {
    const key = `${i}-${l.kind}-${l.time}`

    if (l.from === 'user')
      return <div key={key} className="msg user"><div className="bubble user">{l.text}</div></div>

    if (l.kind === 'tool-call') {
      const label = l.tool ? (TOOL_LABEL[l.tool] ?? l.tool) : l.text
      return (
        <div key={key} className="msg">
          <div className="bubble sys tool-call">
            <span className="tool-label calling"><I.Tool /> {label}</span>
            {l.detail && <div className="tool-detail">{l.detail}</div>}
            <span className="ts">{l.time}</span>
          </div>
        </div>
      )
    }

    if (l.kind === 'tool-result') {
      const label = l.tool ? (TOOL_LABEL[l.tool] ?? l.tool) : l.text
      return (
        <div key={key} className="msg">
          <div className="bubble sys tool-result">
            <span className="tool-label done"><I.Check /> {label}</span>
            {l.detail && <div className="tool-detail">{l.detail}</div>}
            <span className="ts">{l.time}</span>
          </div>
        </div>
      )
    }

    if (l.kind === 'thinking')
      return (
        <div key={key} className="msg">
          <div className="bubble sys">
            <div className="s-think"><span className="spin-dot" /><span>{l.text}</span></div>
            <span className="ts">{l.time}</span>
          </div>
        </div>
      )

    const cls  = l.kind === 'error' ? 's-err' : l.kind === 'ok' ? 's-ok' : 's-info'
    const icon = l.kind === 'ok' ? <I.Check /> : l.kind === 'error' ? <I.AlertC /> : <I.Info />

    return (
      <div key={key} className="msg">
        <div className="bubble sys">
          <div className={cls}>{icon}<span>{l.text}</span></div>
          {l.kind === 'ok' && (
            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border)' }}>
              {saveWfIndex === i ? (
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input type="text" className="setting-input" style={{ margin: 0, padding: '4px 8px', fontSize: '12px' }}
                         autoFocus
                         value={saveWfName} onChange={e => setSaveWfName(e.target.value)}
                         onKeyDown={async e => {
                           if (e.key === 'Enter') {
                             handleSaveWorkflow(saveWfName, i);
                           } else if (e.key === 'Escape') {
                             setSaveWfIndex(null);
                           }
                         }} />
                  <button className="run-btn" style={{ padding: '4px 8px', fontSize: '12px' }}
                          onClick={() => handleSaveWorkflow(saveWfName, i)}>Save</button>
                  <button className="icon-btn" style={{ padding: '4px' }} onClick={() => setSaveWfIndex(null)}><I.X /></button>
                </div>
              ) : (
                <button className="run-btn" style={{ padding: '6px 12px', background: 'transparent', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
                  onClick={() => {
                    const lastUserTask = logs.slice(0, i).reverse().find(x => x.from === 'user')?.text || 'AutoOS Task';
                    setSaveWfName(lastUserTask.slice(0, 50));
                    setSaveWfIndex(i);
                  }}>
                  <I.Folder /> Save as Workflow
                </button>
              )}
            </div>
          )}
          <span className="ts">{l.time}</span>
        </div>
      </div>
    )
  }


  /* ── Main render ───────────────────────────────────────────────────────── */

  return (
    <div className="app-layout">

      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <I.Zap />
          <h1>Auto<span className="accent">OS</span></h1>
        </div>

        <button className={`nav-item ${view === 'chat' ? 'active' : ''}`}
                onClick={() => setView('chat')}>
          <I.Chat /> New Task
        </button>
        <button className={`nav-item ${view === 'library' ? 'active' : ''}`}
                onClick={() => setView('library')}>
          <I.Folder /> Workflows
        </button>
        <button className={`nav-item ${view === 'settings' ? 'active' : ''}`}
                onClick={() => setView('settings')}>
          <I.Settings /> Settings
        </button>

        <div className="sidebar-spacer" />

        <div className="sidebar-status">
          <span className="status-dot" />
          <span>Gateway Active</span>
        </div>

        <button className="nav-item primary-btn" onClick={() => { setView('chat'); toggleRec() }}>
          <I.Mic /> {rec ? 'Stop Recording' : 'Voice Input'}
        </button>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main className="main-content">

        {/* ── Chat view ─────────────────────────────────────────────────── */}
        {view === 'chat' && (
          <div className="chat-container">
            <div className="chat-header">
              {busy && <span className="running-indicator" />}
              <h2>{busy ? 'Running Task' : 'New Task'}</h2>
            </div>

            <div className="chat-history">
              {logs.length === 0 && (
                <div className="empty-state">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                  <p>Describe a task you'd like to automate. I can run commands, open apps, manage files, browse the web, and more.</p>
                </div>
              )}
              {logs.map(renderLog)}
              <div ref={endRef} />
            </div>

            <div className="chat-input-area">
              <div className="input-row">
                <button className={`icon-btn ${rec ? 'recording' : ''}`}
                        disabled={busy} onClick={toggleRec}>
                  <I.Mic />
                </button>
                <input id="task-input" type="text" value={input}
                       onChange={e => setInput(e.target.value)}
                       placeholder={rec ? 'Listening...' : 'What would you like me to do?'}
                       disabled={busy}
                       onKeyDown={e => e.key === 'Enter' && run()}
                       autoFocus />
                {busy ? (
                  <button className="icon-btn stop-btn" onClick={stopTask}
                          title="Stop task">
                    <I.Stop />
                  </button>
                ) : (
                  <button className={`icon-btn ${input.trim() ? 'send-active' : ''}`}
                          onClick={run} disabled={!input.trim()}>
                    <I.Send />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── Library view ──────────────────────────────────────────────── */}
        {view === 'library' && (
          <div className="library-container">
            <h2>Workflows</h2>
            <div className="grid">
              {workflows.length === 0 ? (
                <div className="empty-state">No workflows saved yet. Recorded workflows from the extension will appear here.</div>
              ) : workflows.map((wf) => (
                <div className="card" key={wf.id}>
                  <h3>{wf.name}</h3>
                  <p>{wf.description || 'No description available.'}</p>
                  <div className="card-footer">
                    <span className="meta">{new Date(wf.created_at).toLocaleDateString()} • {wf.source}</span>
                    <div className="wf-actions" style={{ display: 'flex', gap: '8px' }}>
                      <button className="run-btn" title="Run workflow" onClick={() => { 
                        let cmd = wf.description || wf.name;
                        if (wf.source === 'extension' && wf.events) {
                          cmd = `Execute this exact browser workflow: ${JSON.stringify(wf.events)}`;
                        } else if (wf.steps && wf.steps.length > 0) {
                          cmd += `\n\nContext from previous successful run:\n` + JSON.stringify(wf.steps);
                        }
                        setView('chat'); 
                        run(cmd); 
                      }}>
                        <I.Play /> Run
                      </button>
                      <button className="icon-btn" title="Copy Link" onClick={async () => {
                        try {
                          const res = await fetch('http://localhost:8765/api/share', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(wf)
                          });
                          if (!res.ok) throw new Error("Backend failed to create share link");
                          const data = await res.json();
                          const blobId = data.blob_id;
                          if (blobId) {
                            const url = `autoos://share?blob=${blobId}`;
                            navigator.clipboard.writeText(url);
                            alert('Direct App Link copied: ' + url);
                          } else {
                            throw new Error("No blob ID");
                          }
                        } catch (e) {
                          console.error("Online share failed, using fallback:", e);
                          // Fallback to offline base64
                          const wfData = btoa(encodeURIComponent(JSON.stringify(wf)));
                          const url = `autoos://share?data=${wfData}`;
                          navigator.clipboard.writeText(url);
                          alert('Offline direct app link copied to clipboard!');
                        }
                      }}>
                        <I.Zap />
                      </button>
                      <button className="icon-btn stop-btn" title="Delete" onClick={async () => {
                        if (confirm('Delete this workflow?')) {
                          await fetch(`http://localhost:8765/api/workflows/${wf.id}`, { method: 'DELETE' });
                          fetchWorkflows();
                        }
                      }}>
                        <I.X />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Settings view ─────────────────────────────────────────────── */}
        {view === 'settings' && (
          <div className="settings-container">
            <h2>Settings</h2>

            <div className="settings-group">
              <div className="settings-group-title">Model Configuration</div>

              <div className="setting-row">
                <div className="setting-info">
                  <div className="label">Gemini API Key</div>
                  <div className="desc">Your Google AI API key for the gateway</div>
                </div>
                <input className="setting-input" type="password" value={apiKey}
                       onChange={e => setApiKey(e.target.value)}
                       placeholder="AIza..." />
              </div>

              <div className="setting-row">
                <div className="setting-info">
                  <div className="label">Model</div>
                  <div className="desc">Gemini model for the agent</div>
                </div>
                <select className="setting-select" value={model} onChange={e => setModel(e.target.value)}>
                  <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                  <option value="gemini-2.5-flash-preview-05-20">gemini-2.5-flash</option>
                  <option value="gemini-2.5-pro-preview-05-06">gemini-2.5-pro</option>
                  <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                </select>
              </div>
            </div>

            <div className="settings-group">
              <div className="settings-group-title">Voice</div>

              <div className="setting-row">
                <div className="setting-info">
                  <div className="label">Voice Output</div>
                  <div className="desc">Speak status updates aloud</div>
                </div>
                <button className={`toggle ${voiceOut ? 'on' : ''}`}
                        onClick={() => setVoiceOut(!voiceOut)} />
              </div>
            </div>

            <div className="settings-group">
              <div className="settings-group-title">Browser Automation</div>

              <div className="setting-row">
                <div className="setting-info">
                  <div className="label">Headless Mode</div>
                  <div className="desc">Run browser in background without visible window</div>
                </div>
                <button className={`toggle ${headless ? 'on' : ''}`}
                        onClick={() => setHeadless(!headless)} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ── HITL overlay ─────────────────────────────────────────────────── */}
      {hitl && (
        <div className="hitl-overlay">
          <div className="hitl-modal">
            <div className="hitl-icon"><I.User /></div>
            <h3>Input Required</h3>
            <p>{hitl.prompt}</p>
            <input className="hitl-input" type="text" value={hitlIn}
                   onChange={e => setHitlIn(e.target.value)}
                   placeholder="Type your response..."
                   onKeyDown={e => e.key === 'Enter' && submitHitl()}
                   autoFocus />
            <div className="hitl-actions">
              <button className="btn-cancel" onClick={() => {
                setHitl(null); setBusy(false); setExecId(null)
                log('Task cancelled by user.', 'sys', 'error')
              }}>Cancel</button>
              <button className="btn-submit" onClick={submitHitl} disabled={!hitlIn.trim()}>
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
      {/* ── Shared workflow prompt ───────────────────────────────────────── */}
      {sharedWorkflow && (
        <div className="hitl-overlay">
          <div className="hitl-modal" style={{ maxWidth: '500px' }}>
            <h3>Shared Workflow Received</h3>
            <p style={{ margin: '12px 0', opacity: 0.8 }}>
              Someone shared the workflow <strong>"{sharedWorkflow.name}"</strong> with you. Would you like to run it now?
            </p>
            <div className="hitl-actions">
              <button className="secondary-btn" onClick={() => setSharedWorkflow(null)}>
                Cancel
              </button>
              <button className="primary-btn" onClick={() => {
                let cmd = sharedWorkflow.description || sharedWorkflow.name;
                if (sharedWorkflow.source === 'extension' && sharedWorkflow.events) {
                  cmd = `Execute this exact browser workflow: ${JSON.stringify(sharedWorkflow.events)}`;
                }
                setInput(cmd);
                setSharedWorkflow(null);
              }}>
                Load Workflow
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}

export default function Root() {
  const isPopup = new URLSearchParams(window.location.search).get('popup') === 'true'
  const workflowId = new URLSearchParams(window.location.search).get('workflow_id')
  const sharedData = new URLSearchParams(window.location.search).get('share')
  const sharedBlobId = new URLSearchParams(window.location.search).get('blob')
  
  if (isPopup) return <PopupApp />
  return <App sharedWorkflowId={workflowId} sharedData={sharedData} sharedBlobId={sharedBlobId} />
}
