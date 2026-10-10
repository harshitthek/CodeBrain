import React, { useState } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { AgentDescriptor } from '../types/codebrain';

export const AgentRosterSection: React.FC = () => {
  const agents: AgentDescriptor[] = CodeBrainService.getAgentRoster();
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0].id);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  return (
    <section id="agents" className="relative w-full bg-transparent py-24 md:py-32 overflow-hidden border-t border-white/[0.06]">
      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12">
        
        {/* Section Header */}
        <div className="mb-14">
          <span className="section-label">
            AGENT & ORCHESTRATOR ROSTER
          </span>
          <h2 className="text-[#f5f5f7] text-[36px] sm:text-[46px] md:text-[54px] font-normal leading-[1.08] tracking-[-0.038em] mb-4">
            Surgical specialization.
          </h2>
          <p className="text-[#c2c2cb] font-[200] text-[18px] md:text-[19px] max-w-[620px] leading-[1.7]">
            Each agent operates as an isolated Django sub-app under <code className="text-white font-mono text-xs px-2 py-0.5 rounded bg-white/[0.06]">apps/ai_agents/</code>, containing Pydantic v2 schemas, prompt definitions, and specialized execution engines.
          </p>
        </div>

        {/* Two-Column Dossier Layout (Hallmark: No side-stripes, hairline borders) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-start">
          
          {/* Left Column: Interactive Agent Index (lg:col-span-5) */}
          <div className="lg:col-span-5 space-y-2">
            {agents.map((agent, index) => {
              const isSelected = agent.id === selectedAgentId;
              const formattedIndex = String(index + 1).padStart(2, '0');

              return (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`p-4 sm:p-4.5 rounded-[16px] cursor-pointer transition-all duration-200 border ${
                    isSelected
                      ? 'border-white/[0.18] bg-white/[0.05] shadow-[0_4px_24px_rgba(0,0,0,0.4)]'
                      : 'border-transparent bg-transparent hover:bg-white/[0.02] text-[#8e8e98]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-[#8052ff] font-semibold">
                        {formattedIndex}
                      </span>
                      <span className={`text-[15px] font-normal ${isSelected ? 'text-white' : 'text-[#c2c2cb]'}`}>
                        {agent.name}
                      </span>
                    </div>

                    <span
                      className={`text-[10px] font-mono uppercase tracking-[0.1em] px-2 py-0.5 rounded-full ${
                        isSelected
                          ? 'bg-[#8052ff]/20 text-[#8052ff] border border-[#8052ff]/30'
                          : 'text-[#8e8e98] bg-white/[0.03]'
                      }`}
                    >
                      {agent.role.split(' ')[0]}
                    </span>
                  </div>

                  <div className="text-xs font-mono text-[#8e8e98] truncate font-[200] pl-7">
                    {agent.directory}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Column: Architectural Specification Sheet (lg:col-span-7) */}
          <div className="lg:col-span-7 workbench-surface p-7 md:p-9 space-y-7">
            
            {/* Header row */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-white/[0.06]">
              <div>
                <span className="text-[#ffb829] text-[11px] uppercase font-mono tracking-[0.15em] block mb-1">
                  {selectedAgent.role}
                </span>
                <h3 className="text-white text-[24px] sm:text-[28px] font-normal tracking-[-0.02em]">
                  {selectedAgent.name}
                </h3>
              </div>
              <div className="text-[10px] font-mono text-[#15846e] px-3 py-1 rounded-full bg-[#15846e]/10 border border-[#15846e]/30 self-start">
                STATUS: L2/L3 AUTONOMOUS
              </div>
            </div>

            {/* Responsibility Statement */}
            <div className="space-y-1.5">
              <div className="text-[#8e8e98] text-[11px] uppercase tracking-[0.12em] font-mono">
                Primary Architectural Responsibility
              </div>
              <p className="text-[#f5f5f7] font-[200] text-[16px] leading-[1.7]">
                {selectedAgent.responsibility}
              </p>
            </div>

            {/* In / Out Specs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1 font-mono text-xs">
              <div className="bg-black/60 p-4 rounded-[14px] border border-white/[0.05] space-y-1.5">
                <div className="text-[#ffb829] uppercase tracking-wider text-[10px]">Input Format:</div>
                <div className="text-[#c2c2cb] font-[200] leading-relaxed text-[11px]">
                  {selectedAgent.input_format}
                </div>
              </div>

              <div className="bg-black/60 p-4 rounded-[14px] border border-white/[0.05] space-y-1.5">
                <div className="text-[#8052ff] uppercase tracking-wider text-[10px]">Output Format:</div>
                <div className="text-[#c2c2cb] font-[200] leading-relaxed text-[11px]">
                  {selectedAgent.output_format}
                </div>
              </div>
            </div>

            {/* Target Package & Execution Interface */}
            <div className="space-y-2 pt-1 font-mono text-xs">
              <div className="text-[#8e8e98] text-[10px] uppercase tracking-wider">
                Module Interface:
              </div>
              <div className="bg-black/70 p-3.5 rounded-[12px] border border-white/[0.06] flex items-center justify-between">
                <span className="text-white text-[11px] truncate">{selectedAgent.directory}</span>
                <span className="text-[#15846e] text-[10px] uppercase pl-2">Pydantic v2 Validated</span>
              </div>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
