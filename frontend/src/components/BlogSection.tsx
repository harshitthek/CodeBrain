import React from 'react';

interface Article {
  date: string;
  category: string;
  title: string;
  summary: string;
  readTime: string;
}

const ARTICLES: Article[] = [
  {
    date: 'OCT 2026',
    category: 'DISTRIBUTED SYSTEMS',
    title: 'Why Hierarchical Knowledge Storage Fails Modern Engineering Orgs',
    summary: 'The failure of modern knowledge bases is topological: we store dynamic living code and decisions inside rigid linear hierarchies.',
    readTime: '6 MIN READ',
  },
  {
    date: 'SEP 2026',
    category: 'COGNITIVE ARCHITECTURE',
    title: 'Constellations of Context: Semantic Graph Traversal at Sub-100ms Latency',
    summary: 'How Dala indexes ASTs, Git commits, and Slack threads into a single continuous vector manifold without copying raw source data.',
    readTime: '9 MIN READ',
  },
  {
    date: 'AUG 2026',
    category: 'ENTERPRISE SECURITY',
    title: 'Zero-Leak Intelligence: Local Neural Projections Behind the Corporate Perimeter',
    summary: 'Designing cryptographic boundary guarantees so company knowledge stays entirely sovereign while powering company-wide reasoning.',
    readTime: '5 MIN READ',
  },
];

export const BlogSection: React.FC = () => {
  return (
    <section id="blog" className="relative w-full bg-black py-20 md:py-32 overflow-hidden">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        
        {/* Section Header */}
        <div className="mb-16">
          <span className="section-label">
            PERSPECTIVES
          </span>
          <h2 className="text-white text-[36px] sm:text-[42px] font-normal leading-[1.1] tracking-[-1.68px] mb-4">
            Dispatches from the void.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] max-w-[520px]">
            Explorations into distributed memory, neural compilation, and autonomous enterprise systems.
          </p>
        </div>

        {/* Article List: Floating directly on black void with whitespace alone, NO card borders */}
        <div className="space-y-16">
          {ARTICLES.map((article, index) => (
            <article
              key={index}
              className="group cursor-pointer flex flex-col md:flex-row md:items-baseline justify-between gap-6 pb-8 border-b border-white/[0.04] transition-colors"
            >
              <div className="md:w-1/4 flex flex-col gap-1">
                <span className="text-[#ffb829] text-[12px] uppercase font-semibold tracking-wider">
                  {article.category}
                </span>
                <span className="text-[#9a9a9a] text-[13px] font-[200]">
                  {article.date} · {article.readTime}
                </span>
              </div>

              <div className="md:w-3/4">
                <h3 className="text-white text-[24px] sm:text-[27px] font-normal tracking-[-0.48px] mb-3 group-hover:text-[#8052ff] transition-colors">
                  {article.title}
                </h3>
                <p className="text-[#bdbdbd] font-[200] text-[17px] leading-[1.6] max-w-[620px] mb-4">
                  {article.summary}
                </p>
                <span className="accent-link text-[13px]">
                  Read Essay →
                </span>
              </div>
            </article>
          ))}
        </div>

      </div>
    </section>
  );
};
