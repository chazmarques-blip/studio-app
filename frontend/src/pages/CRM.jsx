import { Target, Plus } from 'lucide-react';

const stages = [
  { name: 'New', color: '#C9A84C', count: 0 },
  { name: 'Qualified', color: '#2196F3', count: 0 },
  { name: 'Proposal', color: '#9C27B0', count: 0 },
  { name: 'Won', color: '#4CAF50', count: 0 },
  { name: 'Lost', color: '#666666', count: 0 },
];

export default function CRM() {
  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">CRM Pipeline</h1>
        <button data-testid="add-lead-btn" className="btn-gold flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs">
          <Plus size={14} /> Add Lead
        </button>
      </div>

      {/* Stats bar */}
      <div className="mb-4 flex gap-3 overflow-x-auto pb-2">
        <div className="glass-card flex-shrink-0 px-4 py-2.5">
          <p className="text-xs text-[#666666]">Total Leads</p>
          <p className="text-base font-bold text-white">0</p>
        </div>
        <div className="glass-card flex-shrink-0 px-4 py-2.5">
          <p className="text-xs text-[#666666]">Pipeline Value</p>
          <p className="text-base font-bold text-white">$0</p>
        </div>
        <div className="glass-card flex-shrink-0 px-4 py-2.5">
          <p className="text-xs text-[#666666]">Conversion</p>
          <p className="text-base font-bold text-white">0%</p>
        </div>
      </div>

      {/* Kanban columns (horizontal scroll) */}
      <div className="flex gap-3 overflow-x-auto pb-4">
        {stages.map(stage => (
          <div key={stage.name} data-testid={`stage-${stage.name.toLowerCase()}`} className="w-64 flex-shrink-0">
            <div className="mb-3 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full" style={{ backgroundColor: stage.color }} />
              <span className="text-sm font-semibold text-white">{stage.name}</span>
              <span className="ml-auto rounded-full bg-[#1A1A1A] px-2 py-0.5 text-xs text-[#666666]">{stage.count}</span>
            </div>
            <div className="min-h-[200px] rounded-xl bg-[#111111] border border-[#1A1A1A] p-3">
              <div className="flex h-32 items-center justify-center">
                <p className="text-center text-xs text-[#3A3A3A]">No leads in this stage</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
