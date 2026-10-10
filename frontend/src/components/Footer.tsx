import React from 'react';

interface FooterProps {
  onLaunchPipeline: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onLaunchPipeline }) => {
  return (
    <footer className="relative w-full bg-black py-20 border-t border-white/[0.04]">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        
        {/* Top footer row */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-10 pb-16">
          <div className="flex items-center gap-3">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <defs>
                <linearGradient id="footerGradCB" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8052ff" />
                  <stop offset="100%" stopColor="#15846e" />
                </linearGradient>
              </defs>
              <polygon points="12,2 22,20 2,20" fill="url(#footerGradCB)" />
            </svg>
            <div className="flex flex-col">
              <span className="text-white text-[18px] font-normal tracking-tight">
                CodeBrain
              </span>
              <span className="text-[#9a9a9a] text-[11px] font-mono tracking-wider">
                Autonomous Quality Platform
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-8 md:gap-10">
            <a href="#pipeline" className="ghost-link">
              Pipeline Studio
            </a>
            <a href="#agents" className="ghost-link">
              Agent Roster
            </a>
            <a href="#apirunner" className="ghost-link">
              HTTPX Runner
            </a>
            <a href="#architecture" className="ghost-link">
              Architecture
            </a>
            <a href="#rag" className="ghost-link">
              Hybrid RAG
            </a>
            <button
              onClick={onLaunchPipeline}
              className="accent-link text-[14px]"
            >
              Launch Auto-Pilot →
            </button>
          </div>
        </div>

        {/* Bottom row: copyright & ethos */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-[#9a9a9a] text-[13px] font-[200]">
          <div>
            © {new Date().getFullYear()} CodeBrain. Autonomous AI Quality Engineering Platform.
          </div>
          <div className="font-mono text-xs text-[#9a9a9a]">
            Constellation floating on black velvet. Zero-Docker RAG.
          </div>
        </div>

      </div>
    </footer>
  );
};
