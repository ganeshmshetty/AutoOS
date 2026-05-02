export interface Message {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  type?: 'browser' | 'os' | 'info' | 'plan';
  subCategory?: string;
}

export interface HealthData {
  cpu: number;
  ram: number;
  disk: number;
  battery: {
    percent: number;
    power_plugged: boolean;
  } | null;
  processes: {
    pid: number;
    name: string;
    cpu_percent: number;
    memory_percent: number;
  }[];
}
