import React, { useState } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { AgentDescriptor } from '../types/codebrain';

export const AgentRosterSection: React.FC = () => {
  const agents: AgentDescriptor[] = CodeBrainService.getAgentRoster();
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0].id);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  return (
    <section id="agents" className="relative w-full bg-black py-20 md:py-32 overflow-hidden border-t border-white/[0.04]">
      <div className="max-w-[1280px] w-full mx-auto px-6 md:px-10">
        
        {/* Section Header */}
        <div className="mb-16">
          <span className="section-label">
            AGENT & ORCHESTRATOR ROSTER
          </span>
          <h2 className="text-white text-[38px] sm:text-[54px] md:text-[68px] lg:text-[78px] font-normal leading-[1.08] tracking-[-1.8px] sm:tracking-[-2.6px] md:tracking-[-3.12px] mb-4">
            Surgical specialization.
          </h2>
          <p className="text-[#bdbdbd] font-[200] text-[18px] max-w-[580px]">
            Each agent operates as an isolated domain app under <code className="text-white font-mono text-sm">apps/ai_agents/</code>, containing Pydantic v2 schemas, prompt definitions, and specialized execution engines.
          </p>
        </div>

        {/* Two-Column Interactive Roster */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          
          {/* Left Column: Agent Selection List */}
          <div className="lg:col-span-5 space-y-3">
            {agents.map((agent) => {
              const isSelected = agent.id === selectedAgentId;

              return (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`p-5 rounded-[20px] cursor-pointer transition-all duration-200 border-none ${
                    isSelected
                      ? 'bg-white/[0.06] text-white'
                      : 'bg-transparent text-[#9a9a9a] hover:bg-white/[0.02] hover:text-white'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[17px] font-normal text-white">
                      {agent.name}
                    </span>
                    <span
                      className={`text-[11px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        isSelected ? 'bg-[#8052ff] text-white' : 'text-[#9a9a9a]'
                      }`}
                    >
                      {agent.role.split(' ')[0]}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-[#9a9a9a] truncate">
                    {agent.directory}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Column: Deep-dive Agent Inspection Card */}
          <div className="lg:col-span-7 bg-white/[0.02] rounded-[24px] p-8 md:p-10 border border-white/[0.06] space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/[0.06]">
              <div>
                <span className="text-[#ffb829] text-[12px] uppercase font-semibold font-mono tracking-wider block mb-1">
                  {selectedAgent.role}
                </span>
                <h3 className="text-white text-[28px] sm:text-[32px] font-normal">
                  {selectedAgent.name}
                </h3>
              </div>
              <div className="text-xs font-mono text-[#15846e] px-3 py-1 rounded-full bg-[#15846e]/10 self-start">
                STATUS: L2/L3 AUTONOMOUS
              </div>
            </div>

            {/* Responsibility */}
            <div>
              <div className="text-[#9a9a9a] text-[12px] uppercase tracking-wider font-mono mb-2">
                Primary Architectural Responsibility
              </div>
              <p className="text-white font-[200] text-[17px] leading-[1.6]">
                {selectedAgent.responsibility}
              </p>
            </div>

            {/* In / Out Specs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2 font-mono text-xs">
              <div className="bg-black/60 p-5 rounded-[16px] border border-white/[0.04]">
                <div className="text-[#ffb829] uppercase mb-2">Input Format:</div>
                <div className="text-[#bdbdbd] font-[200] leading-relaxed">
                  {selectedAgent.input_format}
                </div>
              </div>

              <div className="bg-black/60 p-5 rounded-[16px] border border-white/[0.04]">
                <div className="text-[#8052ff] uppercase mb-2">Output Format:</div>
                <div className="text-[#bdbdbd] font-[200] leading-relaxed">
                  {selectedAgent.output_format}
                </div>
              </div>
            </div>

            {/* Key Methods */}
            <div>
              <div className="text-[#9a9a9a] text-[12px] uppercase tracking-wider font-mono mb-3">
                Core Controllers & Execution Methods
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedAgent.primary_methods.map((method, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 rounded-[9999px] bg-white/[0.04] text-[#bdbdbd] text-xs font-mono"
                  >
                    {method}
                  </span>
                ))}
              </div>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
