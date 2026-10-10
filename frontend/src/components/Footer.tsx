import React from 'react';

export const Footer: React.FC<{ onRequestAccess: () => void }> = ({ onRequestAccess }) => {
  return (
    <footer className="relative w-full bg-black py-20 border-t border-white/[0.04]">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        
        {/* Top footer row */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-10 pb-16">
          <div className="flex items-center gap-3">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <defs>
                <linearGradient id="footerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8052ff" />
                  <stop offset="100%" stopColor="#15846e" />
                </linearGradient>
              </defs>
              <polygon points="12,2 22,20 2,20" fill="url(#footerGrad)" />
            </svg>
            <span className="text-white text-[18px] font-normal tracking-tight">
              Dala
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-8 md:gap-12">
            <a href="#manifesto" className="ghost-link">
              Manifesto
            </a>
            <a href="#synthesis" className="ghost-link">
              Synthesis
            </a>
            <a href="#team" className="ghost-link">
              Team
            </a>
            <a href="#blog" className="ghost-link">
              Blog
            </a>
            <button
              onClick={onRequestAccess}
              className="accent-link text-[14px]"
            >
              Request Access →
            </button>
          </div>
        </div>

        {/* Bottom row: copyright & ethos */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-[#9a9a9a] text-[13px] font-[200]">
          <div>
            © {new Date().getFullYear()} Dala Technologies Inc. All rights reserved.
          </div>
          <div>
            Constellation floating on black velvet.
          </div>
        </div>

      </div>
    </footer>
  );
};
