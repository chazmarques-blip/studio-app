import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, User, Phone, Mail, Building, Target, Clock, ArrowRightLeft } from 'lucide-react';

const timeline = [
  { event: 'Lead created by AI', time: '2 hours ago', type: 'system' },
  { event: 'Moved to Qualified', time: '1 hour ago', type: 'system' },
  { event: 'Follow-up message sent', time: '30 min ago', type: 'agent' },
  { event: 'Customer replied', time: '15 min ago', type: 'customer' },
];

export default function LeadDetail() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-24">
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => navigate('/crm')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
        <h1 className="text-xl font-bold text-white">{t('crm.lead_detail')}</h1>
      </div>

      <div className="glass-card mb-4 p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-[#2196F3] to-[#1565C0]">
            <span className="text-lg font-bold text-white">M</span>
          </div>
          <div className="flex-1">
            <h2 className="text-base font-bold text-white">Maria Silva</h2>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-[#2196F3]/15 px-2 py-0.5 text-[10px] font-medium text-[#2196F3]">{t('crm.qualified')}</span>
              <div className="h-2 w-2 rounded-full bg-[#25D366]" />
              <span className="text-xs text-[#666666]">WhatsApp</span>
            </div>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-[#C9A84C] bg-[#C9A84C]/10">
            <span className="text-sm font-bold text-[#C9A84C]">85</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2 text-[#A0A0A0]"><Phone size={12} /> +55 11 98765-4321</div>
          <div className="flex items-center gap-2 text-[#A0A0A0]"><Mail size={12} /> maria@email.com</div>
          <div className="flex items-center gap-2 text-[#A0A0A0]"><Building size={12} /> Tech Solutions</div>
          <div className="flex items-center gap-2 text-[#A0A0A0]"><Target size={12} /> $2,500</div>
        </div>
      </div>

      <div className="glass-card mb-4 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#C9A84C]"><Target size={14} /> {t('crm.ai_analysis')}</h3>
        <div className="space-y-2 text-xs text-[#A0A0A0]">
          <p><span className="text-[#666666]">Reason:</span> High engagement, asked pricing questions multiple times</p>
          <p><span className="text-[#666666]">Confidence:</span></p>
          <div className="h-1.5 rounded-full bg-[#1E1E1E]"><div className="h-full w-[85%] rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]" /></div>
          <p><span className="text-[#666666]">Next Best Action:</span> <span className="text-[#C9A84C]">Send Proposal</span></p>
        </div>
      </div>

      <div className="glass-card mb-4 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#A0A0A0]"><Clock size={14} /> {t('crm.activity')}</h3>
        <div className="relative ml-3 border-l border-[#2A2A2A] pl-4">
          {timeline.map((ev, i) => (
            <div key={i} className="relative mb-4 last:mb-0">
              <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ev.type === 'customer' ? '#25D366' : ev.type === 'agent' ? '#C9A84C' : '#2196F3' }} />
              <p className="text-sm text-white">{ev.event}</p>
              <p className="text-xs text-[#666666]">{ev.time}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button className="btn-gold rounded-lg py-2.5 text-xs">{t('crm.move_stage')}</button>
        <button className="btn-gold-outline rounded-lg py-2.5 text-xs">{t('crm.assign')}</button>
        <button className="rounded-lg border border-[#4CAF50]/30 bg-[#4CAF50]/10 py-2.5 text-xs text-[#4CAF50]">{t('crm.mark_won')}</button>
        <button className="rounded-lg border border-red-500/30 bg-red-500/10 py-2.5 text-xs text-red-400">{t('crm.mark_lost')}</button>
      </div>
    </div>
  );
}
