import React, { useState } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { AgentDescriptor } from '../types/codebrain';

export const AgentRosterSection: React.FC = () => {
  const agents: AgentDescriptor[] = CodeBrainService.getAgentRoster();
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0].id);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  return (
    <section id="agents" className="relative w-full bg-black py-24 md:py-32 overflow-hidden border-t border-white/[0.06]">
      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12">
        
        {/* Section Header */}
        <div className="mb-14">
          <span className="section-label">
            AGENT & ORCHESTRATOR ROSTER
          </span>
          <h2 className="text-white text-[38px] sm:text-[52px] md:text-[64px] font-normal leading-[1.08] tracking-[-0.038em] mb-4">
            Surgical specialization.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] md:text-[19px] max-w-[580px] leading-[1.7]">
            Each agent operates as an isolated Django sub-app under <code className="text-white font-mono text-xs px-2 py-0.5 rounded bg-white/[0.06]">apps/ai_agents/</code>, containing Pydantic v2 schemas, prompt definitions, and specialized execution engines.
          </p>
        </div>

        {/* Two-Column Dossier Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-start">
          
          {/* Left Column: Interactive Agent Index */}
          <div className="lg:col-span-5 space-y-2">
            {agents.map((agent, index) => {
              const isSelected = agent.id === selectedAgentId;
              const formattedIndex = String(index + 1).padStart(2, '0');

              return (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`p-4 sm:p-5 rounded-[18px] cursor-pointer transition-all duration-300 border-l-2 ${
                    isSelected
                      ? 'border-[#8052ff] bg-white/[0.04] pl-6'
                      : 'border-transparent bg-transparent hover:bg-white/[0.02] pl-4 text-[#9a9a9a]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-[#8052ff] font-semibold">
                        {formattedIndex}
                      </span>
                      <span className={`text-[16px] font-normal ${isSelected ? 'text-white' : 'text-[#bdbdbd]'}`}>
                        {agent.name}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-mono uppercase tracking-[0.12em] px-2.5 py-0.5 rounded-full ${
                        isSelected
                          ? 'bg-[#8052ff]/20 text-[#8052ff] border border-[#8052ff]/30'
                          : 'text-[#9a9a9a]'
                      }`}
                    >
                      {agent.role.split(' ')[0]}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-[#9a9a9a] truncate font-[200] pl-7">
                    {agent.directory}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Column: Architectural Specification Sheet */}
          <div className="lg:col-span-7 glass-surface p-7 md:p-10 space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/[0.06]">
              <div>
                <span className="text-[#ffb829] text-[11px] uppercase font-mono tracking-[0.15em] block mb-1">
                  {selectedAgent.role}
                </span>
                <h3 className="text-white text-[26px] sm:text-[32px] font-normal tracking-[-0.02em]">
                  {selectedAgent.name}
                </h3>
              </div>
              <div className="text-[11px] font-mono text-[#15846e] px-3 py-1 rounded-full bg-[#15846e]/10 border border-[#15846e]/30 self-start">
                STATUS: L2/L3 AUTONOMOUS
              </div>
            </div>

            {/* Responsibility Statement */}
            <div>
              <div className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.12em] font-mono mb-2">
                Primary Architectural Responsibility
              </div>
              <p className="text-white font-[200] text-[17px] leading-[1.7]">
                {selectedAgent.responsibility}
              </p>
            </div>

            {/* In / Out Specs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2 font-mono text-xs">
              <div className="bg-black/60 p-5 rounded-[16px] border border-white/[0.06] space-y-2">
                <div className="text-[#ffb829] uppercase tracking-wider text-[10px]">Input Format:</div>
                <div className="text-[#bdbdbd] font-[200] leading-relaxed">
                  {selectedAgent.input_format}
                </div>
              </div>

              <div className="bg-black/60 p-5 rounded-[16px] border border-white/[0.06] space-y-2">
                <div className="text-[#8052ff] uppercase tracking-wider text-[10px]">Output Format:</div>
                <div className="text-[#bdbdbd] font-[200] leading-relaxed">
                  {selectedAgent.output_format}
                </div>
              </div>
            </div>

            {/* Sub-app Directory & Controller Specs */}
            <div className="space-y-3 pt-2">
              <div className="text-[#9a9a9a] text-[11px] uppercase tracking-[0.12em] font-mono">
                Sub-App Target Package
              </div>
              <div className="bg-black/70 p-4 rounded-[14px] border border-white/[0.06] flex items-center justify-between font-mono text-xs">
                <span className="text-white">{selectedAgent.directory}</span>
                <span className="text-[#15846e] text-[10px] uppercase">Pydantic v2 Validated</span>
              </div>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
