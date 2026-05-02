import { useState, useEffect } from 'react';
import { 
  Cpu, 
  Database, 
  HardDrive, 
  Battery as BatteryIcon, 
  Activity, 
  XCircle,
  AlertCircle
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { HealthData } from './types';

function DashboardView() {
  const [data, setData] = useState<HealthData | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const res = await fetch('http://localhost:8765/system/health');
      if (!res.ok) throw new Error('Failed to fetch system data');
      const health = await res.json();
      
      setData(health);
      setHistory((prev: any[]) => {
        const newHistory = [...prev, {
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          cpu: health.cpu,
          ram: health.ram
        }].slice(-20); // Keep last 20 points
        return newHistory;
      });
      setError(null);
    } catch (err) {
      setError('Backend unreachable. Is the server running?');
    }
  };

  const handleKill = async (target: string | number) => {
    try {
      const res = await fetch('http://localhost:8765/system/processes/kill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target })
      });
      if (!res.ok) {
        const errorData = await res.json();
        alert(`Failed to kill: ${errorData.detail}`);
      } else {
        // Refresh immediately
        fetchData();
      }
    } catch (err) {
      alert('Error connecting to backend.');
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="dashboard-error">
        <AlertCircle size={48} color="#ef4444" />
        <p>{error}</p>
      </div>
    );
  }

  if (!data) return <div className="loading">Initializing Dashboard...</div>;

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-title">
          <Activity color="#38bdf8" />
          <h1>SYSTEM COMMAND CENTER</h1>
        </div>
        <div className="status-badge">LIVE TELEMETRY</div>
      </header>

      {/* Top Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon"><Cpu size={20} /></div>
          <div className="metric-info">
            <span className="label">CPU USAGE</span>
            <span className="value">{data.cpu.toFixed(1)}%</span>
          </div>
          <div className="progress-bar">
            <div className="fill" style={{ width: `${data.cpu}%`, backgroundColor: data.cpu > 80 ? '#ef4444' : '#38bdf8' }}></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon"><Database size={20} /></div>
          <div className="metric-info">
            <span className="label">RAM USAGE</span>
            <span className="value">{data.ram.toFixed(1)}%</span>
          </div>
          <div className="progress-bar">
            <div className="fill" style={{ width: `${data.ram}%`, backgroundColor: data.ram > 80 ? '#ef4444' : '#38bdf8' }}></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon"><HardDrive size={20} /></div>
          <div className="metric-info">
            <span className="label">DISK SPACE</span>
            <span className="value">{data.disk.toFixed(1)}%</span>
          </div>
          <div className="progress-bar">
            <div className="fill" style={{ width: `${data.disk}%` }}></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon"><BatteryIcon size={20} /></div>
          <div className="metric-info">
            <span className="label">BATTERY</span>
            <span className="value">{data.battery ? `${data.battery.percent}%` : 'N/A'}</span>
          </div>
          <div className="progress-bar">
            <div className="fill" style={{ 
              width: `${data.battery?.percent || 0}%`,
              backgroundColor: data.battery?.power_plugged ? '#10b981' : (data.battery?.percent && data.battery.percent < 20 ? '#ef4444' : '#38bdf8')
            }}></div>
          </div>
        </div>
      </div>

      <div className="dashboard-main">
        {/* Real-time Chart */}
        <div className="chart-section">
          <h3>RESOURCE HISTORY</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
                <YAxis domain={[0, 100]} stroke="#64748b" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="cpu" stroke="#38bdf8" fillOpacity={1} fill="url(#colorCpu)" />
                <Area type="monotone" dataKey="ram" stroke="#8b5cf6" fillOpacity={0} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Process List */}
        <div className="process-section">
          <div className="process-header">
            <h3>ACTIVE PROCESSES</h3>
            <span className="count">{data.processes?.length || 0} RUNNING</span>
          </div>
          <div className="process-table-container">
            <table className="process-table">
              <thead>
                <tr>
                  <th>NAME</th>
                  <th>CPU</th>
                  <th>MEM</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {data.processes?.map(proc => (
                  <tr key={proc.pid}>
                    <td className="proc-name">{proc.name}</td>
                    <td>{proc.cpu_percent.toFixed(1)}%</td>
                    <td>{proc.memory_percent.toFixed(1)}%</td>
                    <td>
                      <button 
                        className="kill-btn" 
                        onClick={() => handleKill(proc.pid)}
                        title={`Terminate ${proc.name}`}
                      >
                        <XCircle size={14} />
                        KILL
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardView;
