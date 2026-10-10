import React, { useState } from 'react';
import { CodeBrainService } from '../services/codebrainService';
import { AgentDescriptor } from '../types/codebrain';
import { DotMatrixText } from './DotMatrixText';

export const AgentRosterSection: React.FC = () => {
  const agents: AgentDescriptor[] = CodeBrainService.getAgentRoster();
  const [selectedAgentId, setSelectedAgentId] = useState<string>(agents[0].id);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  return (
    <section id="agents" className="relative w-full py-12 md:py-16">
      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14">
        {/* Top Sheet Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <span className="meta-label">
            SHEET 05A // apps/ai_agents/* (AGENTS.MD ROSTER)
          </span>
          <span className="meta-label">
            05 DJANGO SUB-APPS + <span className="text-[#262523] font-medium">01 SHARED ORCHESTRATOR</span>
          </span>
        </div>

        {/* Dot-Matrix Section Title */}
        <div className="mb-6 overflow-x-auto pb-1">
          <DotMatrixText
            text="SIX DOMAIN AGENTS"
            pitch={5.0}
            dotRadius={1.95}
            showBed={false}
          />
        </div>

        <p className="text-[13px] sm:text-[14px] text-[#57554F] max-w-[820px] mb-8 leading-[1.7]">
          CodeBrain packages five specialized domain agents as dedicated Django sub-apps under{' '}
          <code className="text-[#262523] font-medium">apps/ai_agents/</code> (each with its own system prompts, Pydantic v2 validation schemas, views, and{' '}
          <code className="text-[#262523]">LLMServiceFactory</code> binding) and coordinates the Actor and Critic via the shared reflection orchestrator in{' '}
          <code className="text-[#262523] font-medium">apps/ai_agents/common/orchestrator.py</code>.
        </p>

        {/* Interactive Inter-Agent Collaboration Topology (AGENTS.md) */}
        <div className="border border-[#262523] bg-[#EAE7E0] p-5 mb-8 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#D5D2C9] pb-3">
            <span className="meta-label text-[#262523] font-semibold">
              INTER-AGENT COLLABORATION TOPOLOGY // CLICK ANY NODE TO INSPECT DATASHEET
            </span>
            <span className="meta-label text-[#B33920]">
              ACTIVE NODE: {selectedAgent.id.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-[11px]">
            {/* Track 01: Requirements & Reflection Loop */}
            <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-4 space-y-2.5">
              <div className="text-[10px] text-[#625F58] uppercase tracking-wider font-semibold">
                PIPELINE A // PRD TO CONVERGED SUITE
              </div>
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => setSelectedAgentId('prd_analyzer')}
                  className={`w-full text-left p-2.5 border cursor-pointer transition-colors ${
                    selectedAgentId === 'prd_analyzer'
                      ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                      : 'bg-[#EAE7E0] text-[#262523] border-[#D5D2C9] hover:border-[#262523]'
                  }`}
                >
                  <div
                    className={`text-[10px] font-semibold ${
                      selectedAgentId === 'prd_analyzer' ? 'text-[#D95338]' : 'text-[#B33920]'
                    }`}
                  >
                    01 // prd_analyzer
                  </div>
                  <div className="text-[11px]">.docx (pypandoc) / .md / .txt decomposition</div>
                </button>

                <div className="text-center text-[#B33920] font-bold text-[12px]">↓</div>

                <button
                  type="button"
                  onClick={() => setSelectedAgentId('orchestrator')}
                  className={`w-full text-left p-2.5 border cursor-pointer transition-colors ${
                    selectedAgentId === 'orchestrator'
                      ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                      : 'bg-[#EAE7E0] text-[#262523] border-[#D5D2C9] hover:border-[#262523]'
                  }`}
                >
                  <div
                    className={`text-[10px] font-semibold ${
                      selectedAgentId === 'orchestrator' ? 'text-[#D95338]' : 'text-[#B33920]'
                    }`}
                  >
                    02 // orchestrator (Shared Actor ⇄ Critic Loop)
                  </div>
                  <div className="text-[11px]">Bounded 2-pass reflection & monotonic guard</div>
                </button>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setSelectedAgentId('test_case_generator')}
                    className={`text-left p-2 border cursor-pointer transition-colors ${
                      selectedAgentId === 'test_case_generator'
                        ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                        : 'bg-[#EAE7E0] text-[#262523] border-[#D5D2C9] hover:border-[#262523]'
                    }`}
                  >
                    <div
                      className={`text-[9px] font-semibold ${
                        selectedAgentId === 'test_case_generator' ? 'text-[#D95338]' : 'text-[#B33920]'
                      }`}
                    >
                      ACTOR
                    </div>
                    <div className="text-[10px] font-medium truncate">test_case_generator</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedAgentId('test_case_reviewer')}
                    className={`text-left p-2 border cursor-pointer transition-colors ${
                      selectedAgentId === 'test_case_reviewer'
                        ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                        : 'bg-[#EAE7E0] text-[#262523] border-[#D5D2C9] hover:border-[#262523]'
                    }`}
                  >
                    <div
                      className={`text-[9px] font-semibold ${
                        selectedAgentId === 'test_case_reviewer' ? 'text-[#D95338]' : 'text-[#2A6F4E]'
                      }`}
                    >
                      CRITIC
                    </div>
                    <div className="text-[10px] font-medium truncate">test_case_reviewer</div>
                  </button>
                </div>
              </div>
            </div>

            {/* Track 02: API Contract & Closed-Loop Runner */}
            <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-4 flex flex-col justify-between space-y-2.5">
              <div className="space-y-2">
                <div className="text-[10px] text-[#625F58] uppercase tracking-wider font-semibold">
                  PIPELINE B // REST CONTRACT & HTTPX RUNNER
                </div>
                <div className="p-2.5 border border-[#D5D2C9] bg-[#EAE7E0]/60 text-[#57554F]">
                  <div className="text-[10px] text-[#262523] font-semibold">SPEC INGESTION</div>
                  <div>OpenAPI 3.x / Swagger 2.0 / Postman v2.1</div>
                </div>
                <div className="text-center text-[#B33920] font-bold text-[12px]">↓</div>
                <button
                  type="button"
                  onClick={() => setSelectedAgentId('iface_case_generator')}
                  className={`w-full text-left p-3 border cursor-pointer transition-colors ${
                    selectedAgentId === 'iface_case_generator'
                      ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                      : 'bg-[#EAE7E0] text-[#262523] border-[#D5D2C9] hover:border-[#262523]'
                  }`}
                >
                  <div
                    className={`text-[10px] font-semibold ${
                      selectedAgentId === 'iface_case_generator' ? 'text-[#D95338]' : 'text-[#B33920]'
                    }`}
                  >
                    05 // iface_case_generator
                  </div>
                  <div className="text-[11px] mt-0.5">
                    Synthesizes positive/boundary/negative assertions + executes via APITestRunner
                  </div>
                </button>
              </div>
              <div className="p-2 border border-[#2A6F4E] bg-[#EAE7E0] text-[10px] text-[#2A6F4E] font-medium">
                ✓ OUTPUTS: Live HTTPX Run · Pytest (.py) · Postman (.json)
              </div>
            </div>

            {/* Track 03: White-Box Source AST Analysis */}
            <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-4 flex flex-col justify-between space-y-2.5">
              <div className="space-y-2">
                <div className="text-[10px] text-[#625F58] uppercase tracking-wider font-semibold">
                  PIPELINE C // STATIC AST & WHITE-BOX QA
                </div>
                <div className="p-2.5 border border-[#D5D2C9] bg-[#EAE7E0]/60 text-[#57554F]">
                  <div className="text-[10px] text-[#262523] font-semibold">SOURCE CODE INPUT</div>
                  <div>Java Class / Method Declarations & AST</div>
                </div>
                <div className="text-center text-[#B33920] font-bold text-[12px]">↓</div>
                <button
                  type="button"
                  onClick={() => setSelectedAgentId('java_code_analyzer')}
                  className={`w-full text-left p-3 border cursor-pointer transition-colors ${
                    selectedAgentId === 'java_code_analyzer'
                      ? 'bg-[#262523] text-[#F2F0EC] border-[#262523]'
                      : 'bg-[#EAE7E0] text-[#262523] border-[#D5D2C9] hover:border-[#262523]'
                  }`}
                >
                  <div
                    className={`text-[10px] font-semibold ${
                      selectedAgentId === 'java_code_analyzer' ? 'text-[#D95338]' : 'text-[#B33920]'
                    }`}
                  >
                    06 // java_code_analyzer
                  </div>
                  <div className="text-[11px] mt-0.5">
                    Maps cyclomatic complexity hotspots, branch conditions & unhandled exception paths
                  </div>
                </button>
              </div>
              <div className="p-2 border border-[#D5D2C9] bg-[#EAE7E0] text-[10px] text-[#262523] font-medium">
                ✓ OUTPUTS: Branch Coverage Matrix & Exception Targets
              </div>
            </div>
          </div>
        </div>

        <div className="rule-heavy" />

        <div className="grid grid-cols-1 lg:grid-cols-12 border-b border-[#262523]">
          {/* Left Column: Numbered Agent Index */}
          <div className="lg:col-span-5 lg:border-r border-[#D5D2C9] divide-y divide-[#D5D2C9]">
            {agents.map((agent, idx) => {
              const isSelected = agent.id === selectedAgentId;
              const num = String(idx + 1).padStart(2, '0');
              return (
                <button
                  key={agent.id}
                  type="button"
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`w-full p-4 sm:p-5 text-left cursor-pointer transition-colors flex items-center justify-between gap-3 border-none ${
                    isSelected
                      ? 'bg-[#262523] text-[#F2F0EC]'
                      : 'bg-transparent text-[#262523] hover:bg-[#EAE7E0]'
                  }`}
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <span
                        className={`text-[12px] font-semibold ${
                          isSelected ? 'text-[#D95338]' : 'text-[#625F58]'
                        }`}
                      >
                        {num}
                      </span>
                      <span className="text-[14px] font-medium truncate">
                        {agent.name}
                      </span>
                    </div>
                    <div
                      className={`text-[11px] pl-7 truncate ${
                        isSelected ? 'text-[#F2F0EC]/75' : 'text-[#57554F]'
                      }`}
                    >
                      {agent.directory}
                    </div>
                  </div>
                  <span
                    className={`text-[11px] uppercase tracking-wider ${
                      isSelected ? 'text-[#D95338]' : 'text-[#625F58]'
                    }`}
                  >
                    →
                  </span>
                </button>
              );
            })}
          </div>

          {/* Right Column: Selected Agent Technical Datasheet */}
          <div className="lg:col-span-7 p-6 sm:p-8 bg-[#EAE7E0]/55 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#D5D2C9] pb-4">
                <div>
                  <div className="meta-label text-[#B33920] font-semibold">
                    {selectedAgent.role}
                  </div>
                  <h3 className="text-[22px] font-medium text-[#262523] mt-1">
                    {selectedAgent.name}
                  </h3>
                </div>
                <span className="text-[11px] uppercase tracking-[0.14em] px-2.5 py-1 border border-[#262523] text-[#262523] font-medium">
                  STATUS: {selectedAgent.status.toUpperCase()}
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="meta-label">ARCHITECTURAL RESPONSIBILITY</div>
                <p className="text-[13px] text-[#262523] leading-[1.7]">
                  {selectedAgent.responsibility}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-4 space-y-1">
                  <div className="meta-label text-[#B33920]">INPUT CONTRACT</div>
                  <div className="text-[12px] text-[#262523] leading-[1.5]">
                    {selectedAgent.input_format}
                  </div>
                </div>
                <div className="border border-[#D5D2C9] bg-[#F2F0EC] p-4 space-y-1">
                  <div className="meta-label text-[#2A6F4E]">OUTPUT ARTIFACT</div>
                  <div className="text-[12px] text-[#262523] leading-[1.5]">
                    {selectedAgent.output_format}
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2 pt-4 border-t border-[#D5D2C9]">
              <div className="meta-label">
                PRIMARY PYTHON ENTRYPOINTS // {selectedAgent.directory}
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedAgent.primary_methods.map((fn, i) => (
                  <code
                    key={i}
                    className="text-[11px] px-2.5 py-1 bg-[#F2F0EC] border border-[#D5D2C9] text-[#262523]"
                  >
                    {fn}
                  </code>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
