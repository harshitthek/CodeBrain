import React from 'react';
import { ConstellationCanvas } from './ConstellationCanvas';

interface HeroSectionProps {
  onLaunchPipeline: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onLaunchPipeline }) => {
  return (
    <section className="relative w-full min-h-[92vh] flex items-center bg-black pt-28 pb-16 md:pt-36 md:pb-24 overflow-hidden">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Left Column: Typographic composition */}
          <div className="lg:col-span-7 flex flex-col items-start z-10">
            {/* Upper label in Saffron Spark */}
            <span className="section-label">
              L2/L3 AUTONOMOUS QUALITY ENGINEERING
            </span>

            {/* Display Headline: Weight 400, scale 78-113px, negative tracking */}
            <h1 className="text-white text-[48px] sm:text-[68px] md:text-[88px] lg:text-[102px] xl:text-[110px] font-normal leading-[1.05] tracking-[-2.2px] sm:tracking-[-3.4px] md:tracking-[-4.52px] mb-8 max-w-[760px]">
              Autonomous Quality Engineering on Black Velvet.
            </h1>

            {/* Body Copy: Weight 200 (ultra-light), 18px, max-width 520px */}
            <p className="text-white font-[200] text-[17px] md:text-[18px] leading-[1.6] max-w-[520px] mb-10">
              CodeBrain replaces manual QA friction with an Actor-Critic reflection loop. From messy PRDs to Pydantic-validated test suites, multi-criteria rubric audits, and closed-loop HTTPX execution with monotonic regression safeguards.
            </p>

            {/* Primary Action Button: Single violet pill */}
            <div className="flex flex-wrap items-center gap-6 mb-12">
              <button
                onClick={onLaunchPipeline}
                className="btn-primary-pill"
              >
                Launch Pipeline Studio
              </button>

              <a
                href="#architecture"
                className="ghost-link text-white hover:text-[#ffb829] transition-colors"
              >
                Explore Architecture ↓
              </a>
            </div>

            {/* Invariant Highlights floating on void */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-2 border-t border-white/[0.06] w-full max-w-[620px]">
              <div>
                <div className="text-white text-[24px] sm:text-[28px] font-normal tracking-[-0.8px]">
                  Actor ⇄ Critic
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-wider font-mono">
                  Reflection Loop
                </div>
              </div>

              <div>
                <div className="text-white text-[24px] sm:text-[28px] font-normal tracking-[-0.8px]">
                  Bound = 2
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-wider font-mono">
                  Strict Passes
                </div>
              </div>

              <div>
                <div className="text-white text-[24px] sm:text-[28px] font-normal tracking-[-0.8px]">
                  Zero-Docker
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-wider font-mono">
                  Hybrid RAG
                </div>
              </div>

              <div>
                <div className="text-white text-[24px] sm:text-[28px] font-normal tracking-[-0.8px]">
                  5+ TMS
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-wider font-mono">
                  Direct Exporters
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Signature brain particle constellation */}
          <div className="lg:col-span-5 flex items-center justify-center relative w-full">
            <ConstellationCanvas className="w-full" />
          </div>

        </div>
      </div>
    </section>
  );
};
