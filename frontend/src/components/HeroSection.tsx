import React from 'react';
import { ConstellationCanvas } from './ConstellationCanvas';

interface HeroSectionProps {
  onLaunchPipeline: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onLaunchPipeline }) => {
  return (
    <section className="relative w-full min-h-[94vh] flex items-center bg-black pt-32 pb-20 md:pt-44 md:pb-28 overflow-hidden">
      {/* Subtle atmospheric radial flare */}
      <div className="absolute top-1/4 right-1/4 w-[500px] h-[500px] bg-[#8052ff]/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-12 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-8 items-center">
          
          {/* Left Column: Monolithic Typographic Statement */}
          <div className="lg:col-span-7 flex flex-col items-start">
            
            {/* Amber section marker */}
            <span className="section-label">
              L2/L3 AUTONOMOUS QUALITY PLATFORM
            </span>

            {/* Display Headline: Weight 400, sculptural scale, negative tracking */}
            <h1 className="text-white text-[46px] sm:text-[68px] md:text-[84px] lg:text-[98px] xl:text-[108px] font-normal leading-[1.04] tracking-[-0.038em] mb-8 max-w-[760px]">
              Autonomous quality engineering on black velvet.
            </h1>

            {/* Body Copy: Ultra-light 200, airy line-height, Silver Mist */}
            <p className="text-[#bdbdbd] font-[200] text-[18px] md:text-[19px] leading-[1.7] max-w-[520px] mb-12">
              CodeBrain replaces brittle manual QA with an Actor-Critic reflection loop. From messy PRDs to Pydantic-validated test suites, multi-criteria rubric audits, and closed-loop HTTPX execution with monotonic regression safeguards.
            </p>

            {/* Primary Action Button: Saturated violet pill */}
            <div className="flex flex-wrap items-center gap-7 mb-16">
              <button
                onClick={onLaunchPipeline}
                className="btn-primary-pill"
              >
                Launch Auto-Pilot Studio <span>→</span>
              </button>

              <a
                href="#architecture"
                className="ghost-link hover:text-[#ffb829]"
              >
                Explore 4-Layer Architecture ↓
              </a>
            </div>

            {/* Pure Typographic Metrics Bar: Floating weightlessly with no boxes or borders */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 pt-6 border-t border-white/[0.07] w-full max-w-[620px]">
              <div>
                <div className="text-white text-[28px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1">
                  &lt;0.5s
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Reflection Loop
                </div>
              </div>

              <div>
                <div className="text-white text-[28px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1">
                  85%+
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Rubric Hurdle
                </div>
              </div>

              <div>
                <div className="text-white text-[28px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1">
                  Zero
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Docker Deps
                </div>
              </div>

              <div>
                <div className="text-white text-[28px] sm:text-[34px] font-normal tracking-[-0.03em] mb-1">
                  6
                </div>
                <div className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.12em] font-mono">
                  Domain Agents
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: Signature 3D brain particle constellation */}
          <div className="lg:col-span-5 flex items-center justify-center relative w-full">
            <ConstellationCanvas className="w-full" />
          </div>

        </div>
      </div>
    </section>
  );
};
