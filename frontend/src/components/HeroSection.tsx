import React from 'react';
import { ConstellationCanvas } from './ConstellationCanvas';

interface HeroSectionProps {
  onRequestAccess: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onRequestAccess }) => {
  return (
    <section className="relative w-full min-h-[92vh] flex items-center bg-black pt-28 pb-16 md:pt-36 md:pb-24 overflow-hidden">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Typographic composition */}
          <div className="lg:col-span-7 flex flex-col items-start z-10">
            {/* Upper label in Saffron Spark */}
            <span className="section-label">
              WORKPLACE INTELLIGENCE CORE
            </span>

            {/* Display Headline: Weight 400, scale 78-113px, negative tracking */}
            <h1 className="text-white text-[48px] sm:text-[68px] md:text-[88px] lg:text-[104px] xl:text-[113px] font-normal leading-[1.05] tracking-[-2.2px] sm:tracking-[-3.4px] md:tracking-[-4.52px] mb-8 max-w-[720px]">
              Your workplace has the answer. Just ask Dala for it.
            </h1>

            {/* Body Copy: Weight 200 (ultra-light), 18px, max-width 480px */}
            <p className="text-white font-[200] text-[17px] md:text-[18px] leading-[1.6] max-w-[480px] mb-10">
              Dala operates as a distributed intelligence layer across your organization's scattered context. Knowledge synthesized in real time, floating weightlessly without friction.
            </p>

            {/* Primary Action Button: Single violet pill */}
            <div className="flex items-center gap-6">
              <button
                onClick={onRequestAccess}
                className="btn-primary-pill"
              >
                Request Access
              </button>

              <a
                href="#manifesto"
                className="ghost-link text-white hover:text-[#ffb829] transition-colors"
              >
                Read Manifesto ↓
              </a>
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
