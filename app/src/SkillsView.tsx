import { useState } from 'react';
import { 
  Puzzle, 
  CheckCircle2, 
  Circle, 
  Search, 
  Globe, 
  Smartphone, 
  FileText, 
  Music,
  Zap,
  Info,
  ShieldCheck
} from 'lucide-react';

interface Skill {
  id: string;
  name: string;
  description: string;
  icon: any;
  enabled: boolean;
  category: string;
}

const INITIAL_SKILLS: Skill[] = [
  { id: 'whatsapp', name: 'WhatsApp Pro', description: 'Advanced messaging, contact lookup, and media sending.', icon: <Smartphone size={20} />, enabled: true, category: 'Communication' },
  { id: 'browser', name: 'Web Navigator', description: 'Deep browser automation, form filling, and research.', icon: <Globe size={20} />, enabled: true, category: 'Web' },
  { id: 'file_master', name: 'File Master', description: 'Complex file operations, zip/unzip, and organization.', icon: <FileText size={20} />, enabled: false, category: 'System' },
  { id: 'spotify', name: 'Spotify Control', description: 'Search tracks, manage playlists, and playback control.', icon: <Music size={20} />, enabled: false, category: 'Media' },
  { id: 'guardian', name: 'System Guardian', description: 'Background health monitoring and proactive alerts.', icon: <Zap size={20} />, enabled: true, category: 'Security' },
  { id: 'security', name: 'Secure Sandbox', description: 'Blocks all raw terminal and shell commands for total system safety.', icon: <ShieldCheck size={20} />, enabled: true, category: 'Security' },
];

function SkillsView() {
  const [skills, setSkills] = useState<Skill[]>(INITIAL_SKILLS);
  const [search, setSearch] = useState('');

  const toggleSkill = (id: string) => {
    setSkills(prev => prev.map(s => 
      s.id === id ? { ...s, enabled: !s.enabled } : s
    ));
  };

  const filteredSkills = skills.filter(s => 
    s.name.toLowerCase().includes(search.toLowerCase()) || 
    s.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="skills-container">
      <header className="skills-header">
        <div className="title-area">
          <Puzzle color="#38bdf8" size={24} />
          <h1>SKILLS MARKETPLACE</h1>
        </div>
        <div className="search-bar">
          <Search size={16} color="#64748b" />
          <input 
            placeholder="Search for new capabilities..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </header>

      <div className="skills-info">
        <Info size={16} />
        <span>Enabled skills are automatically injected into the AI's reasoning engine.</span>
      </div>

      <div className="skills-grid">
        {filteredSkills.map(skill => (
          <div key={skill.id} className={`skill-card ${skill.enabled ? 'active' : ''}`}>
            <div className="skill-icon-box">
              {skill.icon}
            </div>
            <div className="skill-content">
              <h3>{skill.name}</h3>
              <p>{skill.description}</p>
              <div className="skill-footer">
                <span className="skill-cat">{skill.category}</span>
                <button 
                  className={`skill-toggle ${skill.enabled ? 'enabled' : ''}`}
                  onClick={() => toggleSkill(skill.id)}
                >
                  {skill.enabled ? <CheckCircle2 size={16} /> : <Circle size={16} />}
                  {skill.enabled ? 'ENABLED' : 'INSTALL'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SkillsView;
