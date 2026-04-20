import { useState } from 'react';
import {
  Home, Users, Bot, Settings, BookOpen, Video, Layers, Plus, Search,
  MoreHorizontal, Folder, ChevronLeft, Check, Zap,
} from 'lucide-react';

// Fake projects used to demonstrate layout density + card styling
const MOCK_PROJECTS = [
  { id: 1, name: 'Lila e seus Brinquedos Fantásticos', type: 'book', thumb: 'https://studiox-storage.emergentagent.com/sample-covers/lila.png', status: 'PDF pronto', when: 'Hoje' },
  { id: 2, name: 'Abraão, Isaque e o Cordeiro', type: 'book', thumb: 'https://studiox-storage.emergentagent.com/sample-covers/abraao.png', status: 'PDF pronto', when: 'Ontem' },
  { id: 3, name: 'A Raposinha Generosa', type: 'book', thumb: 'https://studiox-storage.emergentagent.com/sample-covers/raposa.png', status: 'PDF pronto', when: 'Ontem' },
  { id: 4, name: 'Manual do Pulmeranea', type: 'book', thumb: null, status: 'Preflight OK', when: '2 dias' },
  { id: 5, name: 'Aventura no Bosque — Piloto', type: 'video', thumb: null, status: '6 cenas · 3 min', when: '3 dias' },
  { id: 6, name: 'Saga do Relógio Antigo', type: 'hybrid', thumb: null, status: 'Híbrido · Em produção', when: '4 dias' },
  { id: 7, name: 'O Oráculo de Ferro', type: 'video', thumb: null, status: '12 cenas · 8 min', when: 'semana' },
  { id: 8, name: 'Pequenos Exploradores do Mar', type: 'book', thumb: null, status: 'Ilustrações 80%', when: 'semana' },
];

const TYPE_META = {
  video: { label: 'Vídeo', Icon: Video, dark: 'text-blue-400', light: 'text-blue-600' },
  book: { label: 'Livro', Icon: BookOpen, dark: 'text-emerald-400', light: 'text-emerald-600' },
  hybrid: { label: 'Híbrido', Icon: Layers, dark: 'text-amber-400', light: 'text-amber-600' },
};

// ---------- DARK MOCKUP (Archetype: Swiss/Linear) ----------
function DarkMockup() {
  const [active, setActive] = useState('projetos');
  const [filter, setFilter] = useState('all');

  const items = filter === 'all' ? MOCK_PROJECTS : MOCK_PROJECTS.filter(p => p.type === filter);
  return (
    <div className="rounded-2xl overflow-hidden border border-[#262626] shadow-[0_20px_60px_rgba(0,0,0,0.5)]">
      <div className="flex h-[680px] bg-[#0A0A0A] text-[#F5F5F5]" style={{ fontFamily: "'Outfit', system-ui" }}>
        {/* SIDEBAR */}
        <aside className="w-60 shrink-0 bg-[#121212] border-r border-[#262626] flex flex-col">
          <div className="h-14 px-5 flex items-center gap-2 border-b border-[#262626]">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center text-xs font-black text-black">X</div>
            <span className="text-[15px] font-semibold tracking-tight">StudioX</span>
          </div>
          <nav className="flex-1 px-3 py-4 space-y-0.5">
            {[
              { key: 'projetos', label: 'Projetos', Icon: Home, count: 66 },
              { key: 'personagens', label: 'Personagens', Icon: Users, count: 391 },
              { key: 'agentes', label: 'Agentes', Icon: Bot, count: null },
              { key: 'config', label: 'Configurações', Icon: Settings, count: null },
            ].map(({ key, label, Icon, count }) => {
              const isActive = active === key;
              return (
                <button
                  key={key}
                  onClick={() => setActive(key)}
                  className={`relative w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition ${
                    isActive ? 'bg-white/10 text-white' : 'text-[#A3A3A3] hover:bg-white/5 hover:text-white'
                  }`}
                >
                  {isActive && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-amber-500" />}
                  <Icon size={16} strokeWidth={1.75} />
                  <span className="flex-1 text-left">{label}</span>
                  {count != null && (
                    <span className={`text-[10px] font-mono ${isActive ? 'text-white/70' : 'text-[#737373]'}`}>{count}</span>
                  )}
                </button>
              );
            })}
          </nav>
          <div className="px-3 pb-3 border-t border-[#262626] pt-3">
            <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-[11px] font-bold text-black">TU</div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-medium text-white truncate">Test User</p>
                <p className="text-[10px] text-[#737373] flex items-center gap-1 font-mono"><Zap size={9} className="text-amber-500" />9,987 / 10k</p>
              </div>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="h-14 px-8 flex items-center justify-between border-b border-[#262626]">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-semibold tracking-tight">Projetos</h1>
              <span className="text-xs font-mono text-[#737373]">66</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
                <input
                  placeholder="Buscar..."
                  className="w-64 h-9 pl-9 pr-3 rounded-lg bg-[#171717] border border-[#262626] text-xs text-white placeholder:text-[#737373] outline-none focus:border-[#525252] transition"
                />
              </div>
              <button className="h-9 px-4 rounded-lg bg-white text-black text-xs font-semibold hover:bg-white/90 transition flex items-center gap-1.5">
                <Plus size={14} strokeWidth={2.5} /> Novo Projeto
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-auto px-8 py-6">
            {/* Filter pills */}
            <div className="flex items-center gap-1 mb-6" style={{ fontFamily: "'Manrope', system-ui" }}>
              {[
                { k: 'all', l: 'Todos', n: MOCK_PROJECTS.length, I: Folder },
                { k: 'video', l: 'Vídeos', n: MOCK_PROJECTS.filter(p => p.type === 'video').length, I: Video },
                { k: 'book', l: 'Livros', n: MOCK_PROJECTS.filter(p => p.type === 'book').length, I: BookOpen },
                { k: 'hybrid', l: 'Híbridos', n: MOCK_PROJECTS.filter(p => p.type === 'hybrid').length, I: Layers },
              ].map(({ k, l, n, I }) => {
                const active = filter === k;
                return (
                  <button
                    key={k}
                    onClick={() => setFilter(k)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition ${
                      active ? 'bg-white/10 text-white' : 'text-[#A3A3A3] hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <I size={11} /> {l}
                    <span className={`${active ? 'text-white/60' : 'text-[#525252]'} font-mono text-[10px]`}>{n}</span>
                  </button>
                );
              })}
            </div>

            <div className="grid grid-cols-3 gap-5" style={{ fontFamily: "'Manrope', system-ui" }}>
              {items.map((p) => {
                const meta = TYPE_META[p.type];
                return (
                  <div key={p.id} className="group rounded-xl border border-[#262626] bg-[#121212] overflow-hidden hover:border-[#525252] transition cursor-pointer">
                    <div className="aspect-video bg-gradient-to-br from-[#171717] to-[#0a0a0a] flex items-center justify-center relative overflow-hidden">
                      {p.thumb ? (
                        <img src={p.thumb} alt="" className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                      ) : (
                        <meta.Icon size={32} strokeWidth={1} className="text-[#262626]" />
                      )}
                    </div>
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <h3 className="text-[13px] font-semibold text-white leading-tight line-clamp-1">{p.name}</h3>
                        <button className="p-0.5 rounded hover:bg-white/10 opacity-0 group-hover:opacity-100 transition">
                          <MoreHorizontal size={14} className="text-[#737373]" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-[#A3A3A3]">
                        <span className={`inline-flex items-center gap-1 ${meta.dark}`}>
                          <meta.Icon size={10} /> {meta.label}
                        </span>
                        <span className="text-[#525252]">·</span>
                        <span>{p.status}</span>
                      </div>
                      <p className="text-[10px] text-[#525252] mt-1.5 font-mono uppercase tracking-wider">{p.when}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// ---------- LIGHT MOCKUP (mantendo DNA âmbar atual) ----------
function LightMockup() {
  const [active, setActive] = useState('projetos');
  const [filter, setFilter] = useState('all');
  const items = filter === 'all' ? MOCK_PROJECTS : MOCK_PROJECTS.filter(p => p.type === filter);

  return (
    <div className="rounded-2xl overflow-hidden border border-gray-200 shadow-[0_20px_60px_rgba(0,0,0,0.08)]">
      <div className="flex h-[680px] bg-white text-gray-900" style={{ fontFamily: "'Outfit', system-ui" }}>
        {/* SIDEBAR */}
        <aside className="w-60 shrink-0 bg-[#FAFAFA] border-r border-gray-200 flex flex-col">
          <div className="h-14 px-5 flex items-center gap-2 border-b border-gray-200">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center text-xs font-black text-white">X</div>
            <span className="text-[15px] font-semibold tracking-tight">StudioX</span>
          </div>
          <nav className="flex-1 px-3 py-4 space-y-0.5">
            {[
              { key: 'projetos', label: 'Projetos', Icon: Home, count: 66 },
              { key: 'personagens', label: 'Personagens', Icon: Users, count: 391 },
              { key: 'agentes', label: 'Agentes', Icon: Bot, count: null },
              { key: 'config', label: 'Configurações', Icon: Settings, count: null },
            ].map(({ key, label, Icon, count }) => {
              const isActive = active === key;
              return (
                <button
                  key={key}
                  onClick={() => setActive(key)}
                  className={`relative w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition ${
                    isActive ? 'bg-amber-50 text-amber-900' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {isActive && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-amber-500" />}
                  <Icon size={16} strokeWidth={1.75} />
                  <span className="flex-1 text-left">{label}</span>
                  {count != null && (
                    <span className={`text-[10px] font-mono ${isActive ? 'text-amber-700' : 'text-gray-400'}`}>{count}</span>
                  )}
                </button>
              );
            })}
          </nav>
          <div className="px-3 pb-3 border-t border-gray-200 pt-3">
            <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 cursor-pointer">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-[11px] font-bold text-white">TU</div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-medium text-gray-900 truncate">Test User</p>
                <p className="text-[10px] text-gray-500 flex items-center gap-1 font-mono"><Zap size={9} className="text-amber-500" />9,987 / 10k</p>
              </div>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="h-14 px-8 flex items-center justify-between border-b border-gray-200 bg-white">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-semibold tracking-tight">Projetos</h1>
              <span className="text-xs font-mono text-gray-400">66</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  placeholder="Buscar..."
                  className="w-64 h-9 pl-9 pr-3 rounded-lg bg-gray-50 border border-gray-200 text-xs text-gray-900 placeholder:text-gray-400 outline-none focus:border-amber-400 transition"
                />
              </div>
              <button className="h-9 px-4 rounded-lg bg-gray-900 text-white text-xs font-semibold hover:bg-gray-800 transition flex items-center gap-1.5">
                <Plus size={14} strokeWidth={2.5} /> Novo Projeto
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-auto px-8 py-6 bg-[#FAFAFA]">
            <div className="flex items-center gap-1 mb-6" style={{ fontFamily: "'Manrope', system-ui" }}>
              {[
                { k: 'all', l: 'Todos', n: MOCK_PROJECTS.length, I: Folder },
                { k: 'video', l: 'Vídeos', n: MOCK_PROJECTS.filter(p => p.type === 'video').length, I: Video },
                { k: 'book', l: 'Livros', n: MOCK_PROJECTS.filter(p => p.type === 'book').length, I: BookOpen },
                { k: 'hybrid', l: 'Híbridos', n: MOCK_PROJECTS.filter(p => p.type === 'hybrid').length, I: Layers },
              ].map(({ k, l, n, I }) => {
                const active = filter === k;
                return (
                  <button
                    key={k}
                    onClick={() => setFilter(k)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition ${
                      active ? 'bg-gray-900 text-white' : 'text-gray-600 hover:text-gray-900 hover:bg-white border border-transparent hover:border-gray-200'
                    }`}
                  >
                    <I size={11} /> {l}
                    <span className={`${active ? 'text-white/70' : 'text-gray-400'} font-mono text-[10px]`}>{n}</span>
                  </button>
                );
              })}
            </div>

            <div className="grid grid-cols-3 gap-5" style={{ fontFamily: "'Manrope', system-ui" }}>
              {items.map((p) => {
                const meta = TYPE_META[p.type];
                return (
                  <div key={p.id} className="group rounded-xl border border-gray-200 bg-white overflow-hidden hover:border-gray-300 hover:shadow-md transition cursor-pointer">
                    <div className="aspect-video bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center relative overflow-hidden">
                      {p.thumb ? (
                        <img src={p.thumb} alt="" className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                      ) : (
                        <meta.Icon size={32} strokeWidth={1} className="text-gray-300" />
                      )}
                    </div>
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <h3 className="text-[13px] font-semibold text-gray-900 leading-tight line-clamp-1">{p.name}</h3>
                        <button className="p-0.5 rounded hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition">
                          <MoreHorizontal size={14} className="text-gray-400" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-gray-600">
                        <span className={`inline-flex items-center gap-1 ${meta.light}`}>
                          <meta.Icon size={10} /> {meta.label}
                        </span>
                        <span className="text-gray-300">·</span>
                        <span>{p.status}</span>
                      </div>
                      <p className="text-[10px] text-gray-400 mt-1.5 font-mono uppercase tracking-wider">{p.when}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default function UxPreview() {
  const [mode, setMode] = useState('compare'); // 'compare' | 'dark' | 'light'

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-10 px-6">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');
      `}</style>

      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex items-start justify-between flex-wrap gap-4">
          <div>
            <button onClick={() => window.history.back()} className="text-xs text-gray-500 hover:text-gray-900 flex items-center gap-1 mb-2">
              <ChevronLeft size={12} /> voltar
            </button>
            <h1 className="text-3xl font-bold tracking-tight" style={{ fontFamily: "'Outfit', system-ui" }}>
              Nova Navegação StudioX — Preview
            </h1>
            <p className="text-sm text-gray-600 mt-1" style={{ fontFamily: "'Manrope', system-ui" }}>
              Mockup da página <code className="px-1.5 py-0.5 bg-gray-200 rounded text-[11px] font-mono">/projetos</code> (unifica Dashboard + StudioPage) com sidebar única à esquerda.
            </p>
          </div>
          <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-1">
            {[
              { k: 'compare', l: 'Comparar' },
              { k: 'dark', l: 'Dark' },
              { k: 'light', l: 'Light' },
            ].map(({ k, l }) => (
              <button
                key={k}
                onClick={() => setMode(k)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                  mode === k ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>

        {mode === 'compare' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div>
              <div className="mb-3 flex items-center gap-2">
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-gray-900 text-white text-[11px] font-semibold">
                  <span className="h-2 w-2 rounded-full bg-amber-500" /> DARK · Archetype Swiss/Linear
                </span>
              </div>
              <DarkMockup />
              <p className="text-xs text-gray-500 mt-3" style={{ fontFamily: "'Manrope', system-ui" }}>
                Fundo <code>#0A0A0A</code> · sidebar <code>#121212</code> · cards <code>#171717</code>. Mídias saltam, vibe Linear/Arc/Figma.
              </p>
            </div>
            <div>
              <div className="mb-3 flex items-center gap-2">
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-white border border-gray-200 text-gray-900 text-[11px] font-semibold">
                  <span className="h-2 w-2 rounded-full bg-amber-500" /> LIGHT · refinado mantendo âmbar
                </span>
              </div>
              <LightMockup />
              <p className="text-xs text-gray-500 mt-3" style={{ fontFamily: "'Manrope', system-ui" }}>
                Branco + cinza-claro · DNA âmbar preservado · mesma arquitetura de navegação da versão dark.
              </p>
            </div>
          </div>
        )}
        {mode === 'dark' && <DarkMockup />}
        {mode === 'light' && <LightMockup />}

        <div className="mt-10 bg-white rounded-2xl border border-gray-200 p-6 max-w-3xl" style={{ fontFamily: "'Manrope', system-ui" }}>
          <h2 className="text-base font-bold text-gray-900 mb-3" style={{ fontFamily: "'Outfit', system-ui" }}>O que muda vs hoje</h2>
          <ul className="text-sm text-gray-700 space-y-2">
            <li>✓ Sidebar única à esquerda (Projetos / Personagens / Agentes / Config) + avatar fixo no rodapé</li>
            <li>✓ Unifica Dashboard + StudioPage num único <code className="text-xs bg-gray-100 px-1 rounded">/projetos</code></li>
            <li>✓ Cards com thumbnail grande (aspect-video), 1 status line, menu "···" aparece só no hover</li>
            <li>✓ Filtros pill como chips sutis (Todos · Vídeos · Livros · Híbridos)</li>
            <li>✓ Header minimalista: título + contagem + search + CTA "Novo Projeto"</li>
            <li>✗ Remove: BottomNav (mobile usa drawer via hamburger), stats cards gigantes, seção "Agentes do Estúdio"</li>
            <li>✗ Remove: banner "Empresa do Projeto" grande (virou chip já na Fase 1)</li>
            <li>Fontes: <b>Outfit</b> (títulos) + <b>Manrope</b> (corpo) — Google Fonts, premium, distintas de Inter/Roboto</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
