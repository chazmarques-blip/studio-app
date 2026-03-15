import { useState, useEffect } from 'react';
import { X, Zap, Star, GraduationCap, Briefcase, Award, Brain, Target, Sparkles, MessageCircle, Lightbulb, ChevronDown, ChevronUp, Crown, Bot } from 'lucide-react';
import { getAgentAvatar } from '../data/agentAvatars';

const TYPE_LABELS = {
  sales: 'Vendas', support: 'Suporte', scheduling: 'Agenda',
  sac: 'SAC', onboarding: 'Onboarding', personal: 'Pessoal',
};

function SkillBar({ name, level, delay }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(level), 100 + delay * 80);
    return () => clearTimeout(t);
  }, [level, delay]);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-[#999] font-medium">{name}</span>
        <span className="text-[10px] font-bold text-[#C9A84C]">{level}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-[#1A1A1A] overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#E8D48B] transition-all duration-700 ease-out"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-[#1A1A1A] rounded-xl bg-[#0A0A0A] overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2.5 text-left"
        data-testid={`section-${title.toLowerCase().replace(/\s/g, '-')}`}
      >
        <div className="h-6 w-6 rounded-lg bg-[#C9A84C]/10 flex items-center justify-center shrink-0">
          <Icon size={12} className="text-[#C9A84C]" />
        </div>
        <span className="text-[11px] font-bold text-white flex-1">{title}</span>
        {open ? <ChevronUp size={14} className="text-[#555]" /> : <ChevronDown size={14} className="text-[#555]" />}
      </button>
      {open && <div className="px-3 pb-3 pt-0">{children}</div>}
    </div>
  );
}

export default function AgentDetailsDrawer({ agent, open, onClose, onDeploy }) {
  if (!open || !agent) return null;

  const avatar = getAgentAvatar(agent.name);
  const profile = agent.profile || {};
  const bg = profile.background || {};
  const isPersonal = agent.is_personal;

  return (
    <div className="fixed inset-0 z-50" data-testid="agent-details-drawer">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/85 backdrop-blur-sm" onClick={onClose} />

      {/* Drawer */}
      <div className="absolute inset-x-0 bottom-0 max-h-[92vh] flex flex-col rounded-t-2xl border-t border-[#1A1A1A] bg-[#0D0D0D] animate-in slide-in-from-bottom duration-300">
        {/* Drag handle */}
        <div className="flex justify-center pt-2 pb-1 shrink-0">
          <div className="w-10 h-1 rounded-full bg-[#333]" />
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          data-testid="close-agent-details"
          className="absolute right-3 top-3 z-10 h-7 w-7 rounded-full bg-[#1A1A1A] border border-[#2A2A2A] flex items-center justify-center text-[#666] hover:text-white hover:border-[#C9A84C]/30 transition-all"
        >
          <X size={14} />
        </button>

        {/* Scrollable Content */}
        <div className="overflow-y-auto flex-1 overscroll-contain px-4 pb-24">
          {/* Hero Section */}
          <div className="flex flex-col items-center text-center pt-2 pb-4">
            <div className="relative mb-3">
              <div className="h-20 w-20 rounded-2xl overflow-hidden ring-2 ring-[#C9A84C]/30 shadow-[0_0_30px_rgba(201,168,76,0.1)]">
                {avatar
                  ? <img src={avatar} alt={agent.name} className="h-full w-full object-cover" />
                  : <div className="h-full w-full bg-[#C9A84C]/10 flex items-center justify-center"><Bot size={32} className="text-[#C9A84C]/50" /></div>}
              </div>
              {agent.rating && (
                <div className="absolute -bottom-1 -right-1 flex items-center gap-0.5 bg-[#0D0D0D] border border-[#C9A84C]/30 rounded-full px-1.5 py-0.5">
                  <Star size={8} className="text-[#C9A84C] fill-[#C9A84C]" />
                  <span className="text-[8px] font-bold text-[#C9A84C]">{agent.rating}</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-1.5 mb-1">
              <h2 className="text-base font-bold text-white">{agent.name}</h2>
              {isPersonal && <Crown size={14} className="text-[#C9A84C]" />}
            </div>
            {profile.full_title && (
              <p className="text-[10px] text-[#C9A84C]/80 font-medium mb-1.5 max-w-[280px]">{profile.full_title}</p>
            )}
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-[#C9A84C]/10 border border-[#C9A84C]/20 px-2 py-0.5 text-[8px] font-bold text-[#C9A84C] uppercase tracking-wider">
                {TYPE_LABELS[agent.type] || agent.type}
              </span>
              {agent.category && agent.category !== 'general' && (
                <span className="rounded-full bg-[#1A1A1A] border border-[#2A2A2A] px-2 py-0.5 text-[8px] font-medium text-[#777] capitalize">
                  {agent.category}
                </span>
              )}
            </div>
          </div>

          <div className="space-y-2">
            {/* Mentality */}
            {profile.mentality && (
              <Section icon={Brain} title="Mentalidade" defaultOpen={true}>
                <p className="text-[10px] text-[#999] leading-relaxed">{profile.mentality}</p>
              </Section>
            )}

            {/* Skills */}
            {profile.skills?.length > 0 && (
              <Section icon={Target} title="Habilidades" defaultOpen={true}>
                <div className="space-y-2.5">
                  {profile.skills.map((s, i) => (
                    <SkillBar key={s.name} name={s.name} level={s.level} delay={i} />
                  ))}
                </div>
              </Section>
            )}

            {/* Background */}
            {bg.education && (
              <Section icon={GraduationCap} title="Background" defaultOpen={false}>
                <div className="space-y-3">
                  {bg.education && (
                    <div>
                      <div className="flex items-center gap-1.5 mb-1">
                        <GraduationCap size={10} className="text-[#C9A84C]/60" />
                        <span className="text-[9px] font-bold text-[#777] uppercase tracking-wider">Formacao</span>
                      </div>
                      <p className="text-[10px] text-[#ccc] pl-4">{bg.education}</p>
                    </div>
                  )}
                  {bg.experience?.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1.5 mb-1">
                        <Briefcase size={10} className="text-[#C9A84C]/60" />
                        <span className="text-[9px] font-bold text-[#777] uppercase tracking-wider">Experiencia</span>
                      </div>
                      <div className="pl-4 space-y-1">
                        {bg.experience.map((e, i) => (
                          <p key={i} className="text-[10px] text-[#999] leading-snug">{e}</p>
                        ))}
                      </div>
                    </div>
                  )}
                  {bg.certifications?.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1.5 mb-1">
                        <Award size={10} className="text-[#C9A84C]/60" />
                        <span className="text-[9px] font-bold text-[#777] uppercase tracking-wider">Certificacoes</span>
                      </div>
                      <div className="pl-4 flex flex-wrap gap-1">
                        {bg.certifications.map((c, i) => (
                          <span key={i} className="rounded-md bg-[#1A1A1A] border border-[#2A2A2A] px-1.5 py-0.5 text-[8px] text-[#999]">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Section>
            )}

            {/* Methodologies */}
            {profile.methodologies?.length > 0 && (
              <Section icon={Sparkles} title="Metodologias" defaultOpen={false}>
                <div className="flex flex-wrap gap-1.5">
                  {profile.methodologies.map((m, i) => (
                    <span key={i} className="rounded-lg bg-[#C9A84C]/5 border border-[#C9A84C]/15 px-2 py-1 text-[9px] font-medium text-[#C9A84C]/80">
                      {m}
                    </span>
                  ))}
                </div>
              </Section>
            )}

            {/* Personality Traits */}
            {profile.personality_traits?.length > 0 && (
              <Section icon={Sparkles} title="Personalidade" defaultOpen={false}>
                <div className="flex flex-wrap gap-1.5">
                  {profile.personality_traits.map((t, i) => (
                    <span key={i} className="rounded-full bg-[#1A1A1A] border border-[#2A2A2A] px-2 py-0.5 text-[9px] text-[#aaa]">
                      {t}
                    </span>
                  ))}
                </div>
              </Section>
            )}

            {/* Strengths */}
            {profile.strengths?.length > 0 && (
              <Section icon={Zap} title="Pontos Fortes" defaultOpen={false}>
                <div className="space-y-1.5">
                  {profile.strengths.map((s, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <div className="h-1 w-1 rounded-full bg-[#C9A84C] mt-1.5 shrink-0" />
                      <p className="text-[10px] text-[#999] leading-snug">{s}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            {/* Interaction Style */}
            {profile.interaction_style && (
              <Section icon={MessageCircle} title="Estilo de Interacao" defaultOpen={false}>
                <p className="text-[10px] text-[#999] leading-relaxed">{profile.interaction_style}</p>
              </Section>
            )}

            {/* Inspirations */}
            {profile.inspirations?.length > 0 && (
              <Section icon={Lightbulb} title="Inspiracoes" defaultOpen={false}>
                <div className="space-y-1">
                  {profile.inspirations.map((ins, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="h-4 w-4 rounded-full bg-[#C9A84C]/10 flex items-center justify-center shrink-0">
                        <span className="text-[7px] font-bold text-[#C9A84C]">{i + 1}</span>
                      </div>
                      <p className="text-[10px] text-[#999]">{ins}</p>
                    </div>
                  ))}
                </div>
              </Section>
            )}
          </div>
        </div>

        {/* Sticky Deploy Footer */}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-[#0D0D0D] via-[#0D0D0D] to-transparent pt-6 pb-4 px-4">
          <button
            data-testid={`deploy-modal-${agent.name}`}
            onClick={() => { onDeploy(agent); onClose(); }}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#B89A40] py-3 text-sm font-bold text-[#0A0A0A] transition-all hover:shadow-[0_0_24px_rgba(201,168,76,0.2)] active:scale-[0.98]"
          >
            <Zap size={16} />
            Deploy {agent.name}
          </button>
        </div>
      </div>
    </div>
  );
}
