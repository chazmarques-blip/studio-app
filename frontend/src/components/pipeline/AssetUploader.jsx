import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, X, Image, Loader2, Maximize2, Camera, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { resolveImageUrl } from '../../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function AssetUploader({ assets, onAssetsChange }) {
  const { t } = useTranslation();
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(null);
  const exactRef = useRef(null);
  const refRef = useRef(null);

  const handleUpload = async (files, type) => {
    if (!files?.length) return;
    setUploading(true);
    const newAssets = [...assets];
    for (const file of Array.from(files)) {
      if (!file.type || !file.type.startsWith('image/')) { toast.error(`"${file.name}" is not a valid image`); continue; }
      if (file.size > 10 * 1024 * 1024) { toast.error(`"${file.name}" exceeds 10MB`); continue; }
      try {
        const form = new FormData();
        form.append('file', file);
        form.append('asset_type', type);
        const { data } = await axios.post(`${API}/campaigns/pipeline/upload`, form);
        newAssets.push({ url: data.url, filename: data.filename, type, name: file.name, preview: URL.createObjectURL(file) });
        toast.success(`${file.name} enviado com sucesso!`);
      } catch (e) {
        console.error('Upload error:', e?.response?.status, e?.response?.data, e?.message);
        const msg = e.response?.data?.detail || e.message || 'Erro de conexao';
        toast.error(`Falha ao enviar "${file.name}": ${msg}`);
      }
    }
    onAssetsChange(newAssets);
    setUploading(false);
  };

  const handleDrop = (e, type) => {
    e.preventDefault();
    setDragOver(null);
    const files = e.dataTransfer?.files;
    if (files?.length) handleUpload(files, type);
  };

  const handleDragOver = (e, type) => { e.preventDefault(); setDragOver(type); };
  const handleDragLeave = () => setDragOver(null);

  const removeAsset = (idx) => {
    onAssetsChange(assets.filter((_, i) => i !== idx));
  };

  const exacts = assets.filter(a => a.type === 'exact');
  const refs = assets.filter(a => a.type === 'reference');

  const UploadColumn = ({ type, items, inputRef, color, icon: Icon, label, testId }) => (
    <div>
      <p className="text-[8px] text-[#777] uppercase tracking-wider mb-1">{label}</p>
      <input ref={inputRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp" multiple
        style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
        onChange={e => { handleUpload(e.target.files, type); e.target.value = ''; }} />
      {items.length > 0 ? (
        <div className="flex gap-1.5 flex-wrap items-center">
          {items.map((a, i) => {
            const imgSrc = a.preview || resolveImageUrl(a.url);
            return (
              <div key={i} className="relative group">
                <img src={imgSrc} alt=""
                  onError={(e) => { if (a.url && e.target.src !== resolveImageUrl(a.url)) { e.target.src = resolveImageUrl(a.url); } }}
                  className={`h-14 w-14 rounded-lg object-cover border ${type === 'exact' ? 'border-[#10B981]/30' : 'border-[#1E1E1E]'}`} />
                <button onClick={() => removeAsset(assets.indexOf(a))}
                  className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  <X size={8} className="text-white" />
                </button>
              </div>
            );
          })}
          <button onClick={() => inputRef.current?.click()} disabled={uploading}
            className={`h-14 w-14 rounded-lg border border-dashed border-[#2A2A2A] flex items-center justify-center hover:border-[${color}]/40 transition disabled:opacity-40`}>
            <Upload size={10} className="text-[#777]" />
          </button>
        </div>
      ) : (
        <button data-testid={testId}
          onClick={() => inputRef.current?.click()}
          onDrop={e => handleDrop(e, type)}
          onDragOver={e => handleDragOver(e, type)}
          onDragLeave={handleDragLeave}
          disabled={uploading}
          className={`w-full rounded-xl border border-dashed py-3 flex flex-col items-center gap-1 transition disabled:opacity-40 cursor-pointer ${
            dragOver === type ? `border-[${color}] bg-[${color}]/5` : `border-[#1E1E1E] hover:border-[${color}]/30`
          }`}>
          <Icon size={14} style={{ color }} />
          <span className="text-[8px] font-medium" style={{ color }}>{label}</span>
        </button>
      )}
    </div>
  );

  return (
    <div data-testid="asset-uploader" className="space-y-3">
      <label className="text-[9px] text-[#777] uppercase tracking-wider block">{t('studio.product_images')}</label>

      <div className="grid grid-cols-2 gap-2">
        <UploadColumn type="exact" items={exacts} inputRef={exactRef} color="#10B981"
          icon={Eye} label={t('studio.exact_photos')} testId="upload-exact-btn" />
        <UploadColumn type="reference" items={refs} inputRef={refRef} color="#7CB9E8"
          icon={Image} label={t('studio.ref_photos')} testId="upload-ref-btn" />
      </div>

      {exacts.length > 0 && (
        <p className="text-[8px] text-[#10B981]/70 italic px-1">{t('studio.exact_photos_hint')}</p>
      )}

      {uploading && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-[#C9A84C]/5 border border-[#C9A84C]/20">
          <Loader2 size={12} className="animate-spin text-[#C9A84C]" />
          <span className="text-[10px] text-[#C9A84C]">{t('studio.uploading')}</span>
        </div>
      )}
    </div>
  );
}

/* ── Main PipelineView ── */

export { AssetUploader };
