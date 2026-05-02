import { HashRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { MessageSquare, LayoutDashboard, Settings, User } from 'lucide-react';
import ChatView from './ChatView';
import DashboardView from './DashboardView';
import './index.css';

function SidebarDock() {
  const location = useLocation();

  return (
    <nav className="side-dock">
      <div className="dock-top">
        <Link 
          to="/" 
          className={`dock-item ${location.pathname === '/' ? 'active' : ''}`}
          title="Chat Assistant"
        >
          <MessageSquare size={24} />
        </Link>
        <Link 
          to="/dashboard" 
          className={`dock-item ${location.pathname === '/dashboard' ? 'active' : ''}`}
          title="System Dashboard"
        >
          <LayoutDashboard size={24} />
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
  return (
    <Router>
      <div className="root-layout">
        <SidebarDock />
        <div className="content-area">
          <Routes>
            <Route path="/" element={<ChatView />} />
            <Route path="/dashboard" element={<DashboardView />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
