import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { ManifestoSection } from './components/ManifestoSection';
import { InteractiveDemoSection } from './components/InteractiveDemoSection';
import { TeamSection } from './components/TeamSection';
import { BlogSection } from './components/BlogSection';
import { Footer } from './components/Footer';
import { RequestAccessModal } from './components/RequestAccessModal';

export const App: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('manifesto');

  useEffect(() => {
    const handleScroll = () => {
      const sections = ['manifesto', 'synthesis', 'team', 'blog'];
      const scrollPosition = window.scrollY + 200;

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

  return (
    <div className="min-h-screen bg-black text-white relative flex flex-col selection:bg-[#8052ff] selection:text-white">
      {/* Top Navigation */}
      <Navbar
        onRequestAccess={() => setModalOpen(true)}
        activeSection={activeSection}
      />

      {/* Main Content Sections */}
      <main className="flex-1 w-full">
        {/* Hero Section with Constellation */}
        <HeroSection onRequestAccess={() => setModalOpen(true)} />

        {/* Section 2: The Manifesto */}
        <ManifestoSection />

        {/* Section 3: Autonomous Synthesis Demo */}
        <InteractiveDemoSection onRequestAccess={() => setModalOpen(true)} />

        {/* Section 4: Team Leadership Carousel */}
        <TeamSection />

        {/* Section 5: Perspectives & Blog */}
        <BlogSection />
      </main>

      {/* Footer */}
      <Footer onRequestAccess={() => setModalOpen(true)} />

      {/* Early Access Modal */}
      <RequestAccessModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
};

export default App;
