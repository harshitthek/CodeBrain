import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { PipelineStudio } from './components/PipelineStudio';
import { AgentRosterSection } from './components/AgentRosterSection';
import { APIRunnerSection } from './components/APIRunnerSection';
import { ArchitectureSection } from './components/ArchitectureSection';
import { HybridRAGSection } from './components/HybridRAGSection';
import { Footer } from './components/Footer';
import { initSmoothScroll, destroySmoothScroll, scrollToElement } from './utils/smoothScroll';

export const App: React.FC = () => {
  const [activeSection, setActiveSection] = useState('pipeline');

  useEffect(() => {
    // Initialize darkroomengineering/lenis smooth scroll physics
    initSmoothScroll();

    const handleScroll = () => {
      const sections = ['pipeline', 'agents', 'apirunner', 'architecture', 'rag'];
      const scrollPosition = window.scrollY + 280;

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
    return () => {
      window.removeEventListener('scroll', handleScroll);
      destroySmoothScroll();
    };
  }, []);

  const handleLaunchPipeline = () => {
    scrollToElement('pipeline');
  };

  return (
    <div className="min-h-screen bg-[#050507] text-[#f5f5f7] relative flex flex-col selection:bg-[#8052ff] selection:text-white bg-noise">
      {/* Deep Space Atmospheric Ambient Glow */}
      <div className="ambient-glow" />

      {/* Hallmark N5 Floating Pill Navigation */}
      <Navbar
        onLaunchPipeline={handleLaunchPipeline}
        activeSection={activeSection}
      />

      {/* Main Content Sections */}
      <main className="flex-1 w-full relative z-10">
        {/* Hallmark H2 Hero Section with 3D Constellation Brain */}
        <HeroSection onLaunchPipeline={handleLaunchPipeline} />

        {/* Hallmark Macrostructure 15: Split Studio Workbench */}
        <PipelineStudio />

        {/* Hallmark Segmented Architectural Dossier */}
        <AgentRosterSection />

        {/* Hallmark Diagnostic HTTPX Execution Workbench */}
        <APIRunnerSection />

        {/* 4-Layer System Architecture & Invariants */}
        <ArchitectureSection />

        {/* Zero-Docker Hybrid RAG Query Bench */}
        <HybridRAGSection />
      </main>

      {/* Hallmark Ft2 Inline Colophon Footer */}
      <Footer onLaunchPipeline={handleLaunchPipeline} />
    </div>
  );
};

export default App;
