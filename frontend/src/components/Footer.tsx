import React from 'react';
import { scrollToElement } from '../utils/smoothScroll';

interface FooterProps {
  onLaunchPipeline: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onLaunchPipeline }) => {
  return (
    <footer className="relative w-full bg-transparent py-16 border-t border-white/[0.06]">
      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12">
        
        {/* Top footer row: Hallmark Ft2 Inline Minimalist Colophon */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-12 border-b border-white/[0.05]">
          <div className="flex items-center gap-3">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <defs>
                <linearGradient id="footerGradCB2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8052ff" />
                  <stop offset="100%" stopColor="#15846e" />
                </linearGradient>
              </defs>
              <polygon points="12,2 22,20 2,20" fill="url(#footerGradCB2)" />
            </svg>
            <div className="flex items-baseline gap-2">
              <span className="text-white text-[17px] font-normal tracking-[-0.02em]">
                CodeBrain
              </span>
              <span className="text-[#8e8e98] text-[10px] font-mono tracking-[0.12em] uppercase">
                L2/L3 AUTONOMOUS QA
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-5 sm:gap-7 text-xs font-mono">
            <button
              onClick={() => scrollToElement('pipeline')}
              className="ghost-link"
            >
              Studio
            </button>
            <button
              onClick={() => scrollToElement('agents')}
              className="ghost-link"
            >
              Agents
            </button>
            <button
              onClick={() => scrollToElement('apirunner')}
              className="ghost-link"
            >
              HTTPX Runner
            </button>
            <button
              onClick={() => scrollToElement('architecture')}
              className="ghost-link"
            >
              Architecture
            </button>
            <button
              onClick={() => scrollToElement('rag')}
              className="ghost-link"
            >
              Hybrid RAG
            </button>
            <button
              onClick={() => {
                onLaunchPipeline();
                scrollToElement('pipeline');
              }}
              className="accent-link"
            >
              Launch Studio →
            </button>
          </div>
        </div>

        {/* Bottom row: System Status & Ethos */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-6 text-[#8e8e98] text-[12px] font-mono">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#15846e]" />
            <span>ENGINE STATUS: DETERMINISTIC & OPERATIONAL</span>
          </div>

          <div className="font-[200] text-[#8e8e98]">
            © {new Date().getFullYear()} CodeBrain. Built with Lenis physics & Hallmark anti-slop craft.
          </div>
        </div>

      </div>
    </footer>
  );
};
