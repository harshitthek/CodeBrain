import React from 'react';
import { DotMatrixText } from './DotMatrixText';
import { SheetPageId, SHEET_PAGES } from './Navbar';

interface FooterProps {
  activePage: SheetPageId;
  onNavigate: (page: SheetPageId) => void;
}

const AUTHORS = [
  {
    no: '01',
    matrix: 'HARSHIT',
    fullName: 'Harshit Sharma',
    handle: '@harshitthek',
    url: 'https://github.com/harshitthek',
    role: 'CORE ARCHITECTURE & AGENTS',
  },
  {
    no: '02',
    matrix: 'PERNAV',
    fullName: 'Pernav Jain',
    handle: '@here-2007',
    url: 'https://github.com/here-2007',
    role: 'PIPELINE & RAG SYSTEMS',
  },
  {
    no: '03',
    matrix: 'MRIDUL',
    fullName: 'Mridul Jain',
    handle: '@Mridulxjain',
    url: 'https://github.com/Mridulxjain',
    role: 'EXECUTION & INTEGRATIONS',
  },
];

export const Footer: React.FC<FooterProps> = ({ activePage, onNavigate }) => {
  const currentIdx = SHEET_PAGES.findIndex((p) => p.id === activePage);
  const prevSheet = currentIdx > 0 ? SHEET_PAGES[currentIdx - 1] : null;
  const nextSheet = currentIdx < SHEET_PAGES.length - 1 ? SHEET_PAGES[currentIdx + 1] : null;

  return (
    <footer className="relative w-full pt-10 pb-16 border-t border-[#262523] bg-[#F2F0EC]">
      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14">
        {/* Multi-Page Sheet Pagination Bar */}
        <div className="border border-[#262523] bg-[#EAE7E0] p-4 sm:p-5 mb-12 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div>
            {prevSheet ? (
              <button
                type="button"
                onClick={() => onNavigate(prevSheet.id)}
                className="btn-tech-outline text-[11px] py-2 px-4 w-full sm:w-auto justify-start"
              >
                <span>← PREV // {prevSheet.num} {prevSheet.label}</span>
              </button>
            ) : (
              <span className="meta-label text-[#625F58]">
                START OF TECHNICAL DATASHEET (SHEET 01)
              </span>
            )}
          </div>

          <nav aria-label="Sheet pagination" className="flex items-center justify-center gap-1.5">
            {SHEET_PAGES.map((p) => {
              const isCurrent = p.id === activePage;
              return (
                <button
                  key={p.id}
                  type="button"
                  aria-label={`Sheet ${p.num}: ${p.label}`}
                  aria-current={isCurrent ? 'page' : undefined}
                  onClick={() => onNavigate(p.id)}
                  className={`px-2.5 py-1 text-[10px] font-mono border cursor-pointer transition-colors ${
                    isCurrent
                      ? 'bg-[#262523] text-[#F2F0EC] border-[#262523] font-semibold'
                      : 'bg-[#F2F0EC] text-[#57554F] border-[#D5D2C9] hover:border-[#262523]'
                  }`}
                >
                  {p.num}
                </button>
              );
            })}
          </nav>

          <div className="text-right">
            {nextSheet ? (
              <button
                type="button"
                onClick={() => onNavigate(nextSheet.id)}
                className="btn-tech-vermilion text-[11px] py-2 px-4 w-full sm:w-auto justify-end"
              >
                <span>NEXT // {nextSheet.num} {nextSheet.label} →</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => onNavigate('hero')}
                className="btn-tech-outline text-[11px] py-2 px-4 w-full sm:w-auto justify-end"
              >
                <span>↺ RETURN TO 01 SHIPPED LEDGER</span>
              </button>
            )}
          </div>
        </div>

        {/* Top Metadata Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <span className="meta-label">
            COLOPHON // AUTHORS & CONTRIBUTORS (README.MD)
          </span>
          <span className="meta-label">
            LICENSE: <span className="text-[#262523] font-medium">MIT OPEN SOURCE</span>
          </span>
        </div>

        {/* Dot-Matrix Authors Headline */}
        <div className="mb-8 overflow-x-auto pb-1">
          <DotMatrixText
            text="BUILT BY"
            pitch={5.0}
            dotRadius={1.95}
            showBed={false}
          />
        </div>

        <div className="rule-heavy" />

        {/* Authors Ledger Rows */}
        <div className="divide-y divide-[#D5D2C9]">
          {AUTHORS.map((author) => (
            <a
              key={author.no}
              href={author.url}
              target="_blank"
              rel="noreferrer"
              className="grid grid-cols-12 gap-2 py-5 items-center no-underline hover:bg-[#EAE7E0]/60 transition-colors"
            >
              <div className="col-span-2 sm:col-span-1">
                <span className="text-[13px] text-[#625F58] font-medium">
                  {author.no}
                </span>
              </div>
              <div className="col-span-10 sm:col-span-5 overflow-x-auto">
                <DotMatrixText
                  text={author.matrix}
                  padToChars={9}
                  pitch={4.8}
                  dotRadius={1.85}
                  ghostRadius={0.95}
                  showBed={true}
                />
              </div>
              <div className="hidden sm:block sm:col-span-3">
                <div className="text-[13px] font-medium text-[#262523]">
                  {author.fullName}
                </div>
                <div className="text-[11px] text-[#625F58]">{author.role}</div>
              </div>
              <div className="hidden sm:block sm:col-span-3 text-right">
                <span className="meta-value text-[#B33920] hover:underline">
                  {author.handle} ↗
                </span>
              </div>
            </a>
          ))}
        </div>

        <div className="rule-heavy" />

        {/* Bottom Sheet Bar */}
        <div className="pt-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-6 flex-wrap">
            <span className="meta-label text-[#262523] font-medium">
              CODEBRAIN.EXE — ALL 04 PHASES MERGED
            </span>
            <a
              href="https://github.com/harshitthek/CodeBrain"
              target="_blank"
              rel="noreferrer"
              className="meta-label text-[#B33920] hover:underline no-underline"
            >
              [GITHUB REPOSITORY ↗]
            </a>
          </div>

          <div className="flex items-center gap-5">
            <button
              type="button"
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              className="meta-label hover:text-[#262523] bg-transparent border-none cursor-pointer p-0"
            >
              TOP ↑
            </button>
            <button
              type="button"
              onClick={() => onNavigate('pipeline')}
              className="meta-label text-[#B33920] hover:text-[#262523] bg-transparent border-none cursor-pointer p-0 font-semibold"
            >
              04 PHASES / 61 TESTS PASSED
            </button>

            {/* Reference Bullseye Target Termination Node (◉) */}
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="#262523" strokeWidth="1.2" />
              <circle cx="8" cy="8" r="2.2" fill="#D95338" />
            </svg>
          </div>
        </div>
      </div>
    </footer>
  );
};
