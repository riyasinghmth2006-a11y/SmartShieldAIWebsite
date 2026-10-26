import type { ReactNode } from 'react'

export function Particles({ count = 18 }: { count?: number }) {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {Array.from({ length: count }).map((_, i) => (
        <span
          key={i}
          className="absolute rounded-full bg-cyan"
          style={{
            left: `${(i * 37) % 100}%`,
            top: `${40 + ((i * 53) % 60)}%`,
            width: 2 + (i % 3),
            height: 2 + (i % 3),
            animation: `drift ${5 + (i % 5)}s ${(i % 7) * 0.8}s linear infinite`,
            opacity: 0,
          }}
        />
      ))}
    </div>
  )
}

export function Shield3D({ size = 440, lock = true }: { size?: number; lock?: boolean }) {
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <div className="absolute inset-[8%] rounded-full bg-blue/30 blur-3xl" />
      <svg viewBox="0 0 400 400" className="absolute inset-0 h-full w-full" aria-hidden>
        <defs>
          <linearGradient id="sh-body" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#5fb6ff" />
            <stop offset="0.45" stopColor="#1685ff" />
            <stop offset="1" stopColor="#0a2a66" />
          </linearGradient>
          <linearGradient id="sh-inner" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#0f3a78" />
            <stop offset="1" stopColor="#061633" />
          </linearGradient>
          <linearGradient id="sh-edge" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#22d3ee" />
            <stop offset="1" stopColor="#8b5cf6" />
          </linearGradient>
          <linearGradient id="sh-gloss" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#fff" stopOpacity="0.55" />
            <stop offset="0.6" stopColor="#fff" stopOpacity="0" />
          </linearGradient>
          <filter id="sh-glow">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <ellipse cx="200" cy="372" rx="110" ry="14" fill="#000" opacity="0.5" />
        <g className="floaty" style={{ transformOrigin: '200px 200px' }}>
          <path d="M200 40 L330 85 V190 C330 270 275 328 200 362 C125 328 70 270 70 190 V85 Z" fill="url(#sh-body)" stroke="url(#sh-edge)" strokeWidth="3" filter="url(#sh-glow)" />
          <path d="M200 66 L308 102 V190 C308 255 262 305 200 334 C138 305 92 255 92 190 V102 Z" fill="url(#sh-inner)" stroke="#22d3ee" strokeOpacity="0.7" strokeWidth="1.5" />
          <path d="M200 40 L330 85 V190 C330 200 329 208 328 216 C300 150 250 110 200 100 C150 110 100 150 72 216 C71 208 70 200 70 190 V85 Z" fill="url(#sh-gloss)" opacity="0.35" />
          <path d="M200 66 V334" stroke="#22d3ee" strokeOpacity="0.15" />
          {lock && (
            <g filter="url(#sh-glow)">
              <path d="M170 190 V170 a30 30 0 0 1 60 0 V190" fill="none" stroke="#22d3ee" strokeWidth="9" strokeLinecap="round" />
              <rect x="152" y="188" width="96" height="76" rx="16" fill="#eaf6ff" />
              <rect x="152" y="188" width="96" height="76" rx="16" fill="url(#sh-body)" opacity="0.25" />
              <circle cx="200" cy="218" r="9" fill="#0a2a66" />
              <rect x="196" y="222" width="8" height="22" rx="4" fill="#0a2a66" />
            </g>
          )}
        </g>
      </svg>
      <div className="absolute inset-0 animate-[spin-slow_22s_linear_infinite]" style={{ transform: 'rotateX(68deg)' }}>
        <div className="absolute inset-[-4%] rounded-full border border-cyan/50" style={{ transform: 'rotate(0deg) scaleY(0.32)', boxShadow: '0 0 24px rgba(34,211,238,.35)' }} />
      </div>
      <div className="absolute inset-[-10%] rounded-full border border-violet/40" style={{ transform: 'rotate(-18deg) scaleY(0.28)', animation: 'none' }} />
      <div className="absolute inset-[-10%] rounded-full border border-dashed border-blue/50" style={{ transform: 'rotate(14deg) scaleY(0.2)' }} />
      <span className="absolute left-[2%] top-[46%] h-3 w-3 rounded-full bg-cyan shadow-[0_0_16px_#22d3ee]" />
      <span className="absolute right-[3%] top-[56%] h-2.5 w-2.5 rounded-full bg-violet shadow-[0_0_16px_#8b5cf6]" />
      <Particles />
    </div>
  )
}

export function MagnifierShield() {
  return (
    <svg viewBox="0 0 220 160" className="floaty h-full w-full" aria-hidden>
      <defs>
        <linearGradient id="mg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#22d3ee" />
          <stop offset="1" stopColor="#1685ff" />
        </linearGradient>
      </defs>
      <path d="M95 30 L140 46 V86 C140 110 122 126 95 138 C68 126 50 110 50 86 V46 Z" fill="#1685ff" fillOpacity="0.18" stroke="url(#mg)" strokeWidth="2.5" />
      <path d="M78 84 l12 12 l24 -26" fill="none" stroke="#22d3ee" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="148" cy="62" r="34" fill="#22d3ee" fillOpacity="0.1" stroke="url(#mg)" strokeWidth="5" />
      <path d="M172 88 L200 120" stroke="url(#mg)" strokeWidth="9" strokeLinecap="round" />
      <path d="M132 50 a22 22 0 0 1 20 -8" stroke="#fff" strokeOpacity="0.6" strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  )
}

export function NewsScan() {
  return (
    <svg viewBox="0 0 220 160" className="floaty h-full w-full" aria-hidden>
      <defs>
        <linearGradient id="ng" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8b5cf6" />
          <stop offset="1" stopColor="#22d3ee" />
        </linearGradient>
      </defs>
      <g transform="rotate(-8 100 80)">
        <rect x="40" y="20" width="110" height="124" rx="12" fill="#0c1b30" stroke="url(#ng)" strokeWidth="2.5" />
        <rect x="54" y="36" width="60" height="10" rx="3" fill="#22d3ee" fillOpacity="0.8" />
        <rect x="54" y="56" width="82" height="6" rx="3" fill="#94a8c7" fillOpacity="0.5" />
        <rect x="54" y="70" width="70" height="6" rx="3" fill="#94a8c7" fillOpacity="0.5" />
        <rect x="54" y="84" width="82" height="6" rx="3" fill="#94a8c7" fillOpacity="0.5" />
        <rect x="54" y="98" width="50" height="6" rx="3" fill="#94a8c7" fillOpacity="0.5" />
      </g>
      <circle cx="152" cy="94" r="30" fill="#22d3ee" fillOpacity="0.12" stroke="url(#ng)" strokeWidth="5" />
      <path d="M174 116 L198 142" stroke="url(#ng)" strokeWidth="9" strokeLinecap="round" />
    </svg>
  )
}

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <defs>
        <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#22d3ee" />
          <stop offset="1" stopColor="#1685ff" />
        </linearGradient>
      </defs>
      <path d="M16 2 L28 6.5 V15 C28 22 23 27 16 30 C9 27 4 22 4 15 V6.5 Z" fill="url(#lg)" />
      <path d="M11 16 l4 4 l7 -8" stroke="#050b18" strokeWidth="2.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Icon3D({ children, tone = 'blue' }: { children: ReactNode; tone?: 'blue' | 'cyan' | 'violet' }) {
  const t = { blue: 'from-blue/50 to-[#0a2a66]', cyan: 'from-cyan/50 to-[#0a4a66]', violet: 'from-violet/50 to-[#2a1a66]' }[tone]
  return (
    <div className={`relative grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br ${t} text-ink shadow-[0_12px_24px_-8px_rgba(22,133,255,.6),inset_0_1px_0_rgba(255,255,255,.35)] ring-1 ring-white/10`}>
      {children}
    </div>
  )
}

export const I = {
  input: <path d="M4 6h16M4 12h10M4 18h16" strokeLinecap="round" />,
  check: <path d="M5 12l5 5L20 7" strokeLinecap="round" strokeLinejoin="round" />,
  cpu: <><rect x="6" y="6" width="12" height="12" rx="2" /><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" /></>,
  list: <><path d="M9 6h11M9 12h11M9 18h11" strokeLinecap="round" /><circle cx="4.5" cy="6" r="1" /><circle cx="4.5" cy="12" r="1" /><circle cx="4.5" cy="18" r="1" /></>,
  verify: <><circle cx="11" cy="11" r="6" /><path d="M20 20l-4.5-4.5" strokeLinecap="round" /></>,
  media: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="M21 16l-5-5-8 8" strokeLinejoin="round" /></>,
  upload: <path d="M12 16V4m0 0l-4 4m4-4l4 4M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" strokeLinecap="round" strokeLinejoin="round" />,
  home: <path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" strokeLinejoin="round" />,
  shield: <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" strokeLinejoin="round" />,
  news: <><rect x="4" y="4" width="16" height="16" rx="2" /><path d="M8 9h8M8 13h8M8 17h5" strokeLinecap="round" /></>,
  flow: <><circle cx="6" cy="6" r="2.5" /><circle cx="18" cy="12" r="2.5" /><circle cx="6" cy="18" r="2.5" /><path d="M8 7l8 4M8 17l8-4" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7.5v.5" strokeLinecap="round" /></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />,
  close: <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />,
  warn: <><path d="M12 3l10 18H2z" strokeLinejoin="round" /><path d="M12 10v5M12 18v.5" strokeLinecap="round" /></>,
}

export function Ic({ d, size = 22 }: { d: ReactNode; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      {d}
    </svg>
  )
}

export function MediaFrame3D() {
  return (
    <svg viewBox="0 0 220 160" className="floaty h-full w-full" aria-hidden>
      <defs>
        <linearGradient id="dg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#22d3ee" />
          <stop offset="1" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
      <rect x="52" y="26" width="112" height="100" rx="12" fill="#8b5cf6" fillOpacity="0.12" stroke="#8b5cf6" strokeOpacity="0.5" transform="rotate(8 108 76)" />
      <rect x="40" y="22" width="116" height="104" rx="12" fill="#0c1b30" stroke="url(#dg)" strokeWidth="2.5" />
      <ellipse cx="98" cy="64" rx="19" ry="23" fill="none" stroke="#22d3ee" strokeOpacity="0.8" strokeWidth="2" strokeDasharray="4 4" />
      <path d="M62 120 c4 -22 18 -30 36 -30 s32 8 36 30" fill="none" stroke="#22d3ee" strokeOpacity="0.5" strokeWidth="2" strokeDasharray="4 4" />
      <path d="M40 78 H156" stroke="#22d3ee" strokeWidth="2" opacity="0.9" />
      <circle cx="156" cy="100" r="28" fill="#22d3ee" fillOpacity="0.12" stroke="url(#dg)" strokeWidth="5" />
      <path d="M176 122 L198 146" stroke="url(#dg)" strokeWidth="9" strokeLinecap="round" />
      <circle cx="30" cy="40" r="2.5" fill="#22d3ee" />
      <circle cx="190" cy="40" r="2" fill="#8b5cf6" />
    </svg>
  )
}
