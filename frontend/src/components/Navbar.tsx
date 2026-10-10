import React from 'react';

export type SheetPageId = 'hero' | 'pipeline' | 'apirunner' | 'rag' | 'agents';

interface NavbarProps {
  activePage: SheetPageId;
  onNavigate: (page: SheetPageId) => void;
}

export const SHEET_PAGES: Array<{
  id: SheetPageId;
  num: string;
  label: string;
  shortTitle: string;
  moduleRef: string;
}> = [
  {
    id: 'hero',
    num: '01',
    label: 'SHIPPED LEDGER',
    shortTitle: 'Overview & Shipped Subsystems',
    moduleRef: 'README.MD · PHASES.MD',
  },
  {
    id: 'pipeline',
    num: '02',
    label: 'ORCHESTRATOR',
    shortTitle: 'Actor-Critic Reflection Loop',
    moduleRef: 'apps/ai_agents/common/orchestrator.py',
  },
  {
    id: 'apirunner',
    num: '03',
    label: 'HTTPX RUNNER',
    shortTitle: 'Closed-Loop HTTPX & SSRF Guard',
    moduleRef: 'apps/ai_agents/iface_case_generator/runner.py',
  },
  {
    id: 'rag',
    num: '04',
    label: 'HYBRID RAG',
    shortTitle: 'Zero-Docker SQLite RAG & Parsers',
    moduleRef: 'apps/knowledge/hybrid_retriever.py',
  },
  {
    id: 'agents',
    num: '05',
    label: 'AGENTS & ARCH',
    shortTitle: '6-Agent Roster & 4-Layer Stack',
    moduleRef: 'AGENTS.MD · ARCHITECTURE.MD',
  },
];

export const Navbar: React.FC<NavbarProps> = ({ activePage, onNavigate }) => {
  const currentMeta =
    SHEET_PAGES.find((p) => p.id === activePage) || SHEET_PAGES[0];

  return (
    <header className="sticky top-0 z-50 bg-[#F2F0EC]/95 backdrop-blur-[2px] border-b border-[#D5D2C9]">
      {/* Top Archival Sheet Binding Strip */}
      <div className="w-full h-[10px] bg-[#262523]" />

      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14 h-[54px] flex items-center justify-between gap-4">
        {/* Left: Brand Classification */}
        <button
          type="button"
          onClick={() => onNavigate('hero')}
          className="flex items-center gap-3 bg-transparent border-none p-0 cursor-pointer text-left group"
        >
          <span className="meta-label text-[#262523] font-medium tracking-[0.18em] group-hover:text-[#D95338] transition-colors">
            CODEBRAIN / OPEN SOURCE QA
          </span>
        </button>

        {/* Center: 5 Individual Page Tabs */}
        <nav className="hidden lg:flex items-center gap-1">
          {SHEET_PAGES.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.id)}
                className={`cursor-pointer px-3 py-1.5 text-[11px] tracking-[0.14em] uppercase transition-colors flex items-center gap-1.5 border ${
                  isActive
                    ? 'bg-[#262523] text-[#F2F0EC] border-[#262523] font-semibold'
                    : 'bg-transparent text-[#87847C] border-transparent hover:text-[#262523] hover:border-[#D5D2C9]'
                }`}
              >
                <span className={isActive ? 'text-[#D95338]' : 'text-[#87847C]'}>
                  {item.num}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right: Active Sheet Indicator + Datum Crosshair */}
        <div className="flex items-center gap-4">
          {activePage !== 'pipeline' && (
            <button
              type="button"
              onClick={() => onNavigate('pipeline')}
              className="hidden sm:inline-flex text-[11px] tracking-[0.15em] uppercase text-[#D95338] hover:text-[#262523] bg-transparent border-none cursor-pointer font-medium"
            >
              [RUN SUITE →]
            </button>
          )}

          <span className="meta-label">
            SHEET {currentMeta.num} / 05
          </span>

          {/* Top-Right Circular Crosshair Node */}
          <div
            className="w-[24px] h-[24px] flex items-center justify-center"
            title={`Sheet ${currentMeta.num}: ${currentMeta.shortTitle}`}
          >
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <circle
                cx="11"
                cy="11"
                r="9.5"
                stroke="#262523"
                strokeWidth="1.2"
              />
              <line
                x1="7.5"
                y1="7.5"
                x2="14.5"
                y2="14.5"
                stroke="#262523"
                strokeWidth="1.2"
              />
              <line
                x1="14.5"
                y1="7.5"
                x2="7.5"
                y2="14.5"
                stroke="#262523"
                strokeWidth="1.2"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Mobile / Tablet Page Switcher Strip */}
      <div className="lg:hidden border-t border-[#D5D2C9] bg-[#EAE7E0]/70 overflow-x-auto">
        <div className="max-w-[1180px] mx-auto px-5 flex items-center gap-1 py-1.5">
          {SHEET_PAGES.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.id)}
                className={`cursor-pointer px-2.5 py-1 text-[10px] tracking-[0.12em] uppercase whitespace-nowrap border ${
                  isActive
                    ? 'bg-[#262523] text-[#F2F0EC] border-[#262523] font-semibold'
                    : 'bg-transparent text-[#57554F] border-transparent'
                }`}
              >
                <span className="text-[#D95338] mr-1">{item.num}</span>
                {item.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
