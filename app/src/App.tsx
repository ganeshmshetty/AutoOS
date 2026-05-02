import { useState, useEffect, useRef, useCallback } from 'react';
import { HashRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  MessageSquare, 
  LayoutDashboard, 
  Settings, 
  User, 
  Loader2, 
  XCircle, 
  ShieldAlert, 
  Puzzle, 
  Maximize2, 
  Send,
  Zap
} from 'lucide-react';
import ChatView from './ChatView';
import DashboardView from './DashboardView';
import SkillsView from './SkillsView';
import WorkflowsView from './WorkflowsView';
import { Message } from './types';
import './index.css';

import { FaceAuthModal } from './FaceAuthModal';

// --- Shared Types ---
declare global {
  interface Window {
    electronAPI: {
      resizeWindow: (w: number, h: number) => void;
      sendMessage: (channel: string, data: any) => void;
      onMessage: (channel: string, func: (...args: any[]) => void) => void;
    }
  }
}

function SidebarDock() {
  const location = useLocation();
  return (
    <nav className="side-dock">
      <div className="dock-top">
        <Link to="/" className={`dock-item ${location.pathname === '/' ? 'active' : ''}`} title="Chat Assistant">
          <MessageSquare size={24} />
        </Link>
        <Link to="/dashboard" className={`dock-item ${location.pathname === '/dashboard' ? 'active' : ''}`} title="System Dashboard">
          <LayoutDashboard size={24} />
        </Link>
        <Link to="/workflows" className={`dock-item ${location.pathname === '/workflows' ? 'active' : ''}`} title="Automated Workflows">
          <Zap size={24} />
        </Link>
        <Link to="/skills" className={`dock-item ${location.pathname === '/skills' ? 'active' : ''}`} title="Skills Marketplace">
          <Puzzle size={24} />
        </Link>
      </div>
      <div className="dock-bottom">
        <div className="dock-item" title="Settings">
          <Settings size={24} />
        </div>
        <div className="dock-item user-avatar" title="Account">
          <User size={24} />
        </div>
      </div>
    </nav>
  );
}

function App() {
  // --- Global State ---
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId, setThreadId] = useState<string>('');
  const [threadHistory, setThreadHistory] = useState<any[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'executing'>('idle');
  const [compactState, setCompactState] = useState<{ isCompact: boolean; status: string; description: string; type?: 'alert' | 'task' }>({
    isCompact: false,
    status: '',
    description: '',
    type: 'task'
  });
  const [miniInput, setMiniInput] = useState('');
  
  // --- Face Auth State ---
  const [faceRegistered, setFaceRegistered] = useState(false);
  const [faceAuthAction, setFaceAuthAction] = useState<{ mode: 'register' } | { mode: 'verify', task: string, workflow: any } | null>(null);

  useEffect(() => {
    fetch('http://localhost:8765/api/face-auth/status')
      .then(res => res.json())
      .then(data => setFaceRegistered(data.registered))
      .catch(console.error);
  }, []);
  
  const ws = useRef<WebSocket | null>(null);
  const guardianWs = useRef<WebSocket | null>(null);
  const executionIdRef = useRef<string | null>(null);

  const addMessage = useCallback((role: Message['role'], content: string, extra?: Record<string, any>) => {
    const msg: Message = {
      id: Math.random().toString(36).slice(2, 8),
      role,
      content,
      ...extra,
    };
    setMessages(prev => [...prev, msg]);
  }, []);

  // --- Global Cleanup on Unmount ---
  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
      if (guardianWs.current) {
        guardianWs.current.close();
        guardianWs.current = null;
      }
      executionIdRef.current = null;
    };
  }, []);

  // --- Initial Hydration ---
  useEffect(() => {
    const loadLatest = async () => {
      try {
        const res = await fetch('http://localhost:8765/system/threads/latest');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.id) {
          setThreadId(data.id);
          setMessages(data.messages || []);
        }
        const historyRes = await fetch('http://localhost:8765/system/threads');
        if (!historyRes.ok) throw new Error(`HTTP ${historyRes.status}`);
        setThreadHistory(await historyRes.json());
      } catch (e) { console.error(e); }
    };
    loadLatest();
  }, []);

  // --- Persistence Sync ---
  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    if (threadId && messages.length > 0) {
      timeoutId = setTimeout(() => {
        const sync = async () => {
          try {
            await fetch('http://localhost:8765/system/threads/save', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ id: threadId, messages })
            });
            const hRes = await fetch('http://localhost:8765/system/threads');
            if (hRes.ok) {
              setThreadHistory(await hRes.json());
            }
          } catch (e) {
            console.error('Persistence sync failed:', e);
          }
        };
        sync();
      }, 1000);
    }
    return () => { if (timeoutId) clearTimeout(timeoutId); };
  }, [threadId, messages]);
  // --- Guardian Heartbeat ---
  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    let isMounted = true;
    
    const connect = () => {
      if (!isMounted) return;
      guardianWs.current = new WebSocket(`ws://localhost:8765/ws/execution/global_guardian`);
      guardianWs.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'guardian_alert') {
            setCompactState({ isCompact: true, status: 'GUARDIAN ALERT', description: data.message, type: 'alert' });
            window.electronAPI?.resizeWindow(480, 180);
          }
        } catch (e) {
          console.error('Failed to parse guardian message:', e);
        }
      };
      guardianWs.current.onerror = () => guardianWs.current?.close();
      guardianWs.current.onclose = () => {
        if (isMounted) reconnectTimeout = setTimeout(connect, 3000);
      };
    };
    connect();
    return () => {
      isMounted = false;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      guardianWs.current?.close();
    };
  }, []);

  const compactStateRef = useRef(compactState);
  useEffect(() => { compactStateRef.current = compactState; }, [compactState]);

  const handleStop = async () => {
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify({ type: 'stop' }));
    if (executionIdRef.current) {
      fetch(`http://localhost:8765/executions/${executionIdRef.current}/stop`, { method: 'POST' }).catch(() => {});
    }
    setIsRunning(false);
    setStatus('idle');
    updateCompact(compactStateRef.current.isCompact, 'IDLE', 'Task cancelled.');
    addMessage('system', 'Execution stopped.');
  };

  const updateCompact = useCallback((isCompactActive: boolean, statusStr: string = '', desc: string = '') => {
    setCompactState(prev => ({ ...prev, isCompact: isCompactActive, status: statusStr, description: desc }));
    if (isCompactActive) window.electronAPI?.resizeWindow(480, 180);
    else window.electronAPI?.resizeWindow(900, 700);
  }, []);


  const handleRun = async (taskStr: string) => {
    if (!taskStr.trim() || isRunning) return;
    
    setIsRunning(true);
    setStatus('analyzing');
    addMessage('user', taskStr);
    updateCompact(compactStateRef.current.isCompact, 'ANALYZING', 'Thinking...');

    return new Promise<void>((resolve, reject) => {
      let settled = false;
      const safeReject = (err: any) => {
        if (settled) return;
        settled = true;
        setIsRunning(false);
        setStatus('idle');
        updateCompact(compactStateRef.current.isCompact, 'ERROR', String(err));
        reject(err);
      };
      const safeResolve = () => {
        if (settled) return;
        settled = true;
        resolve();
      };

      fetch('http://localhost:8765/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: taskStr })
      })
      .then(res => res.json())
      .then(data => {
        executionIdRef.current = data.id;
        ws.current = new WebSocket(`ws://localhost:8765/ws/execution/${data.id}`);
        
        ws.current.onopen = () => ws.current?.send(JSON.stringify({ type: 'start', task: taskStr }));
        
        ws.current.onerror = () => {
           safeReject(new Error('WebSocket connection error'));
           ws.current = null;
        };
        ws.current.onclose = () => {
           safeReject(new Error('WebSocket closed unexpectedly'));
           ws.current = null;
        };

        ws.current.onmessage = (event) => {
          let msg;
          try {
            msg = JSON.parse(event.data);
          } catch (e) {
            console.error("Malformed websocket message:", e);
            return;
          }

          switch (msg.type) {
            case 'classification':
              setStatus('executing');
              if (msg.plain_english_plan) {
                updateCompact(true, 'EXECUTING', msg.plain_english_plan);
                addMessage('agent', msg.plain_english_plan, { type: 'info' });
              }
              break;
            case 'complete':
              addMessage('agent', msg.summary);
              setIsRunning(false);
              setStatus('idle');
              updateCompact(compactStateRef.current.isCompact, '', msg.summary);
              safeResolve();
              break;
            case 'step_error':
              addMessage('system', `Error: ${msg.error}`);
              safeReject(msg.error);
              break;
          }
        };
      })
      .catch(e => {
        addMessage('system', 'Failed to connect to backend.');
        safeReject(e);
      });
    });
  };

  // --- UI Handlers ---
  const handleMiniRun = () => {
    handleRun(miniInput);
    setMiniInput('');
  };

  const handleExpand = () => updateCompact(false);

  const isAlert = compactState.type === 'alert';

  return (
    <div className="app-root">
      {compactState.isCompact && (
        <div className={`compact-popup ${isAlert ? 'alert-mode' : ''}`}>
          <div className="compact-header">
            <div className="compact-top-bar">
              <div className={`compact-status-chip ${isAlert ? 'chip-alert' : ''}`}>
                {isAlert ? <ShieldAlert size={12} /> : (isRunning ? <Loader2 className="animate-spin" size={12} /> : <MessageSquare size={12} />)}
                {compactState.status || 'READY'}
              </div>
              {!isAlert && <button className="compact-action-btn" onClick={handleExpand}><Maximize2 size={14} /></button>}
            </div>
            <div className="compact-desc">{compactState.description || (messages.length > 0 ? messages[messages.length-1].content : 'Waiting...')}</div>
          </div>
          <div className="compact-input-area">
            {isAlert ? <button className="dismiss-btn" onClick={() => updateCompact(false)}>DISMISS</button> : (
              <div className="compact-input-box">
                <input value={miniInput} onChange={(e) => setMiniInput(e.target.value)} placeholder={isRunning ? "Working..." : "Next instruction..."} disabled={isRunning} onKeyDown={(e) => e.key === 'Enter' && handleMiniRun()} />
                {isRunning ? <button className="compact-stop-btn" onClick={handleStop}><XCircle size={18} /></button> : <button className="compact-send-btn" onClick={handleMiniRun} disabled={!miniInput.trim()}><Send size={18} /></button>}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="main-app-container" style={{ display: compactState.isCompact ? 'none' : 'block' }}>
          <div className="root-layout">
            <SidebarDock />
            <div className="content-area">
              <Routes>
                <Route path="/" element={
                  <ChatView 
                    messages={messages} 
                    setMessages={setMessages} 
                    threadId={threadId} 
                    setThreadId={setThreadId}
                    threadHistory={threadHistory}
                    isRunning={isRunning}
                    status={status}
                    handleRun={handleRun}
                    handleStop={handleStop}
                  />
                } />
                <Route path="/dashboard" element={<DashboardView />} />
                <Route path="/workflows" element={<WorkflowsView handleRun={handleRun} isRunning={isRunning} faceRegistered={faceRegistered} setFaceAuthAction={setFaceAuthAction} />} />
                <Route path="/skills" element={<SkillsView />} />
              </Routes>
            </div>
          </div>
      </div>

      {/* --- Face Auth Modal --- */}
      {faceAuthAction && (
        <FaceAuthModal
          mode={faceAuthAction.mode}
          onCancel={() => setFaceAuthAction(null)}
          onSuccess={() => {
            if (faceAuthAction.mode === 'register') {
              setFaceRegistered(true);
              setFaceAuthAction(null);
            } else if (faceAuthAction.mode === 'verify') {
              // Dispatch event so WorkflowsView can start the workflow sequence
              window.dispatchEvent(new CustomEvent('face-verified', { detail: faceAuthAction }));
              setFaceAuthAction(null);
            }
          }}
        />
      )}
    </div>
  );
}

export default App;
