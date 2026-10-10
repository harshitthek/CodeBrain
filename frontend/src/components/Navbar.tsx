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
    <header className="fixed top-0 left-0 right-0 z-50 w-full bg-black/60 backdrop-blur-xl border-b border-white/[0.05] transition-all">
      <div className="max-w-[1280px] mx-auto px-6 md:px-12 h-20 flex items-center justify-between">
        {/* Brand Logo Lockup */}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          className="flex items-center gap-3.5 group text-decoration-none select-none"
        >
          {/* Triangular brand glyph with Electric Iris to Deep Verdant gradient */}
          <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 bg-[#8052ff] opacity-40 blur-md rounded-full group-hover:opacity-75 transition-opacity" />
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
            <span className="text-[#9a9a9a] text-[10px] font-mono uppercase tracking-[0.15em] hidden sm:inline">
              Core
            </span>
          </div>
        </a>

        {/* Desktop Nav Items */}
        <nav className="hidden lg:flex items-center gap-9">
          <button
            onClick={() => scrollTo('pipeline')}
            className={`ghost-link transition-colors ${activeSection === 'pipeline' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Studio
          </button>
          <button
            onClick={() => scrollTo('agents')}
            className={`ghost-link transition-colors ${activeSection === 'agents' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Agents
          </button>
          <button
            onClick={() => scrollTo('apirunner')}
            className={`ghost-link transition-colors ${activeSection === 'apirunner' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            HTTPX Runner
          </button>
          <button
            onClick={() => scrollTo('architecture')}
            className={`ghost-link transition-colors ${activeSection === 'architecture' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Architecture
          </button>
          <button
            onClick={() => scrollTo('rag')}
            className={`ghost-link transition-colors ${activeSection === 'rag' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Hybrid RAG
          </button>
        </nav>

        {/* Right CTA */}
        <div className="flex items-center gap-4">
          <button
            onClick={onLaunchPipeline}
            className="btn-primary-pill shadow-[0_0_20px_-3px_rgba(128,82,255,0.4)]"
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
          <button
            onClick={() => scrollTo('pipeline')}
            className="ghost-link text-left text-base text-white"
          >
            Studio
          </button>
          <button
            onClick={() => scrollTo('agents')}
            className="ghost-link text-left text-base text-white"
          >
            Agents
          </button>
          <button
            onClick={() => scrollTo('apirunner')}
            className="ghost-link text-left text-base text-white"
          >
            HTTPX Runner
          </button>
          <button
            onClick={() => scrollTo('architecture')}
            className="ghost-link text-left text-base text-white"
          >
            Architecture
          </button>
          <button
            onClick={() => scrollTo('rag')}
            className="ghost-link text-left text-base text-white"
          >
            Hybrid RAG
          </button>
        </div>
      )}
    </header>
  );
};
