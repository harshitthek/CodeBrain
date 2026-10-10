import React, { useState } from 'react';

interface NavbarProps {
  onLaunchPipeline: () => void;
  activeSection?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ onLaunchPipeline, activeSection = 'pipeline' }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollTo = (id: string) => {
    setMobileMenuOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full bg-black/75 backdrop-blur-xl border-b border-white/[0.06] transition-all">
      <div className="max-w-[1240px] mx-auto px-6 md:px-12 h-20 flex items-center justify-between">
        {/* Brand Logo Lockup: DESIGN.md token (triangular glyph + wordmark) */}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          className="flex items-center gap-3.5 group text-decoration-none select-none"
        >
          <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 bg-[#8052ff] opacity-30 blur-md rounded-full group-hover:opacity-60 transition-opacity" />
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="relative transition-transform duration-300 group-hover:scale-105">
              <defs>
                <linearGradient id="navBrandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8052ff" />
                  <stop offset="100%" stopColor="#15846e" />
                </linearGradient>
              </defs>
              <polygon points="12,2 22,20 2,20" fill="url(#navBrandGrad)" />
            </svg>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-white text-[19px] font-normal tracking-[-0.03em]">
              CodeBrain
            </span>
            <span className="text-[#ffb829] text-[9px] font-mono uppercase tracking-[0.2em] font-semibold">
              CORE
            </span>
          </div>
        </a>

        {/* Desktop Nav Items */}
        <nav className="hidden lg:flex items-center gap-8">
          {[
            { id: 'pipeline', label: 'Studio' },
            { id: 'agents', label: 'Agents' },
            { id: 'apirunner', label: 'HTTPX Runner' },
            { id: 'architecture', label: 'Architecture' },
            { id: 'rag', label: 'Hybrid RAG' },
          ].map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className={`ghost-link transition-colors relative py-1 text-[13px] tracking-[0.04em] ${
                  isActive ? 'text-white font-medium' : 'text-[#9a9a9a] hover:text-white'
                }`}
              >
                {item.label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#8052ff] rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right CTA: Single Electric Iris Pill Button */}
        <div className="flex items-center gap-4">
          <button
            onClick={onLaunchPipeline}
            className="btn-primary-pill shadow-[0_0_24px_-4px_rgba(128,82,255,0.4)]"
          >
            Launch Auto-Pilot
          </button>

          {/* Mobile hamburger toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden text-[#9a9a9a] hover:text-white p-2 focus:outline-none"
            aria-label="Toggle Menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              {mobileMenuOpen ? (
                <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
              ) : (
                <path d="M4 8h16M4 16h16" strokeLinecap="round" strokeLinejoin="round" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-black/95 backdrop-blur-2xl px-6 py-8 flex flex-col gap-6 border-b border-white/[0.08]">
          {[
            { id: 'pipeline', label: 'Studio' },
            { id: 'agents', label: 'Agents' },
            { id: 'apirunner', label: 'HTTPX Runner' },
            { id: 'architecture', label: 'Architecture' },
            { id: 'rag', label: 'Hybrid RAG' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="ghost-link text-left text-base text-white py-1"
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
};
