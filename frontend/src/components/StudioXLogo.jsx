import React from 'react';

/**
 * StudioX Logo Component
 * A modern, sleek logo for the StudioX brand with violet/purple color scheme
 */
export function StudioXLogo({ size = 'md', showText = true, className = '' }) {
  const sizes = {
    xs: { icon: 20, text: 'text-sm', gap: 'gap-1' },
    sm: { icon: 24, text: 'text-base', gap: 'gap-1.5' },
    md: { icon: 32, text: 'text-lg', gap: 'gap-2' },
    lg: { icon: 40, text: 'text-xl', gap: 'gap-2.5' },
    xl: { icon: 48, text: 'text-2xl', gap: 'gap-3' },
  };
  
  const s = sizes[size] || sizes.md;
  
  return (
    <div className={`flex items-center ${s.gap} ${className}`}>
      <div className="relative">
        <svg 
          width={s.icon} 
          height={s.icon} 
          viewBox="0 0 48 48" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="studioXGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#A78BFA" />
              <stop offset="50%" stopColor="#8B5CF6" />
              <stop offset="100%" stopColor="#7C3AED" />
            </linearGradient>
            <linearGradient id="studioXGradLight" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#C4B5FD" />
              <stop offset="100%" stopColor="#A78BFA" />
            </linearGradient>
          </defs>
          <circle cx="24" cy="24" r="20" fill="url(#studioXGrad)" />
          <circle cx="24" cy="24" r="14" fill="#0A0A0A" />
          <path d="M18 18L30 30M30 18L18 30" stroke="url(#studioXGradLight)" strokeWidth="3.5" strokeLinecap="round" />
          <circle cx="24" cy="6" r="2.5" fill="#0A0A0A" />
          <circle cx="24" cy="42" r="2.5" fill="#0A0A0A" />
          <circle cx="6" cy="24" r="2.5" fill="#0A0A0A" />
          <circle cx="42" cy="24" r="2.5" fill="#0A0A0A" />
        </svg>
        <div 
          className="absolute inset-0 rounded-full blur-md opacity-30 -z-10"
          style={{ background: 'linear-gradient(135deg, #A78BFA, #7C3AED)' }}
        />
      </div>
      {showText && (
        <span className={`font-bold tracking-tight ${s.text}`}>
          <span className="text-white">Studio</span>
          <span className="bg-gradient-to-r from-[#A78BFA] to-[#8B5CF6] bg-clip-text text-transparent">X</span>
        </span>
      )}
    </div>
  );
}

export function StudioXMark({ size = 24, className = '' }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 48 48" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="studioXMarkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#A78BFA" />
          <stop offset="50%" stopColor="#8B5CF6" />
          <stop offset="100%" stopColor="#7C3AED" />
        </linearGradient>
      </defs>
      <circle cx="24" cy="24" r="20" fill="url(#studioXMarkGrad)" />
      <circle cx="24" cy="24" r="14" fill="#0A0A0A" />
      <path d="M18 18L30 30M30 18L18 30" stroke="#C4B5FD" strokeWidth="3.5" strokeLinecap="round" />
    </svg>
  );
}

export default StudioXLogo;
