import { useState, useEffect } from 'react';
import { 
  Activity, 
  Cpu, 
  Database, 
  Zap, 
  HardDrive, 
  RefreshCcw,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

interface HealthData {
  cpu: number;
  ram: number;
  disk: number;
  battery: {
    percent: number;
    power_plugged: boolean;
  } | null;
}

function DashboardView() {
  const [data, setData] = useState<HealthData | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const res = await fetch('http://localhost:8765/system/health');
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
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch health:', err);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <RefreshCcw className="animate-spin" size={48} color="#38bdf8" />
        <p>GATHERING SYSTEM TELEMETRY...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="title-area">
          <Activity color="#38bdf8" size={24} />
          <h1>SYSTEM COMMAND CENTER</h1>
        </div>
        <div className="status-badge">
          <ShieldCheck size={16} color="#10b981" />
          SYSTEM SECURE
        </div>
      </header>

      <div className="stats-grid">
        <StatCard 
          icon={<Cpu size={20} />} 
          label="CPU USAGE" 
          value={`${data?.cpu.toFixed(1)}%`} 
          color="#38bdf8"
          trend="OPTIMAL"
        />
        <StatCard 
          icon={<Database size={20} />} 
          label="MEMORY" 
          value={`${data?.ram.toFixed(1)}%`} 
          color="#a78bfa"
          trend="STABLE"
        />
        <StatCard 
          icon={<HardDrive size={20} />} 
          label="DISK STORAGE" 
          value={`${data?.disk.toFixed(1)}%`} 
          color="#f472b6"
          trend="HEALTHY"
        />
        <StatCard 
          icon={<Zap size={20} />} 
          label="POWER" 
          value={data?.battery ? `${data.battery.percent}%` : 'A/C'} 
          color="#fbbf24"
          trend={data?.battery?.power_plugged ? 'CHARGING' : 'BATTERY'}
        />
      </div>

      <div className="charts-area">
        <div className="chart-card">
          <h3>REAL-TIME TELEMETRY (CPU & RAM)</h3>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorRam" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a78bfa" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a78bfa" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="cpu" stroke="#38bdf8" fillOpacity={1} fill="url(#colorCpu)" strokeWidth={2} />
                <Area type="monotone" dataKey="ram" stroke="#a78bfa" fillOpacity={1} fill="url(#colorRam)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="process-mini-list">
          <h3>ACTIVE SECURITY POLICIES</h3>
          <div className="policy-item">
            <ShieldCheck size={14} color="#10b981" />
            <span>ENCRYPTED SOCKET CHANNEL</span>
          </div>
          <div className="policy-item">
            <ShieldCheck size={14} color="#10b981" />
            <span>LOCAL EXECUTION GATEWAY</span>
          </div>
          <div className="policy-item">
            <ShieldCheck size={14} color="#10b981" />
            <span>IDENTITY PERSISTENCE SYNC</span>
          </div>
          <div className="warning-panel">
            <AlertTriangle size={20} color="#fbbf24" />
            <div>
              <strong>SYSTEM NOTICE</strong>
              <p>Hardware acceleration is enabled for maximum assistant responsiveness.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color, trend }: any) {
  return (
    <div className="stat-card">
      <div className="stat-header">
        <div className="stat-icon" style={{ color }}>{icon}</div>
        <span className="stat-label">{label}</span>
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-trend" style={{ color: '#64748b' }}>{trend}</div>
    </div>
  );
}

export default DashboardView;
