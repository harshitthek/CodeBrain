import React, { useState } from 'react';

interface TeamMember {
  name: string;
  role: string;
  photoUrl: string;
  twitter?: string;
  linkedin?: string;
}

const TEAM_MEMBERS: TeamMember[] = [
  {
    name: 'Joel Kang',
    role: 'CO FOUNDER & CTO',
    photoUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80',
    twitter: '#',
    linkedin: '#',
  },
  {
    name: 'Elena Rostova',
    role: 'CO FOUNDER & CEO',
    photoUrl: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=600&q=80',
    twitter: '#',
    linkedin: '#',
  },
  {
    name: 'Marcus Vance',
    role: 'HEAD OF RESEARCH',
    photoUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80',
    twitter: '#',
    linkedin: '#',
  },
  {
    name: 'Saffron Chen',
    role: 'PRINCIPAL ARCHITECT',
    photoUrl: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=600&q=80',
    twitter: '#',
    linkedin: '#',
  },
];

export const TeamSection: React.FC = () => {
  // Carousel slides of 2 members per slide or individual pagination
  const [activeSlide, setActiveSlide] = useState(0);
  const totalSlides = 2; // Slide 0: Joel & Elena, Slide 1: Marcus & Saffron

  const displayedMembers = TEAM_MEMBERS.slice(activeSlide * 2, activeSlide * 2 + 2);

  return (
    <section id="team" className="relative w-full bg-black py-20 md:py-32 overflow-hidden">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        
        {/* Section Header */}
        <div className="mb-16">
          <span className="section-label">
            LEADERSHIP & RESEARCH
          </span>
          <h2 className="text-white text-[42px] sm:text-[56px] md:text-[68px] lg:text-[78px] font-normal leading-[1.08] tracking-[-1.8px] sm:tracking-[-2.4px] md:tracking-[-3.12px] mb-4">
            Built by engineers from the frontier.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] max-w-[540px]">
            We come from distributed systems labs and deep learning research teams, united by a singular focus: making human work effortless through synthesized collective intelligence.
          </p>
        </div>

        {/* Team Members Grid / Carousel: Cards float on pure black void with whitespace alone */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 lg:gap-16">
          {displayedMembers.map((member) => (
            <div key={member.name} className="flex flex-col items-start group">
              {/* Large rounded-rectangle portrait photo (~24px corner radius, NO border, NO shadow) */}
              <div className="w-full aspect-[4/3] sm:aspect-[16/11] rounded-[24px] overflow-hidden mb-6 bg-black">
                <img
                  src={member.photoUrl}
                  alt={member.name}
                  className="w-full h-full object-cover object-center grayscale contrast-110 transition-transform duration-700 ease-out group-hover:scale-105"
                  loading="lazy"
                />
              </div>

              {/* Role label: 12px uppercase #8052ff */}
              <span className="text-[#8052ff] text-[12px] uppercase font-normal tracking-[0.05em] mb-2">
                {member.role}
              </span>

              {/* Name: 27px weight 400 #ffffff */}
              <div className="flex items-center justify-between w-full">
                <h3 className="text-white text-[27px] font-normal leading-tight">
                  {member.name}
                </h3>

                {/* Inline Social Glyphs in #9a9a9a */}
                <div className="flex items-center gap-3">
                  <a
                    href={member.twitter}
                    className="text-[#9a9a9a] hover:text-white transition-colors"
                    aria-label={`${member.name} on X`}
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                    </svg>
                  </a>
                  <a
                    href={member.linkedin}
                    className="text-[#9a9a9a] hover:text-white transition-colors"
                    aria-label={`${member.name} on LinkedIn`}
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Carousel Indicator: Two small dots ~8px, filled #8052ff for active position, 30px gap below */}
        <div className="flex items-center justify-center gap-3 mt-[30px]">
          {Array.from({ length: totalSlides }).map((_, index) => (
            <button
              key={index}
              onClick={() => setActiveSlide(index)}
              aria-label={`Go to slide ${index + 1}`}
              className={`w-[8px] h-[8px] rounded-full p-0 border-none transition-all duration-300 cursor-pointer ${
                activeSlide === index
                  ? 'bg-[#8052ff] scale-125'
                  : 'bg-[#9a9a9a]/40 hover:bg-[#9a9a9a]'
              }`}
            />
          ))}
        </div>

      </div>
    </section>
  );
};
