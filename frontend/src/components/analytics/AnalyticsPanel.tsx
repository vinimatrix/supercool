import React from 'react';
import { BarChart3, TrendingUp, Users, Eye, Activity } from 'lucide-react';

export const AnalyticsPanel: React.FC = () => {
  return (
    <div className="flex flex-col h-full space-y-6 p-4">
      <div className="flex items-center gap-2">
        <BarChart3 className="w-3 h-3 text-[var(--color-accent)]" />
        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Advanced Analytics</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Avg Retention', value: '64%', icon: TrendingUp, color: 'text-emerald-400' },
          { label: 'Total Views', value: '1.2M', icon: Eye, color: 'text-blue-400' },
          { label: 'Conversion', value: '12.4%', icon: Users, color: 'text-purple-400' },
          { label: 'Drop-off', value: '22%', icon: Activity, color: 'text-red-400' },
        ].map((stat, i) => (
          <div key={i} className="p-3 rounded-sm border border-[var(--color-border)] bg-black/40">
            <div className="flex items-center gap-2 mb-2 opacity-50">
              <stat.icon className="w-3 h-3" />
              <span className="text-[9px] mono text-gray-500 uppercase">{stat.label}</span>
            </div>
            <div className={`text-xl font-bold mono ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="flex-1 rounded-sm border border-[var(--color-border)] bg-black/60 p-4 flex flex-col items-center justify-center opacity-40">
        <BarChart3 className="w-8 h-8 text-gray-700 mb-2" />
        <p className="text-[10px] mono text-gray-500">METRICS DATA STREAM OFFLINE</p>
        <p className="text-[8px] mono text-gray-600 mt-1">Connect YouTube API for real-time tracking</p>
      </div>
    </div>
  );
};
