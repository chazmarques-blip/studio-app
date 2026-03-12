import { BarChart3, TrendingUp } from 'lucide-react';

export default function Analytics() {
  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Analytics</h1>
        <button className="rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-1.5 text-xs text-[#A0A0A0]">
          Last 7 Days
        </button>
      </div>

      {/* Stats */}
      <div className="mb-6 grid grid-cols-2 gap-3">
        {[
          { label: 'Total Messages', value: '0', color: '#C9A84C' },
          { label: 'Resolution Rate', value: '0%', color: '#4CAF50' },
          { label: 'Avg Response', value: '0s', color: '#2196F3' },
          { label: 'Total Cost', value: '$0.00', color: '#FF9800' },
        ].map((s, i) => (
          <div key={i} className="glass-card p-4">
            <p className="text-lg font-bold text-white">{s.value}</p>
            <p className="text-xs text-[#666666]">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Chart placeholder */}
      <div data-testid="analytics-chart-placeholder" className="glass-card mb-6 p-6">
        <h3 className="mb-4 text-sm font-semibold text-[#A0A0A0]">Messages Over Time</h3>
        <div className="flex h-40 items-center justify-center">
          <div className="text-center">
            <BarChart3 size={32} className="mx-auto mb-2 text-[#2A2A2A]" />
            <p className="text-xs text-[#666666]">Start receiving messages to see analytics</p>
          </div>
        </div>
      </div>

      {/* Agent Performance placeholder */}
      <div className="glass-card p-6">
        <h3 className="mb-4 text-sm font-semibold text-[#A0A0A0]">Agent Performance</h3>
        <div className="flex h-24 items-center justify-center">
          <p className="text-xs text-[#666666]">No agent data yet</p>
        </div>
      </div>
    </div>
  );
}
