import { useState, useEffect, useRef } from 'react'
import './index.css'
import './App.css'

// --- Icons (Inlined SVGs for Zero Dependencies) ---
const Icons = {
  Chat: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>,
  Folder: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>,
  Settings: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 0 9.4a1.65 1.65 0 0 0-1.82.33l2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>,
  Mic: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>,
  Send: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>,
  Globe: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>,
  Monitor: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>,
  Play: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>,
  Check: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>,
  Alert: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>,
}

interface LogEntry {
  source: 'user' | 'system';
  type: 'browser' | 'os' | 'info' | 'error' | 'success';
  message: string;
  timestamp: string;
}

interface HitlRequest {
  stepId: string;
  prompt: string;
}

function App() {
  const [currentView, setCurrentView] = useState<'chat' | 'library'>('chat');
  const [input, setInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [hitlRequest, setHitlRequest] = useState<HitlRequest | null>(null);
  const [hitlInput, setHitlInput] = useState('');
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  // Auto-scroll chat
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const addLog = (message: string, source: LogEntry['source'], type: LogEntry['type'] = 'info') => {
    setLogs(prev => [...prev, {
      source,
      type,
      message,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
  }

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const formData = new FormData();
          formData.append('audio', audioBlob, 'voice_command.wav');
          
          addLog('Transcribing voice command...', 'system', 'info');

          try {
            const response = await fetch('http://localhost:8765/voice/transcribe', {
              method: 'POST',
              body: formData,
            });

            if (response.ok) {
              const data = await response.json();
              if (data.text) {
                setInput((prev) => prev ? prev + ' ' + data.text : data.text);
              }
            } else {
              addLog('Failed to transcribe audio.', 'system', 'error');
            }
          } catch (error) {
            addLog('Network error during transcription.', 'system', 'error');
          } finally {
            stream.getTracks().forEach(track => track.stop());
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        addLog('Microphone access denied or unavailable.', 'system', 'error');
      }
    }
  };

  const handleRun = async () => {
    if (!input.trim() || isRunning) return;
    
    const taskText = input;
    setInput('');
    setIsRunning(true);
    addLog(taskText, 'user', 'info');
    addLog('Starting task...', 'system', 'info');

    try {
      const response = await fetch('http://localhost:8765/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: taskText })
      });
      
      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      const executionId = data.id;
      setActiveExecutionId(executionId);

      ws.current = new WebSocket(`ws://localhost:8765/ws/execution/${executionId}`);
      
      ws.current.onopen = () => {
        ws.current?.send(JSON.stringify({ type: 'start', task: taskText }));
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'step_start':
            addLog(`Executing: ${data.description}`, 'system', 'info');
            break;
          case 'step_done':
            addLog(`Completed: ${data.description}`, 'system', 'success');
            break;
          case 'step_error':
            addLog(`Error: ${data.error}`, 'system', 'error');
            break;
          case 'complete':
            setIsRunning(false);
            setActiveExecutionId(null);
            addLog(`Task Finished: ${data.summary}`, 'system', 'success');
            ws.current?.close();
            break;
          case 'classification':
            const isBrowser = data.category === 'browser';
            addLog(`Routed to ${isBrowser ? 'Browser' : 'OS'} Automation`, 'system', isBrowser ? 'browser' : 'os');
            break;
          case 'hitl_request':
            setHitlRequest({ stepId: data.step_id, prompt: data.prompt });
            setIsRunning(false); // Pause UI while waiting for human
            break;
          case 'speech':
             // Just show as info if speech is enabled
             addLog(`Voice: ${data.text}`, 'system', 'info');
             break;
        }
      };

      ws.current.onerror = () => {
        addLog('Connection lost. Please try again.', 'system', 'error');
        setIsRunning(false);
        setActiveExecutionId(null);
      };

    } catch (error) {
      addLog('Failed to connect to the local server.', 'system', 'error');
      setIsRunning(false);
      setActiveExecutionId(null);
    }
  }

  const handleHitlSubmit = async () => {
    if (!hitlInput.trim() || !activeExecutionId) return;
    
    const responseText = hitlInput;
    setHitlInput('');
    setHitlRequest(null);
    setIsRunning(true);
    addLog(responseText, 'user', 'info');
    
    try {
      await fetch(`http://localhost:8765/executions/${activeExecutionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response: responseText })
      });
      addLog('Response sent. Resuming task...', 'system', 'info');
    } catch (e) {
      addLog('Failed to send response.', 'system', 'error');
      setIsRunning(false);
    }
  }

  // Helper to render correct icon based on log type
  const renderLogIcon = (type: string) => {
    switch(type) {
      case 'browser': return <Icons.Globe />;
      case 'os': return <Icons.Monitor />;
      case 'success': return <Icons.Check />;
      case 'error': return <Icons.Alert />;
      default: return null;
    }
  }

  return (
    <div className="app-layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <h1>AutoFlow</h1>
        <button 
          className={`nav-item ${currentView === 'library' ? 'active' : ''}`}
          onClick={() => setCurrentView('library')}
        >
          <Icons.Folder /> My Workflows
        </button>
        <button 
          className={`nav-item ${currentView === 'chat' ? 'active' : ''}`}
          onClick={() => setCurrentView('chat')}
        >
          <Icons.Chat /> New Workflow
        </button>
        <div style={{ flex: 1 }}></div>
        <button className="nav-item">
          <Icons.Settings /> Settings
        </button>
        <button className="nav-item primary" onClick={() => {
          setCurrentView('chat');
          document.getElementById('task-input')?.focus();
          toggleRecording();
        }}>
          <Icons.Mic /> {isRecording ? 'Stop Recording' : 'Voice Input'}
        </button>
      </aside>

      {/* MAIN CONTENT */}
      <main className="main-content">
        {currentView === 'chat' ? (
          <div className="chat-container">
            <div className="chat-header">
              <h2>New Task</h2>
            </div>
            
            <div className="chat-history">
              {logs.length === 0 && (
                <div style={{ margin: 'auto', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '400px' }}>
                  <Icons.Chat />
                  <p style={{ marginTop: '1rem', fontSize: '1.125rem' }}>Describe a task you'd like me to automate for you. I can browse the web or use your computer.</p>
                </div>
              )}
              {logs.map((log, i) => (
                <div key={i} className={`message-wrapper ${log.source}`}>
                  <div className={`message-bubble ${log.source}`}>
                    {log.source === 'system' ? (
                      <div className={`status-${log.type === 'error' ? 'error' : log.type === 'success' ? 'success' : 'info'}`}>
                        {renderLogIcon(log.type)}
                        <span>{log.message}</span>
                      </div>
                    ) : (
                      log.message
                    )}
                    {log.source === 'system' && <span className="timestamp">{log.timestamp}</span>}
                  </div>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>

            <div className="chat-input-container">
              <div className="input-box">
                <button 
                  className={`icon-btn ${isRecording ? 'recording' : ''}`} 
                  disabled={isRunning} 
                  aria-label="Use voice"
                  onClick={toggleRecording}
                  style={isRecording ? { color: '#dc2626' } : {}}
                >
                  <Icons.Mic />
                </button>
                <input 
                  id="task-input"
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="What would you like me to do for you?"
                  disabled={isRunning}
                  onKeyDown={(e) => e.key === 'Enter' && handleRun()}
                  autoFocus
                />
                <button 
                  className={`icon-btn ${input.trim() ? 'primary' : ''}`}
                  onClick={handleRun} 
                  disabled={isRunning || !input.trim()}
                  aria-label="Send task"
                >
                  <Icons.Send />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="library-container">
            <h2>My Workflows</h2>
            <div className="grid">
              {/* Mock Data for Library */}
              {[
                { name: "Check Morning Email", desc: "Opens Gmail and summarizes unread messages.", date: "Today" },
                { name: "Book Flights", desc: "Searches Kayak for weekend flights to NYC.", date: "Yesterday" },
                { name: "Clear Downloads", desc: "Moves files older than 30 days to Trash.", date: "Last Week" },
              ].map((wf, i) => (
                <div className="card" key={i}>
                  <div>
                    <h3>{wf.name}</h3>
                    <p>{wf.desc}</p>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                    <span className="meta">Last run: {wf.date}</span>
                    <button 
                      className="card-btn" 
                      style={{ width: 'auto', padding: '0.5rem 1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}
                      onClick={() => {
                        setInput(wf.desc);
                        setCurrentView('chat');
                      }}
                    >
                      <Icons.Play /> Run
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* HITL OVERLAY */}
      {hitlRequest && (
        <div className="hitl-overlay">
          <div className="hitl-modal">
            <div style={{ color: 'var(--primary)', marginBottom: '1rem' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            </div>
            <h3>I need your input to continue</h3>
            <p>{hitlRequest.prompt}</p>
            <input 
              className="hitl-input"
              type="text" 
              value={hitlInput}
              onChange={(e) => setHitlInput(e.target.value)}
              placeholder="Type your response..."
              onKeyDown={(e) => e.key === 'Enter' && handleHitlSubmit()}
              autoFocus
            />
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                className="card-btn" 
                style={{ flex: 1 }}
                onClick={() => {
                  setHitlRequest(null);
                  setIsRunning(false);
                  setActiveExecutionId(null);
                  addLog("Task cancelled by user.", 'system', 'error');
                }}
              >
                Cancel Task
              </button>
              <button 
                className="hitl-btn" 
                style={{ flex: 2 }}
                onClick={handleHitlSubmit}
                disabled={!hitlInput.trim()}
              >
                Submit Response
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
