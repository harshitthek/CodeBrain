import React, { useState, useEffect } from 'react';

export const ManifestoSection: React.FC = () => {
  const [activeNode, setActiveNode] = useState(0);

  const NODES = [
    { label: 'Pull Requests & Commits', type: 'code', color: '#8052ff' },
    { label: 'Technical Specs & RFCs', type: 'doc', color: '#ffb829' },
    { label: 'Incident Postmortems', type: 'incident', color: '#15846e' },
    { label: 'Slack & Team Discussions', type: 'chat', color: '#ec4899' },
    { label: 'Architecture Decisions', type: 'adr', color: '#38bdf8' },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveNode((prev) => (prev + 1) % NODES.length);
    }, 2800);
    return () => clearInterval(timer);
  }, [NODES.length]);

  return (
    <section id="manifesto" className="relative w-full bg-black py-20 md:py-32 overflow-hidden">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        {/* Asymmetric Alternating Two-Column: Visual Left, Text Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-12 items-center">
          
          {/* Left Column: Visual representation of distributed knowledge */}
          <div className="lg:col-span-6 relative flex flex-col items-center justify-center min-h-[420px] md:min-h-[480px]">
            {/* Minimalist interactive synaptic node field */}
            <div className="relative w-full max-w-[460px] aspect-square flex items-center justify-center">
              {/* Outer orbit rings without border boxes */}
              <div className="absolute inset-0 rounded-full border border-white/[0.04] animate-pulse" />
              <div className="absolute inset-8 rounded-full border border-white/[0.03]" />
              <div className="absolute inset-20 rounded-full border border-white/[0.02]" />

              {/* Central Nucleus Node */}
              <div className="relative z-20 flex flex-col items-center justify-center">
                <div className="w-20 h-20 rounded-full bg-black flex items-center justify-center relative">
                  {/* Subtle pulsing glow in Electric Iris */}
                  <div className="absolute inset-0 rounded-full bg-[#8052ff] opacity-20 blur-xl animate-pulse" />
                  <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
                    <defs>
                      <linearGradient id="nucleusGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#8052ff" />
                        <stop offset="100%" stopColor="#ffb829" />
                      </linearGradient>
                    </defs>
                    <polygon points="12,3 21,19 3,19" fill="url(#nucleusGrad)" />
                  </svg>
                </div>
                <span className="text-white text-xs tracking-[0.2em] uppercase mt-3 font-semibold">
                  SYNAPTIC CORE
                </span>
              </div>

              {/* Orbital Nodes floating on black void */}
              {NODES.map((node, i) => {
                const total = NODES.length;
                const angle = (i * (2 * Math.PI)) / total - Math.PI / 2;
                const radius = 160; // orbital radius
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;
                const isActive = activeNode === i;

                return (
                  <div
                    key={node.label}
                    style={{
                      transform: `translate(${x}px, ${y}px)`,
                    }}
                    onClick={() => setActiveNode(i)}
                    className="absolute cursor-pointer transition-all duration-500 flex flex-col items-center group z-30"
                  >
                    {/* Tiny outlined triangle marker */}
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300"
                      style={{
                        backgroundColor: isActive ? '#000000' : 'transparent',
                      }}
                    >
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <polygon
                          points="8,2 14,14 2,14"
                          stroke={node.color}
                          strokeWidth={isActive ? '2' : '1.2'}
                          fill={isActive ? node.color : 'transparent'}
                        />
                      </svg>
                    </div>

                    <span
                      className={`text-[12px] uppercase tracking-[0.05em] mt-2 whitespace-nowrap transition-colors duration-300 select-none ${
                        isActive ? 'text-white font-semibold' : 'text-[#9a9a9a] font-normal'
                      }`}
                    >
                      {node.label}
                    </span>
                  </div>
                );
              })}

              {/* Synaptic beam connecting active node to core */}
              {(() => {
                const angle = (activeNode * (2 * Math.PI)) / NODES.length - Math.PI / 2;
                const x2 = Math.cos(angle) * 160;
                const y2 = Math.sin(angle) * 160;
                return (
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox="-230 -230 460 460"
                  >
                    <line
                      x1="0"
                      y1="0"
                      x2={x2}
                      y2={y2}
                      stroke={NODES[activeNode].color}
                      strokeWidth="1.5"
                      strokeDasharray="4 4"
                      className="transition-all duration-500 opacity-60"
                    />
                  </svg>
                );
              })()}
            </div>
          </div>

          {/* Right Column: Monolithic headline + ultra-light body */}
          <div className="lg:col-span-6 flex flex-col items-start">
            <span className="section-label">
              THE MANIFESTO
            </span>

            {/* Headline at 78px, weight 400, negative tracking */}
            <h2 className="text-white text-[42px] sm:text-[60px] md:text-[72px] lg:text-[78px] font-normal leading-[1.08] tracking-[-1.8px] sm:tracking-[-2.6px] md:tracking-[-3.12px] mb-8">
              Unlock collective wisdom.
            </h2>

            {/* Body Copy: Weight 200, 18px, Silver Mist */}
            <div className="space-y-6 max-w-[520px]">
              <p className="text-[#bdbdbd] font-[200] text-[17px] md:text-[18px] leading-[1.6]">
                Modern companies operate across fragmented tools: unindexed PR discussions, orphaned architecture notes, buried incident postmortems, and isolated communications.
              </p>
              <p className="text-[#bdbdbd] font-[200] text-[17px] md:text-[18px] leading-[1.6]">
                Dala dissolves these silos. It visualizes and indexes enterprise context as a living, interconnected constellation of intelligence. When you ask a question, you are not querying a search box — you are querying your company's collective brain.
              </p>
            </div>

            {/* Accent link in Saffron Spark */}
            <div className="mt-10">
              <a href="#synthesis" className="accent-link group">
                <span>Explore the synthesis architecture</span>
                <span className="transition-transform duration-200 group-hover:translate-x-1">→</span>
              </a>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};
