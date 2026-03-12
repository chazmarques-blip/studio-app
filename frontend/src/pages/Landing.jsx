import { useNavigate } from 'react-router-dom';
import { Bot, MessageSquare, Zap, Globe, ArrowRight, Shield, BarChart3 } from 'lucide-react';

const features = [
  { icon: Bot, title: 'AI-Powered Agents', desc: 'Deploy intelligent chatbots that learn and adapt to your business.' },
  { icon: MessageSquare, title: 'Omnichannel Inbox', desc: 'WhatsApp, Instagram, Facebook & Telegram in one unified view.' },
  { icon: Zap, title: 'Multi-Agent System', desc: 'Seamlessly switch between specialized agents mid-conversation.' },
  { icon: Globe, title: 'Multi-Language', desc: 'Auto-detect and respond in your customer\'s language.' },
  { icon: Shield, title: 'CRM with AI', desc: 'Leads are created and scored automatically by AI.' },
  { icon: BarChart3, title: 'Real-Time Analytics', desc: 'Track performance, costs, and conversion in real-time.' },
];

const channels = [
  { name: 'WhatsApp', color: '#25D366' },
  { name: 'Instagram', color: '#E4405F' },
  { name: 'Facebook', color: '#1877F2' },
  { name: 'Telegram', color: '#0088CC' },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      {/* Navbar */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-[#2A2A2A]/50 bg-[#0A0A0A]/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#C9A84C] to-[#A88B3D]">
              <Bot size={18} className="text-[#0A0A0A]" />
            </div>
            <span className="text-lg font-bold text-white">AgentFlow</span>
          </div>
          <nav className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm text-[#A0A0A0] transition hover:text-white">Features</a>
            <a href="#channels" className="text-sm text-[#A0A0A0] transition hover:text-white">Channels</a>
            <a href="#pricing" className="text-sm text-[#A0A0A0] transition hover:text-white">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <button
              data-testid="landing-login-btn"
              onClick={() => navigate('/login')}
              className="btn-gold-outline rounded-lg px-4 py-2 text-sm"
            >
              Sign In
            </button>
            <button
              data-testid="landing-signup-btn"
              onClick={() => navigate('/login?tab=signup')}
              className="btn-gold rounded-lg px-4 py-2 text-sm"
            >
              Start Free
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative flex min-h-screen flex-col items-center justify-center px-6 pt-20">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-1/3 h-[400px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[120px]" />
        </div>
        <div className="relative z-10 mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-4 py-1.5">
            <Zap size={14} className="text-[#C9A84C]" />
            <span className="text-xs font-medium text-[#A0A0A0]">AI-powered automation for your business</span>
          </div>
          <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
            Deploy AI Agents<br />
            <span className="bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] bg-clip-text text-transparent">
              in Minutes
            </span>
          </h1>
          <p className="mx-auto mb-8 max-w-xl text-base text-[#A0A0A0] sm:text-lg">
            The no-code platform that lets you create, customize, and deploy intelligent AI agents across all your social channels.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <button
              data-testid="hero-start-free-btn"
              onClick={() => navigate('/login?tab=signup')}
              className="btn-gold flex items-center gap-2 rounded-xl px-8 py-3.5 text-base font-semibold"
            >
              Start Free <ArrowRight size={18} />
            </button>
            <button className="btn-gold-outline rounded-xl px-8 py-3.5 text-base">
              Watch Demo
            </button>
          </div>
        </div>

        {/* Channel badges */}
        <div id="channels" className="relative z-10 mt-16 flex flex-wrap items-center justify-center gap-4">
          {channels.map(ch => (
            <div key={ch.name} className="glass-card flex items-center gap-2 px-5 py-2.5">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ch.color }} />
              <span className="text-sm font-medium text-[#A0A0A0]">{ch.name}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-2xl font-bold text-white sm:text-3xl">Everything You Need</h2>
          <p className="text-base text-[#A0A0A0]">Powerful features to automate your customer interactions</p>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div
              key={i}
              className="glass-card group p-6 transition-all duration-300 hover:border-[rgba(201,168,76,0.3)]"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]/10">
                <f.icon size={20} className="text-[#C9A84C]" />
              </div>
              <h3 className="mb-2 text-base font-semibold text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-[#A0A0A0]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-2xl font-bold text-white sm:text-3xl">Choose Your Plan</h2>
          <p className="text-base text-[#A0A0A0]">Start free, upgrade when you need more</p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {/* Free */}
          <div className="glass-card flex flex-col p-6">
            <h3 className="mb-1 text-lg font-bold text-white">Free</h3>
            <p className="mb-4 text-sm text-[#666666]">Try before you buy</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">$0</span><span className="text-sm text-[#666666]">/forever</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#A0A0A0]">
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />1 Agent</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />50 messages/week</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />1 Channel</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />Basic analytics</li>
            </ul>
            <button onClick={() => navigate('/login?tab=signup')} className="btn-gold-outline w-full rounded-lg py-2.5 text-sm">Start Free</button>
          </div>
          {/* Starter */}
          <div className="glass-card gold-glow relative flex flex-col border-[rgba(201,168,76,0.4)] p-6">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#C9A84C] px-3 py-0.5 text-xs font-semibold text-[#0A0A0A]">Most Popular</div>
            <h3 className="mb-1 text-lg font-bold text-white">Starter</h3>
            <p className="mb-4 text-sm text-[#666666]">For growing businesses</p>
            <div className="mb-6"><span className="text-3xl font-bold text-[#C9A84C]">$49</span><span className="text-sm text-[#666666]">/month</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#A0A0A0]">
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />5 Agents</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />10,000 messages/month</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />All 4 Channels</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />Full CRM + Campaigns</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />Priority Support</li>
            </ul>
            <button className="btn-gold w-full rounded-lg py-2.5 text-sm">Subscribe</button>
          </div>
          {/* Enterprise */}
          <div className="glass-card flex flex-col p-6">
            <h3 className="mb-1 text-lg font-bold text-white">Enterprise</h3>
            <p className="mb-4 text-sm text-[#666666]">For large operations</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">Custom</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#A0A0A0]">
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />Unlimited Agents</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />Unlimited Messages</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />Custom Integrations</li>
              <li className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]" />Dedicated Support</li>
            </ul>
            <button className="btn-gold-outline w-full rounded-lg py-2.5 text-sm">Contact Us</button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#2A2A2A] bg-[#0A0A0A] px-6 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-[#C9A84C] to-[#A88B3D]">
              <Bot size={14} className="text-[#0A0A0A]" />
            </div>
            <span className="text-sm font-semibold text-white">AgentFlow</span>
          </div>
          <p className="text-xs text-[#666666]">2025 AgentFlow. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
