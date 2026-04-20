import { useState } from 'react';
import {
  Home, Users, Bot, Settings, BookOpen, Video, Layers, Plus, Search,
  MoreHorizontal, Folder, ChevronLeft, Check, Zap, FileText, Clapperboard, Clock, Loader2 as Loader,
} from 'lucide-react';

// Fake projects used to demonstrate layout density + card styling
const MOCK_PROJECTS = [
  { id: 1, name: 'Lila e seus Brinquedos Fantásticos', type: 'book', thumb: null, status: 'PDF pronto', when: 'Hoje', characters: 3, pages: 40, done: true },
  { id: 2, name: 'Abraão, Isaque e o Cordeiro — Picturebook', type: 'book', thumb: null, status: 'PDF pronto', when: 'Ontem', characters: 5, pages: 32, done: true },
  { id: 3, name: 'A Raposinha Generosa', type: 'book', thumb: null, status: 'PDF pronto', when: 'Ontem', characters: 4, pages: 40, done: true },
  { id: 4, name: 'Manual do Pulmeranea', type: 'book', thumb: null, status: 'Ilustrações 80%', when: '2 dias', characters: 3, pages: 36, done: false },
  { id: 5, name: 'Aventura no Bosque — Piloto', type: 'video', thumb: null, status: '6 cenas · 3 min', when: '3 dias', characters: 4, scenes: 6, done: true },
  { id: 6, name: 'Saga do Relógio Antigo', type: 'hybrid', thumb: null, status: 'Em produção', when: '4 dias', characters: 7, scenes: 14, done: false },
  { id: 7, name: 'O Oráculo de Ferro', type: 'video', thumb: null, status: '12 cenas · 8 min', when: 'semana', characters: 9, scenes: 12, done: true },
  { id: 8, name: 'Pequenos Exploradores do Mar', type: 'book', thumb: null, status: 'Outline aprovado', when: 'semana', characters: 5, pages: 28, done: false },
];

const TYPE_META = {
  video: { label: 'Vídeo', Icon: Video, dark: 'text-violet-400', light: 'text-violet-600' },
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
      <div className="flex h-[680px] bg-[#0A0614] text-[#F5F5F5]" style={{ fontFamily: "'Outfit', system-ui" }}>
        {/* SIDEBAR */}
        <aside className="w-60 shrink-0 bg-[#110A1F] border-r border-[#2A2442] flex flex-col">
          <div className="h-14 px-5 flex items-center gap-2 border-b border-[#2A2442]">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center text-xs font-black text-white shadow-[0_0_20px_rgba(139,92,246,0.4)]">X</div>
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
                    isActive ? 'bg-violet-500/15 text-violet-200' : 'text-[#A3A3B2] hover:bg-white/5 hover:text-white'
                  }`}
                >
                  {isActive && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-violet-500" />}
                  <Icon size={16} strokeWidth={1.75} />
                  <span className="flex-1 text-left">{label}</span>
                  {count != null && (
                    <span className={`text-[10px] font-mono ${isActive ? 'text-violet-300/80' : 'text-[#6B647F]'}`}>{count}</span>
                  )}
                </button>
              );
            })}
          </nav>
          <div className="px-3 pb-3 border-t border-[#2A2442] pt-3">
            <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/5 cursor-pointer">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-orange-500 flex items-center justify-center text-[11px] font-bold text-white">TU</div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-medium text-white truncate">Test User</p>
                <p className="text-[10px] text-[#6B647F] flex items-center gap-1 font-mono"><Zap size={9} className="text-orange-400" />9,987 / 10k</p>
              </div>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="h-14 px-8 flex items-center justify-between border-b border-[#2A2442]">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-semibold tracking-tight">Projetos</h1>
              <span className="text-xs font-mono text-[#6B647F]">66</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B647F]" />
                <input
                  placeholder="Buscar..."
                  className="w-64 h-9 pl-9 pr-3 rounded-lg bg-[#1A1430] border border-[#2A2442] text-xs text-white placeholder:text-[#6B647F] outline-none focus:border-violet-500/60 transition"
                />
              </div>
              <button className="h-9 px-4 rounded-lg bg-gradient-to-r from-orange-500 to-orange-600 text-white text-xs font-semibold hover:brightness-110 transition flex items-center gap-1.5 shadow-[0_0_20px_rgba(249,115,22,0.35)]">
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
                      active ? 'bg-violet-500/15 text-violet-200 border border-violet-500/30' : 'text-[#A3A3B2] hover:text-white hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <I size={11} /> {l}
                    <span className={`${active ? 'text-violet-300/70' : 'text-[#6B647F]'} font-mono text-[10px]`}>{n}</span>
                  </button>
                );
              })}
            </div>

            <div className="space-y-1.5" style={{ fontFamily: "'Manrope', system-ui" }}>
              {items.map((p) => {
                const meta = TYPE_META[p.type];
                return (
                  <div
                    key={p.id}
                    className="group flex items-center gap-3 rounded-xl border border-[#2A2442] bg-[#1A1430] hover:border-violet-500/40 transition cursor-pointer px-2 py-1"
                  >
                    {/* Thumbnail — horizontal (16:9) */}
                    <div className="w-28 h-16 shrink-0 rounded-md bg-gradient-to-br from-[#221A3F] to-[#0D0719] overflow-hidden flex items-center justify-center relative">
                      {p.thumb ? (
                        <img src={p.thumb} alt="" className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                      ) : (
                        <meta.Icon size={22} strokeWidth={1.25} className="text-[#4A3F6B]" />
                      )}
                    </div>

                    {/* Name + meta */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-[14px] font-semibold text-white truncate leading-tight">{p.name}</h3>
                      <div className="flex items-center gap-2.5 text-[11px] text-[#A3A3B2] mt-1 flex-wrap">
                        <span className={`inline-flex items-center gap-1 font-medium ${meta.dark}`}>
                          <meta.Icon size={11} /> {meta.label}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Users size={11} className="text-[#6B647F]" />
                          {p.characters} {p.characters === 1 ? 'personagem' : 'personagens'}
                        </span>
                        {p.pages && (
                          <span className="inline-flex items-center gap-1">
                            <FileText size={11} className="text-[#6B647F]" />
                            {p.pages} páginas
                          </span>
                        )}
                        {p.scenes && (
                          <span className="inline-flex items-center gap-1">
                            <Clapperboard size={11} className="text-[#6B647F]" />
                            {p.scenes} cenas
                          </span>
                        )}
                        <span className={`inline-flex items-center gap-1 font-medium ${p.done ? 'text-emerald-400' : 'text-amber-400'}`}>
                          {p.done ? <Check size={11} /> : <Loader size={11} />}
                          {p.status}
                        </span>
                        <span className="inline-flex items-center gap-1 text-[#6B647F]">
                          <Clock size={11} />
                          {p.when}
                        </span>
                      </div>
                    </div>

                    {/* Status badge + actions (right side) */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      <div className={`h-9 w-9 rounded-full flex items-center justify-center ${
                        p.done ? 'bg-gradient-to-br from-violet-500 to-orange-500 shadow-[0_0_16px_rgba(139,92,246,0.35)]' : 'bg-gradient-to-br from-[#2A2442] to-[#1A1430] border border-[#3A3258]'
                      }`} title={p.done ? 'Pronto' : 'Em progresso'}>
                        <meta.Icon size={14} className="text-white" />
                      </div>

                      <button className="w-[108px] h-8 rounded-full bg-violet-500/10 text-violet-300 hover:bg-violet-500/20 text-[11px] font-medium flex items-center justify-center gap-1.5 transition border border-violet-500/20">
                        <BookOpen size={12} /> {p.type === 'video' ? 'Abrir vídeo' : 'Abrir livro'}
                      </button>
                      <button className="w-[100px] h-8 rounded-full bg-orange-500/10 text-orange-300 hover:bg-orange-500/20 text-[11px] font-medium flex items-center justify-center gap-1.5 transition border border-orange-500/20">
                        <BookOpen size={12} /> Carregar
                      </button>
                      <button className="p-1.5 rounded-md hover:bg-white/10 transition">
                        <MoreHorizontal size={14} className="text-[#6B647F]" />
                      </button>
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
        <aside className="w-60 shrink-0 bg-[#FAF8FD] border-r border-[#EEECF5] flex flex-col">
          <div className="h-14 px-5 flex items-center gap-2 border-b border-[#EEECF5]">
            <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center text-xs font-black text-white shadow-sm">X</div>
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
                    isActive ? 'bg-violet-50 text-violet-800' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {isActive && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-violet-500" />}
                  <Icon size={16} strokeWidth={1.75} />
                  <span className="flex-1 text-left">{label}</span>
                  {count != null && (
                    <span className={`text-[10px] font-mono ${isActive ? 'text-violet-600' : 'text-gray-400'}`}>{count}</span>
                  )}
                </button>
              );
            })}
          </nav>
          <div className="px-3 pb-3 border-t border-[#EEECF5] pt-3">
            <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-white cursor-pointer">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-orange-500 flex items-center justify-center text-[11px] font-bold text-white">TU</div>
              <div className="flex-1 min-w-0">
                <p className="text-[12px] font-medium text-gray-900 truncate">Test User</p>
                <p className="text-[10px] text-gray-500 flex items-center gap-1 font-mono"><Zap size={9} className="text-orange-500" />9,987 / 10k</p>
              </div>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="h-14 px-8 flex items-center justify-between border-b border-[#EEECF5] bg-white">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-semibold tracking-tight">Projetos</h1>
              <span className="text-xs font-mono text-gray-400">66</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  placeholder="Buscar..."
                  className="w-64 h-9 pl-9 pr-3 rounded-lg bg-gray-50 border border-gray-200 text-xs text-gray-900 placeholder:text-gray-400 outline-none focus:border-violet-400 transition"
                />
              </div>
              <button className="h-9 px-4 rounded-lg bg-gradient-to-r from-orange-500 to-orange-600 text-white text-xs font-semibold hover:brightness-110 transition flex items-center gap-1.5 shadow-[0_0_20px_rgba(249,115,22,0.3)]">
                <Plus size={14} strokeWidth={2.5} /> Novo Projeto
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-auto px-8 py-6 bg-[#FAFAFC]">
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
                      active ? 'bg-violet-100 text-violet-800 border border-violet-200' : 'text-gray-600 hover:text-gray-900 hover:bg-white border border-transparent hover:border-gray-200'
                    }`}
                  >
                    <I size={11} /> {l}
                    <span className={`${active ? 'text-violet-600' : 'text-gray-400'} font-mono text-[10px]`}>{n}</span>
                  </button>
                );
              })}
            </div>

            <div className="space-y-1.5" style={{ fontFamily: "'Manrope', system-ui" }}>
              {items.map((p) => {
                const meta = TYPE_META[p.type];
                return (
                  <div
                    key={p.id}
                    className="group flex items-center gap-3 rounded-xl border border-[#EEECF5] bg-white hover:border-violet-200 hover:shadow-sm transition cursor-pointer px-2 py-1"
                  >
                    {/* Thumbnail — horizontal (16:9) */}
                    <div className="w-28 h-16 shrink-0 rounded-md bg-gradient-to-br from-violet-50 to-gray-100 overflow-hidden flex items-center justify-center relative">
                      {p.thumb ? (
                        <img src={p.thumb} alt="" className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                      ) : (
                        <meta.Icon size={22} strokeWidth={1.25} className="text-violet-200" />
                      )}
                    </div>

                    {/* Name + meta */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-[14px] font-semibold text-gray-900 truncate leading-tight">{p.name}</h3>
                      <div className="flex items-center gap-2.5 text-[11px] text-gray-600 mt-1 flex-wrap">
                        <span className={`inline-flex items-center gap-1 font-medium ${meta.light}`}>
                          <meta.Icon size={11} /> {meta.label}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Users size={11} className="text-gray-400" />
                          {p.characters} {p.characters === 1 ? 'personagem' : 'personagens'}
                        </span>
                        {p.pages && (
                          <span className="inline-flex items-center gap-1">
                            <FileText size={11} className="text-gray-400" />
                            {p.pages} páginas
                          </span>
                        )}
                        {p.scenes && (
                          <span className="inline-flex items-center gap-1">
                            <Clapperboard size={11} className="text-gray-400" />
                            {p.scenes} cenas
                          </span>
                        )}
                        <span className={`inline-flex items-center gap-1 font-medium ${p.done ? 'text-emerald-600' : 'text-amber-600'}`}>
                          {p.done ? <Check size={11} /> : <Loader size={11} />}
                          {p.status}
                        </span>
                        <span className="inline-flex items-center gap-1 text-gray-500">
                          <Clock size={11} />
                          {p.when}
                        </span>
                      </div>
                    </div>

                    {/* Status badge + actions */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      <div className={`h-9 w-9 rounded-full flex items-center justify-center ${
                        p.done ? 'bg-gradient-to-br from-violet-500 to-orange-500 shadow-[0_0_12px_rgba(139,92,246,0.25)]' : 'bg-gradient-to-br from-gray-200 to-gray-300'
                      }`} title={p.done ? 'Pronto' : 'Em progresso'}>
                        <meta.Icon size={14} className="text-white" />
                      </div>

                      <button className="w-[108px] h-8 rounded-full bg-violet-50 text-violet-700 hover:bg-violet-100 text-[11px] font-medium flex items-center justify-center gap-1.5 transition border border-violet-100">
                        <BookOpen size={12} /> {p.type === 'video' ? 'Abrir vídeo' : 'Abrir livro'}
                      </button>
                      <button className="w-[100px] h-8 rounded-full bg-orange-50 text-orange-700 hover:bg-orange-100 text-[11px] font-medium flex items-center justify-center gap-1.5 transition border border-orange-100">
                        <BookOpen size={12} /> Carregar
                      </button>
                      <button className="p-1.5 rounded-md hover:bg-gray-100 transition">
                        <MoreHorizontal size={14} className="text-gray-400" />
                      </button>
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
