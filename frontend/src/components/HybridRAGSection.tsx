import React, { useState } from 'react';

interface RAGDoc {
  id: string;
  title: string;
  snippet: string;
  source: string;
  bm25_rank: number;
  vector_rank: number;
  rrf_score: number;
}

const SAMPLE_KNOWLEDGE: Record<string, RAGDoc[]> = {
  webhook: [
    {
      id: 'doc-1',
      title: 'Payment Gateway Integration Spec & Webhook Handlers',
      snippet: 'Stripe webhook listener must compute HMAC-SHA256 signature using internal secret and verify against X-Signature header before order mutation.',
      source: 'specs/payments/v2_webhook_spec.md',
      bm25_rank: 1,
      vector_rank: 2,
      rrf_score: 0.0328,
    },
    {
      id: 'doc-2',
      title: 'Incident Postmortem: Payment Gateway Spike Starvation',
      snippet: 'Database connection pool exhaustion caused webhook response latency >5000ms. Solved by increasing pool headroom and circuit breaking.',
      source: 'postmortems/2026-10-06-webhook-timeout.md',
      bm25_rank: 2,
      vector_rank: 1,
      rrf_score: 0.0328,
    },
    {
      id: 'doc-3',
      title: 'Idempotency Key Verification in Distributed Transactions',
      snippet: 'Ensure all incoming payment transition events record unique idempotency keys in Redis cache with 24-hour expiration TTL.',
      source: 'architecture/idempotency_patterns.md',
      bm25_rank: 3,
      vector_rank: 4,
      rrf_score: 0.0308,
    },
  ],
  oauth: [
    {
      id: 'doc-4',
      title: 'OAuth2 PKCE RFC-7636 Authorization Flow',
      snippet: 'Clients generate high-entropy code_verifier and code_challenge S256 hash. Authorization code is single-use and expires after 60 seconds.',
      source: 'security/oauth2_pkce_architecture.md',
      bm25_rank: 1,
      vector_rank: 1,
      rrf_score: 0.0333,
    },
    {
      id: 'doc-5',
      title: 'Refresh Token Family Revocation & Replay Mitigation',
      snippet: 'If a compromised or stale refresh token is presented, the entire lineage of issued tokens is revoked immediately.',
      source: 'security/token_rotation_guidelines.md',
      bm25_rank: 2,
      vector_rank: 2,
      rrf_score: 0.0323,
    },
  ],
  consensus: [
    {
      id: 'doc-6',
      title: 'Raft Quorum Election & Heartbeat Timing Constraints',
      snippet: 'Leader broadcasts empty AppendEntries RPC every 150-300ms. Quorum requires strict majority N/2 + 1 to elect new term leader.',
      source: 'consensus/raft_specification.md',
      bm25_rank: 1,
      vector_rank: 1,
      rrf_score: 0.0333,
    },
  ],
};

export const HybridRAGSection: React.FC = () => {
  const [activeQueryKey, setActiveQueryKey] = useState<string>('webhook');
  const results = SAMPLE_KNOWLEDGE[activeQueryKey] || SAMPLE_KNOWLEDGE.webhook;

  return (
    <section id="rag" className="relative w-full bg-transparent py-24 md:py-32 overflow-hidden border-t border-white/[0.06]">
      <div className="max-w-[1240px] w-full mx-auto px-6 md:px-12">
        
        {/* Section Header */}
        <div className="mb-14">
          <span className="section-label">
            ZERO-DOCKER HYBRID RETRIEVAL (RAG)
          </span>
          <h2 className="text-[#f5f5f7] text-[36px] sm:text-[46px] md:text-[54px] font-normal leading-[1.08] tracking-[-0.038em] mb-4">
            Lexical BM25 meets semantic dense fusion.
          </h2>
          <p className="text-[#c2c2cb] font-[200] text-[18px] md:text-[19px] max-w-[620px] leading-[1.7]">
            Combines pure-Python <code className="text-white font-mono text-xs px-2 py-0.5 rounded bg-white/[0.06]">PureBM25Index</code> with local SQLite Chroma embeddings via Reciprocal Rank Fusion (RRF), running locally with zero Docker overhead.
          </p>
        </div>

        {/* Interactive Query Bench */}
        <div className="space-y-6 max-w-[1040px]">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-[#8e8e98] text-xs font-mono uppercase tracking-wider">
              Query Bench:
            </span>
            {[
              { key: 'webhook', label: '"Payment gateway webhook signature & timeout"' },
              { key: 'oauth', label: '"OAuth2 PKCE token family replay mitigation"' },
              { key: 'consensus', label: '"Raft quorum majority heartbeat timing"' },
            ].map((q) => (
              <button
                key={q.key}
                type="button"
                onClick={() => setActiveQueryKey(q.key)}
                className={`text-xs px-3.5 py-1.5 rounded-full border cursor-pointer transition-all font-mono ${
                  activeQueryKey === q.key
                    ? 'bg-[#8052ff] text-white font-medium border-[#8052ff] shadow-[0_0_16px_rgba(128,82,255,0.4)]'
                    : 'bg-white/[0.03] text-[#8e8e98] border-white/[0.06] hover:text-white'
                }`}
              >
                {q.label}
              </button>
            ))}
          </div>

          {/* RRF Results Grid */}
          <div className="space-y-3.5">
            {results.map((doc) => (
              <div
                key={doc.id}
                className="workbench-surface p-6 space-y-2.5"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                  <span className="text-white text-[17px] sm:text-[18px] font-normal">
                    {doc.title}
                  </span>
                  <div className="flex items-center gap-2.5 text-xs font-mono">
                    <span className="text-[#ffb829] bg-[#ffb829]/10 px-2.5 py-0.5 rounded-full border border-[#ffb829]/20 text-[11px]">
                      BM25 #{doc.bm25_rank}
                    </span>
                    <span className="text-[#8052ff] bg-[#8052ff]/10 px-2.5 py-0.5 rounded-full border border-[#8052ff]/20 text-[11px]">
                      Vector #{doc.vector_rank}
                    </span>
                    <span className="text-[#15846e] font-semibold text-[11px]">
                      RRF: {doc.rrf_score.toFixed(4)}
                    </span>
                  </div>
                </div>

                <p className="text-[#c2c2cb] font-[200] text-[14px] leading-relaxed">
                  {doc.snippet}
                </p>

                <div className="text-[11px] font-mono text-[#8e8e98] pt-0.5">
                  Source: <span className="text-white/80">{doc.source}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="text-xs font-mono text-[#8e8e98] pt-1">
            Formula: <code className="text-[#ffb829]">RRF_Score(d) = Σ [ 1 / (60 + Rank(d)) ]</code> across BM25 lexical & Dense SQLite embeddings.
          </div>
        </div>

      </div>
    </section>
  );
};
