import React from 'react';
import { useTranslation } from 'react-i18next';
import { X, Building2, Briefcase, User, Loader2, Image, Globe, MessageSquare } from 'lucide-react';
import { resolveImageUrl } from '../../utils/resolveImageUrl';

/**
 * CompanyModal — Create/Edit company modal.
 * Extracted from PipelineView to reduce file size.
 */
export function CompanyModal({
  editingCompanyId, newCompany, setNewCompany, logoUploading,
  cancelCompanyForm, addCompany, saveEditCompany, uploadCompanyLogo, logoInputRef,
}) {
  const { t } = useTranslation();

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" onClick={cancelCompanyForm}>
      <div data-testid="company-modal" className="w-full max-w-md rounded-2xl border border-[#8B5CF6]/20 bg-[#0D0D0D] p-5 space-y-3" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <p className="text-sm text-white font-semibold">{editingCompanyId ? t('studio.edit_company') : t('studio.new_company')}</p>
          <button onClick={cancelCompanyForm} className="p-1 rounded hover:bg-[#1A1A1A]"><X size={16} className="text-[#999]" /></button>
        </div>
        {/* Profile Type Selector */}
        <div className="flex gap-1.5">
          {[
            { id: 'company', label: 'Empresa', icon: Building2 },
            { id: 'professional', label: 'Profissional', icon: Briefcase },
            { id: 'personal', label: 'Pessoal', icon: User },
          ].map(pt => (
            <button key={pt.id} data-testid={`profile-type-${pt.id}`}
              onClick={() => setNewCompany(p => ({ ...p, profile_type: pt.id }))}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border text-[10px] font-semibold transition ${newCompany.profile_type === pt.id
                ? 'border-[#8B5CF6]/50 bg-[#8B5CF6]/10 text-[#8B5CF6]'
                : 'border-[#1E1E1E] text-[#999] hover:text-[#888] hover:border-[#333]'}`}>
              <pt.icon size={12} />
              {pt.label}
            </button>
          ))}
        </div>
        {/* Logo / Photo Upload */}
        <input ref={logoInputRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp,image/svg+xml"
          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
          onChange={e => { uploadCompanyLogo(e.target.files); e.target.value = ''; }} />
        <div className="flex items-center gap-3">
          <button data-testid="company-logo-upload" type="button" onClick={() => logoInputRef.current?.click()}
            disabled={logoUploading}
            className={`relative shrink-0 h-14 w-14 rounded-xl border-2 border-dashed flex items-center justify-center overflow-hidden transition ${newCompany.logo_url ? 'border-[#8B5CF6]/40' : 'border-[#2A2A2A] hover:border-[#8B5CF6]/30'}`}>
            {newCompany.logo_url ? (
              <img src={resolveImageUrl(newCompany.logo_url)} alt="Logo" loading="lazy" decoding="async" className="h-full w-full object-cover" />
            ) : logoUploading ? (
              <Loader2 size={16} className="animate-spin text-[#8B5CF6]" />
            ) : (
              <Image size={18} className="text-[#888]" />
            )}
          </button>
          <div className="flex-1">
            <p className="text-[10px] text-white font-medium">{newCompany.profile_type === 'personal' ? 'Foto' : newCompany.profile_type === 'professional' ? 'Foto / Logo' : 'Logo'}</p>
            <p className="text-[11px] text-[#999]">{newCompany.logo_url ? t('studio.click_to_change') || 'Click to change' : t('studio.upload_logo')}</p>
            {newCompany.logo_url && (
              <button onClick={() => setNewCompany(p => ({ ...p, logo_url: '' }))} className="text-[11px] text-red-400 hover:text-red-300 mt-0.5">{t('studio.remove')}</button>
            )}
          </div>
        </div>
        <div>
          <label className="text-xs text-[#999] uppercase mb-1 block">{newCompany.profile_type === 'personal' ? 'Nome' : newCompany.profile_type === 'professional' ? 'Nome Profissional' : t('studio.company_name_label')} *</label>
          <input data-testid="new-company-name" value={newCompany.name} onChange={e => setNewCompany(p => ({ ...p, name: e.target.value }))}
            placeholder="E.g.: StudioX, My Company..."
            className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#8B5CF6]/30" />
        </div>
        <div className="grid grid-cols-[1fr_auto] gap-3">
          <div>
            <label className="text-xs text-[#999] uppercase mb-1 block">{t('studio.company_phone')}</label>
            <input data-testid="new-company-phone" value={newCompany.phone} onChange={e => setNewCompany(p => ({ ...p, phone: e.target.value }))}
              placeholder="+1 555 123-4567"
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#8B5CF6]/30" />
          </div>
          <div className="flex items-end pb-0.5">
            <button data-testid="new-company-whatsapp-toggle" onClick={() => setNewCompany(p => ({ ...p, is_whatsapp: !p.is_whatsapp }))}
              className={`flex items-center gap-1 rounded-lg border px-3 py-2 text-[10px] font-medium transition ${newCompany.is_whatsapp ? 'border-[#25D366]/40 bg-[#25D366]/10 text-[#25D366]' : 'border-[#1E1E1E] text-[#999]'}`}>
              <MessageSquare size={10} /> WhatsApp
            </button>
          </div>
        </div>
        <div>
          <label className="text-xs text-[#999] uppercase mb-1 flex items-center gap-1">
            <Globe size={9} /> {t('studio.company_website')}
          </label>
          <input data-testid="new-company-website" value={newCompany.website_url} onChange={e => setNewCompany(p => ({ ...p, website_url: e.target.value }))}
            placeholder="https://www.yourcompany.com"
            className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#8B5CF6]/30" />
        </div>
        <div>
          <label className="text-xs text-[#999] uppercase mb-1 block">{t('studio.product_service') || 'Produto / Servico'}</label>
          <textarea data-testid="new-company-product" value={newCompany.product_description} onChange={e => setNewCompany(p => ({ ...p, product_description: e.target.value }))}
            placeholder="Ex: Plataforma de agentes IA para atendimento ao cliente, Loja de roupas femininas..."
            rows={2}
            className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#8B5CF6]/30 resize-none" />
        </div>
        {/* Social Links */}
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-[11px] text-[#999] uppercase mb-1 flex items-center gap-1"><span style={{color:'#1877F2'}}>f</span> Facebook</label>
            <input data-testid="new-company-facebook" value={newCompany.facebook_url || ''} onChange={e => setNewCompany(p => ({ ...p, facebook_url: e.target.value }))}
              placeholder="facebook.com/..."
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#1877F2]/30" />
          </div>
          <div>
            <label className="text-[11px] text-[#999] uppercase mb-1 flex items-center gap-1"><span style={{color:'#E4405F'}}>@</span> Instagram</label>
            <input data-testid="new-company-instagram" value={newCompany.instagram_url || ''} onChange={e => setNewCompany(p => ({ ...p, instagram_url: e.target.value }))}
              placeholder="instagram.com/..."
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#E4405F]/30" />
          </div>
          <div>
            <label className="text-[11px] text-[#999] uppercase mb-1 flex items-center gap-1"><span style={{color:'#fff'}}>T</span> TikTok</label>
            <input data-testid="new-company-tiktok" value={newCompany.tiktok_url || ''} onChange={e => setNewCompany(p => ({ ...p, tiktok_url: e.target.value }))}
              placeholder="tiktok.com/@..."
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#fff]/20" />
          </div>
        </div>
        
        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* PROJECT DEFAULTS SECTION (NEW) */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        <div className="border-t border-[#1E1E1E] pt-3 mt-2">
          <p className="text-xs text-white font-semibold mb-2">⚙️ Padrões de Projeto</p>
          <p className="text-[10px] text-[#999] mb-3">Configure valores padrão que serão aplicados automaticamente ao criar novos projetos</p>
          
          {/* Default Visual Style */}
          <div className="mb-2">
            <label className="text-[10px] text-[#999] uppercase mb-1 block">Estilo Visual Padrão</label>
            <div className="grid grid-cols-3 gap-1">
              {[
                { id: 'pixar_3d', label: 'Pixar 3D' },
                { id: 'cartoon_2d', label: 'Cartoon 2D' },
                { id: 'realista', label: 'Realista' },
              ].map(style => (
                <button key={style.id} type="button"
                  onClick={() => setNewCompany(p => ({ ...p, default_visual_style: style.id, default_animation_sub: style.id }))}
                  className={`px-2 py-1.5 rounded border text-[9px] transition ${
                    newCompany.default_visual_style === style.id
                      ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                      : 'border-[#1E1E1E] text-[#999] hover:border-[#333]'
                  }`}>
                  {style.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Default Target Audience */}
          <div className="mb-2">
            <label className="text-[10px] text-[#999] uppercase mb-1 block">Público-Alvo Padrão</label>
            <div className="grid grid-cols-3 gap-1">
              {[
                { id: '3-6', label: '3-6 anos' },
                { id: '6-9', label: '6-9 anos' },
                { id: '10-13', label: '10-13' },
                { id: '14-17', label: '14-17' },
                { id: '18-25', label: '18-25' },
                { id: '25+', label: '25+' },
                { id: 'all', label: 'Todas' },
              ].map(age => (
                <button key={age.id} type="button"
                  onClick={() => setNewCompany(p => ({ ...p, default_target_audience: age.id }))}
                  className={`px-2 py-1.5 rounded border text-[9px] transition ${
                    newCompany.default_target_audience === age.id
                      ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                      : 'border-[#1E1E1E] text-[#999] hover:border-[#333]'
                  }`}>
                  {age.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Default Format */}
          <div className="mb-2">
            <label className="text-[10px] text-[#999] uppercase mb-1 block">Formato Padrão</label>
            <div className="grid grid-cols-3 gap-1">
              {[
                { id: 'safe_zone', label: 'Safe Zone' },
                { id: 'dual', label: 'Dual' },
                { id: 'multi', label: 'Multi' },
              ].map(format => (
                <button key={format.id} type="button"
                  onClick={() => setNewCompany(p => ({ ...p, default_format_strategy: format.id }))}
                  className={`px-2 py-1.5 rounded border text-[9px] transition ${
                    newCompany.default_format_strategy === format.id
                      ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                      : 'border-[#1E1E1E] text-[#999] hover:border-[#333]'
                  }`}>
                  {format.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Default Video Engine */}
          <div className="mb-2">
            <label className="text-[10px] text-[#999] uppercase mb-1 block">Engine de Vídeo Padrão</label>
            <div className="grid grid-cols-2 gap-1">
              {[
                { id: 'sora', label: 'Sora 2 (12s)' },
                { id: 'kling', label: 'Kling AI (5min)' },
              ].map(engine => (
                <button key={engine.id} type="button"
                  onClick={() => setNewCompany(p => ({ ...p, default_video_engine: engine.id }))}
                  className={`px-2 py-1.5 rounded border text-[9px] transition ${
                    newCompany.default_video_engine === engine.id
                      ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                      : 'border-[#1E1E1E] text-[#999] hover:border-[#333]'
                  }`}>
                  {engine.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Default Duration (only for Kling) */}
          {newCompany.default_video_engine === 'kling' && (
            <div className="mb-2">
              <label className="text-[10px] text-[#999] uppercase mb-1 block">Duração Padrão (minutos)</label>
              <div className="grid grid-cols-5 gap-1">
                {[5, 10, 15, 20, 25].map(duration => (
                  <button key={duration} type="button"
                    onClick={() => setNewCompany(p => ({ ...p, default_target_duration: duration }))}
                    className={`px-2 py-1.5 rounded border text-[9px] transition ${
                      newCompany.default_target_duration === duration
                        ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                        : 'border-[#1E1E1E] text-[#999] hover:border-[#333]'
                    }`}>
                    {duration}min
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <p className="text-[9px] text-[#666] italic mt-2">
            💡 Pasta de personagens padrão será definida após selecionar a empresa no projeto
          </p>
        </div>

        <div className="flex gap-2 pt-2">
          <button onClick={cancelCompanyForm}
            className="flex-1 rounded-lg border border-[#1E1E1E] py-2 text-xs text-[#888] hover:text-white transition">
            {t('studio.cancel')}
          </button>
          <button data-testid="save-company-btn" onClick={editingCompanyId ? saveEditCompany : addCompany} disabled={!newCompany.name.trim()}
            className="flex-1 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#D4B85A] py-2 text-xs font-bold text-black hover:opacity-90 disabled:opacity-30 transition">
            {editingCompanyId ? t('studio.update_company') : t('studio.save_company')}
          </button>
        </div>
      </div>
    </div>
  );
}
