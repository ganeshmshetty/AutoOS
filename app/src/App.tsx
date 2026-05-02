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

  // --- Initial Hydration ---
  useEffect(() => {
    const loadLatest = async () => {
      try {
        const res = await fetch('http://localhost:8765/system/threads/latest');
        const data = await res.json();
        if (data.id) {
          setThreadId(data.id);
          setMessages(data.messages || []);
        }
        const historyRes = await fetch('http://localhost:8765/system/threads');
        setThreadHistory(await historyRes.json());
      } catch (e) { console.error(e); }
    };
    loadLatest();
  }, []);

  // --- Persistence Sync ---
  useEffect(() => {
    if (threadId && messages.length > 0) {
      const sync = async () => {
        await fetch('http://localhost:8765/system/threads/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: threadId, messages })
        });
        const hRes = await fetch('http://localhost:8765/system/threads');
        setThreadHistory(await hRes.json());
      };
      sync();
    }
  }, [messages, threadId]);

  // --- Guardian Heartbeat ---
  useEffect(() => {
    const connect = () => {
      guardianWs.current = new WebSocket(`ws://localhost:8765/ws/execution/global_guardian`);
      guardianWs.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'guardian_alert') {
          setCompactState({ isCompact: true, status: 'GUARDIAN ALERT', description: data.message, type: 'alert' });
          window.electronAPI?.resizeWindow(480, 180);
        }
      };
      guardianWs.current.onclose = () => setTimeout(connect, 3000);
    };
    connect();
    return () => guardianWs.current?.close();
  }, []);

  // --- Core Execution Engine (The Unified Brain) ---
  const addMessage = useCallback((role: Message['role'], content: string, extra: Partial<Message> = {}) => {
    setMessages(prev => [...prev, { id: Math.random().toString(36).substring(7), role, content, ...extra }]);
  }, []);

  const updateCompact = useCallback((isCompactActive: boolean, statusStr: string = '', desc: string = '') => {
    setCompactState(prev => ({ ...prev, isCompact: isCompactActive, status: statusStr, description: desc }));
    if (isCompactActive) window.electronAPI?.resizeWindow(480, 180);
    else window.electronAPI?.resizeWindow(900, 700);
  }, []);

  const handleStop = async () => {
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify({ type: 'stop' }));
    if (executionIdRef.current) {
      fetch(`http://localhost:8765/executions/${executionIdRef.current}/stop`, { method: 'POST' }).catch(() => {});
    }
    setIsRunning(false);
    setStatus('idle');
    updateCompact(compactState.isCompact, 'IDLE', 'Task cancelled.');
    addMessage('system', 'Execution stopped.');
  };

  const handleRun = async (taskStr: string) => {
    if (!taskStr.trim() || isRunning) return;
    
    setIsRunning(true);
    setStatus('analyzing');
    addMessage('user', taskStr);
    updateCompact(compactState.isCompact || false, 'ANALYZING', 'Thinking...');

    return new Promise<void>((resolve, reject) => {
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
        ws.current.onmessage = (event) => {
          const msg = JSON.parse(event.data);
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
              updateCompact(compactState.isCompact, '', msg.summary);
              resolve();
              break;
            case 'step_error':
              addMessage('system', `Error: ${msg.error}`);
              setIsRunning(false);
              setStatus('idle');
              updateCompact(compactState.isCompact, 'ERROR', msg.error);
              reject(msg.error);
              break;
          }
        };
      })
      .catch(e => {
        setIsRunning(false);
        setStatus('idle');
        addMessage('system', 'Failed to connect to backend.');
        reject(e);
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
