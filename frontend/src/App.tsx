import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { PipelineStudio } from './components/PipelineStudio';
import { AgentRosterSection } from './components/AgentRosterSection';
import { APIRunnerSection } from './components/APIRunnerSection';
import { ArchitectureSection } from './components/ArchitectureSection';
import { HybridRAGSection } from './components/HybridRAGSection';
import { Footer } from './components/Footer';

export const App: React.FC = () => {
  const [activeSection, setActiveSection] = useState('pipeline');

  useEffect(() => {
    const handleScroll = () => {
      const sections = ['pipeline', 'agents', 'apirunner', 'architecture', 'rag'];
      const scrollPosition = window.scrollY + 250;

      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const top = el.offsetTop;
          const height = el.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveSection(sectionId);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToPipeline = () => {
    const el = document.getElementById('pipeline');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-black text-white relative flex flex-col selection:bg-[#8052ff] selection:text-white">
      {/* Top Navigation */}
      <Navbar
        onLaunchPipeline={scrollToPipeline}
        activeSection={activeSection}
      />

      {/* Main Content Sections */}
      <main className="flex-1 w-full">
        {/* Hero Section with 3D Constellation Brain */}
        <HeroSection onLaunchPipeline={scrollToPipeline} />

        {/* Core Interactive Module: Autonomous Actor-Critic Reflection Studio */}
        <PipelineStudio />

        {/* Agent Roster Deep Dive */}
        <AgentRosterSection />

        {/* Closed-Loop Async HTTPX Runner */}
        <APIRunnerSection />

        {/* 4-Layer System Architecture & Invariants */}
        <ArchitectureSection />

        {/* Zero-Docker Hybrid RAG */}
        <HybridRAGSection />
      </main>

      {/* Footer */}
      <Footer onLaunchPipeline={scrollToPipeline} />
    </div>
  );
};

export default App;
