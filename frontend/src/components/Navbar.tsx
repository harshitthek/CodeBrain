import React, { useState } from 'react';
import { scrollToElement } from '../utils/smoothScroll';

interface NavbarProps {
  onLaunchPipeline: () => void;
  activeSection?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ onLaunchPipeline, activeSection = 'pipeline' }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavClick = (id: string) => {
    setMobileMenuOpen(false);
    scrollToElement(id);
  };

  return (
    <header className="fixed top-4 left-0 right-0 z-50 flex justify-center px-4 sm:px-6 pointer-events-none">
      {/* Hallmark N5 Floating Pill Nav: Detached, frosted, precision bounds */}
      <div className="pointer-events-auto max-w-[1020px] w-full h-[58px] rounded-full bg-[#08080c]/85 backdrop-blur-2xl border border-white/[0.09] shadow-[0_12px_40px_rgba(0,0,0,0.7)] px-5 sm:px-6 flex items-center justify-between transition-all duration-300">
        
        {/* Brand Logo Lockup */}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            scrollToElement('hero', -120);
          }}
          className="flex items-center gap-3 group text-decoration-none select-none"
        >
          <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 bg-[#8052ff] opacity-40 blur-md rounded-full group-hover:opacity-75 transition-opacity" />
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="relative transition-transform duration-300 group-hover:scale-105">
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
            <span className="text-[#f5f5f7] text-[16px] font-normal tracking-[-0.02em]">
              CodeBrain
            </span>
            <span className="text-[#ffb829] text-[9px] font-mono uppercase tracking-[0.18em] font-semibold">
              CORE
            </span>
          </div>
        </a>

        {/* Desktop Nav Items */}
        <nav className="hidden md:flex items-center gap-6 lg:gap-7">
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
                onClick={() => handleNavClick(item.id)}
                className={`ghost-link transition-colors relative py-1 text-[12px] uppercase tracking-[0.06em] font-mono ${
                  isActive ? 'text-[#f5f5f7] font-semibold' : 'text-[#8e8e98] hover:text-[#f5f5f7]'
                }`}
              >
                {item.label}
                {isActive && (
                  <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-[#8052ff] shadow-[0_0_8px_#8052ff]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Action: Single Electric Iris Pill Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              onLaunchPipeline();
              scrollToElement('pipeline');
            }}
            className="btn-primary-pill text-[12px] py-2 px-4.5 h-[38px] shadow-[0_0_20px_-3px_rgba(128,82,255,0.4)]"
          >
            Launch Studio
          </button>

          {/* Mobile hamburger toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-[#8e8e98] hover:text-white p-1.5 focus:outline-none"
            aria-label="Toggle Menu"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
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
        <div className="pointer-events-auto absolute top-20 left-4 right-4 bg-[#0a0a0f]/95 backdrop-blur-2xl px-6 py-6 rounded-[24px] border border-white/[0.09] shadow-2xl flex flex-col gap-4 md:hidden">
          {[
            { id: 'pipeline', label: 'Studio' },
            { id: 'agents', label: 'Agents' },
            { id: 'apirunner', label: 'HTTPX Runner' },
            { id: 'architecture', label: 'Architecture' },
            { id: 'rag', label: 'Hybrid RAG' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className="ghost-link text-left text-sm text-[#f5f5f7] py-2 font-mono"
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
};
