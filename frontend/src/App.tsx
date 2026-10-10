import React, { useState, useEffect } from 'react';
import { Navbar, SheetPageId, SHEET_PAGES } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { PipelineStudio } from './components/PipelineStudio';
import { APIRunnerSection } from './components/APIRunnerSection';
import { HybridRAGSection } from './components/HybridRAGSection';
import { AgentRosterSection } from './components/AgentRosterSection';
import { ArchitectureSection } from './components/ArchitectureSection';
import { Footer } from './components/Footer';
import { initSmoothScroll, destroySmoothScroll } from './utils/smoothScroll';

function parseHashToPage(): SheetPageId {
  if (typeof window === 'undefined') return 'hero';
  const raw = window.location.hash.replace(/^#\/?/, '').toLowerCase();
  if (raw === 'pipeline' || raw === 'orchestrator') return 'pipeline';
  if (raw === 'apirunner' || raw === 'httpx') return 'apirunner';
  if (raw === 'rag' || raw === 'hybrid-rag') return 'rag';
  if (raw === 'agents' || raw === 'architecture') return 'agents';
  return 'hero';
}

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<SheetPageId>(() => parseHashToPage());

  useEffect(() => {
    initSmoothScroll();

    const handleHashChange = () => {
      const next = parseHashToPage();
      setActivePage(next);
      window.scrollTo({ top: 0, behavior: 'auto' });
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => {
      window.removeEventListener('hashchange', handleHashChange);
      destroySmoothScroll();
    };
  }, []);

  const handleNavigate = (page: SheetPageId) => {
    setActivePage(page);
    if (typeof window !== 'undefined') {
      const nextHash = page === 'hero' ? '#hero' : `#${page}`;
      if (window.location.hash !== nextHash) {
        window.history.pushState(null, '', nextHash);
      }
      window.scrollTo({ top: 0, behavior: 'auto' });
    }
  };

  return (
    <div className="min-h-screen sheet-paper text-[#262523] relative flex flex-col">
      {/* Right-Margin Technical Schematic Trace Line (Interactive Sheet Station Nodes) */}
      <div
        className="hidden xl:block fixed top-[64px] bottom-[48px] right-[28px] w-[1px] bg-[#D5D2C9] z-40"
        aria-hidden="true"
      >
        {SHEET_PAGES.map((p, idx) => {
          const topPct = (idx / (SHEET_PAGES.length - 1)) * 100;
          const isCurrent = p.id === activePage;
          return (
            <button
              key={p.id}
              type="button"
              tabIndex={-1}
              onClick={() => handleNavigate(p.id)}
              title={`${p.num} ${p.label}`}
              style={{ top: `${topPct}%` }}
              className={`absolute -left-[5px] w-[11px] h-[11px] rounded-full border cursor-pointer p-0 flex items-center justify-center transition-colors ${
                isCurrent
                  ? 'border-[#262523] bg-[#F2F0EC]'
                  : 'border-[#625F58] bg-[#F2F0EC] hover:border-[#D95338]'
              }`}
            >
              {isCurrent && <span className="w-[4.5px] h-[4.5px] rounded-full bg-[#D95338]" />}
            </button>
          );
        })}
      </div>

      {/* Archival Sheet Index Bar (Switches between the 5 individual pages) */}
      <Navbar activePage={activePage} onNavigate={handleNavigate} />

      {/* Active Individual Page View */}
      <main className="flex-1 w-full relative z-10">
        {activePage === 'hero' && <HeroSection onNavigate={handleNavigate} />}

        {activePage === 'pipeline' && <PipelineStudio />}

        {activePage === 'apirunner' && <APIRunnerSection />}

        {activePage === 'rag' && <HybridRAGSection />}

        {activePage === 'agents' && (
          <>
            <AgentRosterSection />
            <ArchitectureSection />
          </>
        )}
      </main>

      {/* Sheet Pagination Bar & Colophon */}
      <Footer activePage={activePage} onNavigate={handleNavigate} />
    </div>
  );
};

export default App;
