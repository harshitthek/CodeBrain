import React, { useState } from 'react';

interface NavbarProps {
  onRequestAccess: () => void;
  activeSection?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ onRequestAccess, activeSection = 'manifesto' }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollTo = (id: string) => {
    setMobileMenuOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-none w-full">
      <div className="max-w-[1280px] mx-auto px-6 md:px-10 h-24 flex items-center justify-between">
        {/* Brand Logo Lockup */}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          className="flex items-center gap-3 group text-decoration-none"
        >
          {/* Triangular brand icon with violet to deep verdant gradient */}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="transition-transform duration-300 group-hover:scale-110">
            <defs>
              <linearGradient id="navLogoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8052ff" />
                <stop offset="100%" stopColor="#15846e" />
              </linearGradient>
            </defs>
            <polygon points="12,2 22,20 2,20" fill="url(#navLogoGradient)" />
          </svg>
          <span className="text-white text-[17px] font-normal tracking-[-0.3px] select-none">
            Dala
          </span>
        </a>

        {/* Desktop Nav Items */}
        <nav className="hidden md:flex items-center gap-10">
          <button
            onClick={() => scrollTo('manifesto')}
            className={`ghost-link transition-colors ${activeSection === 'manifesto' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Manifesto
          </button>
          <button
            onClick={() => scrollTo('synthesis')}
            className={`ghost-link transition-colors ${activeSection === 'synthesis' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Intelligence
          </button>
          <button
            onClick={() => scrollTo('team')}
            className={`ghost-link transition-colors ${activeSection === 'team' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Team
          </button>
          <button
            onClick={() => scrollTo('blog')}
            className={`ghost-link transition-colors ${activeSection === 'blog' ? 'text-white' : 'text-[#9a9a9a]'}`}
          >
            Blog
          </button>
        </nav>

        {/* Right CTA */}
        <div className="flex items-center gap-4">
          <button
            onClick={onRequestAccess}
            className="btn-primary-pill"
          >
            Request Access
          </button>

          {/* Mobile hamburger toggle (clean minimal) */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-[#9a9a9a] hover:text-white p-2 focus:outline-none"
            aria-label="Toggle Menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
        <div className="md:hidden bg-black px-6 py-8 flex flex-col gap-6 border-none">
          <button
            onClick={() => scrollTo('manifesto')}
            className="ghost-link text-left text-lg text-white"
          >
            Manifesto
          </button>
          <button
            onClick={() => scrollTo('synthesis')}
            className="ghost-link text-left text-lg text-white"
          >
            Intelligence
          </button>
          <button
            onClick={() => scrollTo('team')}
            className="ghost-link text-left text-lg text-white"
          >
            Team
          </button>
          <button
            onClick={() => scrollTo('blog')}
            className="ghost-link text-left text-lg text-white"
          >
            Blog
          </button>
        </div>
      )}
    </header>
  );
};
