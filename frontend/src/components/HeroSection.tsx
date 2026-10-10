import React from 'react';
import { ConstellationCanvas } from './ConstellationCanvas';
import { scrollToElement } from '../utils/smoothScroll';

interface HeroSectionProps {
  onLaunchPipeline: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onLaunchPipeline }) => {
  return (
    <section id="hero" className="relative w-full min-h-[92vh] flex items-center bg-transparent pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
      {/* Subtle atmospheric radial flare */}
      <div className="absolute top-1/4 right-1/4 w-[540px] h-[540px] bg-[#8052ff]/8 rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Left Column: Hallmark H2 Monolithic Typographic Statement */}
          <div className="lg:col-span-7 flex flex-col items-start pt-2">
            
            {/* Saffron section marker */}
            <span className="section-label">
              L2/L3 AUTONOMOUS QUALITY PLATFORM
            </span>

            {/* Display Headline: Weight 400, Roman purity, sculptural scale */}
            <h1 className="text-[#f5f5f7] text-[34px] sm:text-[44px] md:text-[50px] lg:text-[54px] xl:text-[58px] font-normal leading-[1.08] tracking-[-0.038em] mb-7 max-w-[720px]">
              Autonomous quality engineering.
              <br />
              <span className="text-[#8e8e98]">Self-healing on black velvet.</span>
            </h1>

            {/* Body Copy: Ultra-light 200, Silver Mist, comfortable line-height */}
            <p className="text-[#c2c2cb] font-[200] text-[18px] md:text-[19px] leading-[1.7] max-w-[540px] mb-10">
              CodeBrain replaces brittle manual QA with an autonomous Actor-Critic reflection loop. From ambiguous PRDs to Pydantic-validated test suites, multi-criteria rubric audits, and closed-loop HTTPX execution with monotonic regression safeguards.
            </p>

            {/* Primary Action Button & Architectural Link */}
            <div className="flex flex-wrap items-center gap-6 mb-14">
              <button
                onClick={() => {
                  onLaunchPipeline();
                  scrollToElement('pipeline');
                }}
                className="btn-primary-pill"
              >
                Launch Studio Workbench <span>→</span>
              </button>

              <button
                onClick={() => scrollToElement('architecture')}
                className="ghost-link hover:text-[#ffb829] py-2"
              >
                4-Layer Architecture ↓
              </button>
            </div>

            {/* Pure Typographic Metrics Bar: Data-led, weightless, zero box enclosures */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 pt-8 border-t border-white/[0.07] w-full max-w-[620px]">
              <div>
                <div className="text-[#f5f5f7] text-[30px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1 font-mono">
                  &lt;0.5s
                </div>
                <div className="text-[#8e8e98] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Reflection Loop
                </div>
              </div>

              <div>
                <div className="text-[#f5f5f7] text-[30px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1 font-mono">
                  85%+
                </div>
                <div className="text-[#8e8e98] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Rubric Hurdle
                </div>
              </div>

              <div>
                <div className="text-[#f5f5f7] text-[30px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1 font-mono">
                  Zero
                </div>
                <div className="text-[#8e8e98] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Docker Deps
                </div>
              </div>

              <div>
                <div className="text-[#f5f5f7] text-[30px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1 font-mono">
                  6
                </div>
                <div className="text-[#8e8e98] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Domain Agents
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: Signature 3D brain particle constellation with Lenis velocity sync */}
          <div className="lg:col-span-5 flex items-center justify-center relative w-full">
            <ConstellationCanvas className="w-full" />
          </div>

        </div>
      </div>
    </section>
  );
};
