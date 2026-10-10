import React, { useState, useMemo } from 'react';
import { DotMatrixText } from './DotMatrixText';

interface KnowledgeChunk {
  id: string;
  title: string;
  snippet: string;
  source: string;
  category: string;
  keywords: string[];
  semanticConcepts: string[];
  baseVectorRank: number;
}

const CORPUS_CHUNKS: KnowledgeChunk[] = [
  {
    id: 'CHUNK-01',
    title: 'Stripe Webhook HMAC-SHA256 Verification & Idempotency Contract',
    snippet:
      'Webhook listener computes HMAC-SHA256 digest over raw request body using internal secret and verifies X-Signature header before transitioning order state from PENDING to PAID.',
    source: 'specs/payments/v2_webhook_spec.md',
    category: 'PRD / SPEC',
    keywords: ['payment', 'webhook', 'stripe', 'hmac', 'signature', 'x-signature', 'idempotent', 'checkout'],
    semanticConcepts: ['billing', 'order', 'paid', 'digest', 'secret', 'callback', 'fulfillment', 'payment'],
    baseVectorRank: 1,
  },
  {
    id: 'CHUNK-02',
    title: 'Payment Gateway Timeout (>5000ms) & Circuit Breaker State Machine',
    snippet:
      'Under downstream payment gateway latency exceeding 5000ms, circuit breaker transitions from CLOSED to OPEN after 3 consecutive timeouts and queues orders to delayed retry topic.',
    source: 'postmortems/webhook_timeout_circuit_breaker.md',
    category: 'POSTMORTEM',
    keywords: ['payment', 'timeout', '5000ms', 'circuit', 'breaker', 'retry', 'gateway', 'webhook'],
    semanticConcepts: ['latency', 'resilience', 'fault', 'fallback', 'degraded', 'queue', 'backoff', 'timeout'],
    baseVectorRank: 2,
  },
  {
    id: 'CHUNK-03',
    title: 'OAuth2 PKCE S256 Code Challenge & Token Family Revocation',
    snippet:
      'POST /oauth/token exchanges SHA-256 code_verifier for 60m access_token and 30d refresh_token. Presenting a previously rotated refresh token revokes the entire token family lineage.',
    source: 'security/oauth2_pkce_rfc7636.md',
    category: 'SECURITY SPEC',
    keywords: ['oauth', 'oauth2', 'pkce', 's256', 'token', 'refresh', 'replay', 'code_verifier', 'lineage'],
    semanticConcepts: ['auth', 'authentication', 'jwt', 'session', 'identity', 'revocation', 'security', 'pkce'],
    baseVectorRank: 3,
  },
  {
    id: 'CHUNK-04',
    title: 'Raft Consensus Quorum (N/2 + 1) & Election Jitter Bounds',
    snippet:
      'Leader broadcasts AppendEntries heartbeat every 150-300ms. Follower increments term and requests votes on timeout; minority partitions reject writes with ERR_QUORUM_UNREACHABLE.',
    source: 'consensus/raft_quorum_spec.md',
    category: 'DISTRIBUTED SPEC',
    keywords: ['raft', 'quorum', 'leader', 'election', 'heartbeat', 'majority', 'partition', 'appendentries'],
    semanticConcepts: ['cluster', 'consensus', 'distributed', 'node', 'follower', 'candidate', 'split', 'quorum'],
    baseVectorRank: 4,
  },
  {
    id: 'CHUNK-05',
    title: 'OpenAPI 3.x / Swagger 2.0 Circular $ref Resolution & Postman v2.1 Parser',
    snippet:
      'openapi_parser.py resolves internal #/components/schemas/ pointers with visited-set cycle detection; postman_parser.py recursively flattens nested folder item trees.',
    source: 'apps/knowledge/openapi_parser.py',
    category: 'PARSER ENGINE',
    keywords: ['openapi', 'swagger', 'postman', 'ref', '$ref', 'cycle', 'schema', 'parser'],
    semanticConcepts: ['contract', 'specification', 'ingestion', 'endpoint', 'folder', 'circular', 'json', 'openapi'],
    baseVectorRank: 5,
  },
];

const PRESET_QUERIES = [
  { key: 'webhook', label: 'payment webhook hmac signature timeout', query: 'payment webhook hmac signature timeout' },
  { key: 'oauth', label: 'oauth2 pkce s256 token replay lineage', query: 'oauth2 pkce s256 token replay lineage' },
  { key: 'raft', label: 'raft quorum majority heartbeat partition', query: 'raft quorum majority heartbeat partition' },
  { key: 'openapi', label: 'openapi swagger $ref cycle postman parser', query: 'openapi swagger $ref cycle postman parser' },
];

const PARSER_SAMPLES = {
  openapi: {
    label: 'OPENAPI 3.0 (CIRCULAR $REF)',
    module: 'apps/knowledge/openapi_parser.py',
    raw: `{
  "openapi": "3.0.3",
  "info": { "title": "Payment & Order Graph API", "version": "2.4.0" },
  "paths": {
    "/api/v1/orders/{orderId}": {
      "post": {
        "summary": "Create child replacement order",
        "parameters": [{ "name": "orderId", "in": "path", "required": true }],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/OrderNode" }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "OrderNode": {
        "type": "object",
        "required": ["id", "amount_cents"],
        "properties": {
          "id": { "type": "string" },
          "amount_cents": { "type": "integer" },
          "parent_order": { "$ref": "#/components/schemas/OrderNode" }
        }
      }
    }
  }
}`,
    normalized: `{
  "parser": "OpenAPISpecParser.parse_dict()",
  "cycle_guard_triggered": true,
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/v1/orders/{orderId}",
      "summary": "Create child replacement order",
      "parameters": [
        { "name": "orderId", "in": "path", "required": true }
      ],
      "resolved_body_schema": {
        "type": "object",
        "required": ["id", "amount_cents"],
        "properties": {
          "id": { "type": "string" },
          "amount_cents": { "type": "integer" },
          "parent_order": {
            "$circular_ref": "#/components/schemas/OrderNode (visited-set guard)"
          }
        }
      }
    }
  ]
}`,
  },
  postman: {
    label: 'POSTMAN COLLECTION V2.1',
    module: 'apps/knowledge/postman_parser.py',
    raw: `{
  "info": {
    "name": "Enterprise Checkout Collection",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "v1 / Orders Folder",
      "item": [
        {
          "name": "Submit Order Checkout",
          "request": {
            "method": "POST",
            "header": [
              { "key": "X-Idempotency-Key", "value": "{{$guid}}" }
            ],
            "url": {
              "raw": "{{base_url}}/api/v1/orders/checkout?region=us-east"
            },
            "body": {
              "mode": "raw",
              "raw": "{\\"cart_id\\": \\"cart_991\\", \\"currency\\": \\"USD\\"}"
            }
          }
        }
      ]
    }
  ]
}`,
    normalized: `{
  "parser": "PostmanCollectionParser.parse_dict()",
  "folder_depth_flattened": 2,
  "endpoints": [
    {
      "folder_breadcrumb": "v1 / Orders Folder",
      "name": "Submit Order Checkout",
      "method": "POST",
      "path": "/api/v1/orders/checkout",
      "query_params": [{ "key": "region", "value": "us-east" }],
      "headers": [{ "key": "X-Idempotency-Key", "value": "{{$guid}}" }],
      "body_fields": ["cart_id", "currency"]
    }
  ]
}`,
  },
};

export const HybridRAGSection: React.FC = () => {
  const [queryText, setQueryText] = useState<string>(PRESET_QUERIES[0].query);
  const [activeParserTab, setActiveParserTab] = useState<'openapi' | 'postman'>('openapi');

  const queryTokens = useMemo(
    () =>
      queryText
        .toLowerCase()
        .split(/[^a-z0-9_$]+/)
        .filter(Boolean),
    [queryText]
  );

  const rankedResults = useMemo(() => {
    // Fixed-weight lexical demonstration stream + independent semantic concept stream
    const scored = CORPUS_CHUNKS.map((chunk) => {
      const haystack = `${chunk.title} ${chunk.snippet} ${chunk.source} ${chunk.keywords.join(' ')}`.toLowerCase();
      const semanticField = `${chunk.category} ${chunk.semanticConcepts.join(' ')} ${chunk.title}`.toLowerCase();
      let lexicalScore = 0;
      let vectorScore = 0;
      const matchedKeywords: string[] = [];

      for (const tok of queryTokens) {
        if (chunk.keywords.includes(tok)) {
          lexicalScore += 3.2;
          if (!matchedKeywords.includes(tok)) matchedKeywords.push(tok);
        }
        if (haystack.includes(tok)) {
          lexicalScore += 1.5;
          if (!matchedKeywords.includes(tok)) matchedKeywords.push(tok);
        }
        // Independent semantic concept & prefix affinity for the simulated vector stream
        if (chunk.semanticConcepts.includes(tok)) {
          vectorScore += 4.0;
        } else if (
          tok.length >= 3 &&
          chunk.semanticConcepts.some((c) => c.startsWith(tok.slice(0, 4)) || tok.startsWith(c.slice(0, 4)))
        ) {
          vectorScore += 2.6;
        } else if (semanticField.includes(tok)) {
          vectorScore += 1.8;
        }
      }
      return {
        ...chunk,
        lexicalScore,
        vectorScore,
        matchedKeywords,
      };
    });

    const byBm25 = [...scored].sort((a, b) => b.lexicalScore - a.lexicalScore || a.baseVectorRank - b.baseVectorRank);
    const bm25RankMap = new Map<string, number>();
    byBm25.forEach((item, idx) => bm25RankMap.set(item.id, idx + 1));

    const byVector = [...scored].sort((a, b) => b.vectorScore - a.vectorScore || a.baseVectorRank - b.baseVectorRank);
    const vectorRankMap = new Map<string, number>();
    byVector.forEach((item, idx) => vectorRankMap.set(item.id, idx + 1));

    const rrfK = 60;
    return scored
      .map((chunk) => {
        const bm25_rank = bm25RankMap.get(chunk.id) || 5;
        const vector_rank = vectorRankMap.get(chunk.id) || 5;
        const bm25_contrib = 1 / (rrfK + bm25_rank);
        const vector_contrib = 1 / (rrfK + vector_rank);
        const rrf_score = bm25_contrib + vector_contrib;
        return {
          ...chunk,
          bm25_rank,
          vector_rank,
          bm25_contrib,
          vector_contrib,
          rrf_score,
        };
      })
      .sort((a, b) => b.rrf_score - a.rrf_score);
  }, [queryTokens]);

  return (
    <section id="rag" className="relative w-full py-12 md:py-16">
      <div className="max-w-[1180px] mx-auto px-5 sm:px-10 md:px-14">
        {/* Top Sheet Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <span className="meta-label">
            SHEET 04 // apps/knowledge/hybrid_retriever.py · chroma_store.py · openapi_parser.py
          </span>
          <span className="meta-label">
            INVARIANT 03: <span className="text-[#262523] font-medium">SQLITE 384-DIM VECTORS</span> · LEXICAL + DENSE RRF (K=60)
          </span>
        </div>

        {/* Dot-Matrix Section Title */}
        <div className="mb-6 overflow-x-auto pb-1">
          <DotMatrixText
            text="ZERO-DOCKER RAG"
            pitch={5.0}
            dotRadius={1.95}
            showBed={false}
          />
        </div>

        <p className="text-[13px] sm:text-[14px] text-[#57554F] max-w-[820px] mb-8 leading-[1.7]">
          In the Python backend, <code className="text-[#262523] font-medium">HybridRetriever</code> combines dense cosine similarity from{' '}
          <code className="text-[#262523]">PersistentSQLiteVectorStore</code> (<code className="text-[#262523]">chroma_db/chroma_vectors.sqlite3</code>) with lexical token matching using Reciprocal Rank Fusion:{' '}
          <code className="text-[#B33920] font-medium">RRF(d) = 1/(60 + rank_dense) + 1/(60 + rank_lexical)</code>. The interactive bench below demonstrates this dual-stream RRF ranking using client-side lexical-match and semantic-concept streams.
        </p>

        <div className="rule-heavy" />

        {/* Query Bar & Preset Buttons */}
        <div className="py-6 border-b border-[#D5D2C9] space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
            <label
              htmlFor="hybrid-rrf-query-input"
              className="lg:col-span-3 meta-label text-[#262523] font-medium cursor-pointer"
            >
              HYBRID RRF QUERY BENCH:
            </label>
            <div className="lg:col-span-9">
              <input
                id="hybrid-rrf-query-input"
                type="text"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                placeholder="Enter API path, error code, or specification query..."
                className="w-full bg-[#EAE7E0] text-[#262523] text-[13px] p-3 border border-[#262523] focus:outline-none font-mono"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="meta-label mr-2">PRESET QUERIES:</span>
            {PRESET_QUERIES.map((pq, idx) => (
              <button
                key={pq.key}
                type="button"
                onClick={() => setQueryText(pq.query)}
                className={`btn-tech-outline text-[10px] py-1.5 px-3 ${
                  queryText === pq.query ? 'active' : ''
                }`}
              >
                0{idx + 1} // {pq.label}
              </button>
            ))}
          </div>
        </div>

        {/* RRF Table Header */}
        <div className="grid grid-cols-12 gap-2 py-3 border-b border-[#D5D2C9] meta-label">
          <div className="col-span-2 sm:col-span-1">RANK</div>
          <div className="col-span-10 sm:col-span-6">DOCUMENT CHUNK, MATCHED TOKENS & SOURCE</div>
          <div className="hidden sm:block sm:col-span-2 text-right">LEXICAL / VEC DEMO</div>
          <div className="hidden sm:block sm:col-span-3 text-right">RRF FUSION SCORE (K=60)</div>
        </div>

        {/* Ranked Knowledge Chunks */}
        <div className="divide-y divide-[#D5D2C9] border-b border-[#262523]">
          {rankedResults.map((doc, idx) => {
            const maxRrf = 2 / 61; // ~0.0327868
            const bm25Pct = Math.min(50, (doc.bm25_contrib / maxRrf) * 100);
            const vecPct = Math.min(50, (doc.vector_contrib / maxRrf) * 100);

            return (
              <div
                key={doc.id}
                className="grid grid-cols-12 gap-2 py-5 items-start hover:bg-[#EAE7E0]/50 transition-colors"
              >
                <div className="col-span-2 sm:col-span-1">
                  <span
                    className={`text-[13px] font-semibold ${
                      idx === 0 ? 'text-[#B33920]' : 'text-[#625F58]'
                    }`}
                  >
                    0{idx + 1}
                  </span>
                </div>

                <div className="col-span-10 sm:col-span-6 space-y-2 pr-4">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[14px] font-medium text-[#262523]">
                      {doc.title}
                    </span>
                    <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 bg-[#EAE7E0] border border-[#D5D2C9] text-[#57554F]">
                      {doc.category}
                    </span>
                  </div>
                  <p className="text-[12px] text-[#57554F] leading-[1.6]">
                    {doc.snippet}
                  </p>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#625F58]">
                    <span>
                      SOURCE: <code className="text-[#262523]">{doc.source}</code>
                    </span>
                    {doc.matchedKeywords.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1">
                        <span className="text-[10px] uppercase text-[#B33920] ml-1">MATCHED:</span>
                        {doc.matchedKeywords.map((kw) => (
                          <span
                            key={kw}
                            className="px-1.5 py-0.2 bg-[#262523] text-[#F2F0EC] text-[10px]"
                          >
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="hidden sm:block sm:col-span-2 text-right space-y-1">
                  <div className="meta-value text-[12px]">
                    LEX #{doc.bm25_rank} · VEC #{doc.vector_rank}
                  </div>
                  <div className="text-[10px] text-[#625F58]">
                    {doc.bm25_contrib.toFixed(4)} + {doc.vector_contrib.toFixed(4)}
                  </div>
                </div>

                <div className="hidden sm:flex sm:col-span-3 flex-col items-end space-y-1.5">
                  <span
                    className={`text-[13px] font-semibold ${
                      idx === 0 ? 'text-[#B33920]' : 'text-[#2A6F4E]'
                    }`}
                  >
                    {doc.rrf_score.toFixed(5)}
                  </span>
                  {/* Dual-Stream RRF Contribution Bar */}
                  <div className="w-36 h-2 bg-[#EAE7E0] border border-[#D5D2C9] flex overflow-hidden">
                    <div
                      style={{ width: `${bm25Pct}%` }}
                      className="bg-[#D95338] h-full"
                      title={`Lexical match contribution: ${doc.bm25_contrib.toFixed(5)}`}
                    />
                    <div
                      style={{ width: `${vecPct}%` }}
                      className="bg-[#262523] h-full"
                      title={`Semantic vector demo contribution: ${doc.vector_contrib.toFixed(5)}`}
                    />
                  </div>
                  <div className="text-[9px] text-[#625F58] uppercase tracking-wider">
                    <span className="text-[#B33920]">■ LEXICAL DEMO</span> · <span className="text-[#262523]">■ VECTOR DEMO</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* ====================================================================
            SUB-SHEET 04B: INTERACTIVE OPENAPI 3.X ($REF) & POSTMAN V2.1 PARSER LAB
            ==================================================================== */}
        <div className="pt-14">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <span className="meta-label">
              SHEET 04B // apps/knowledge/openapi_parser.py · postman_parser.py
            </span>
            <span className="meta-label">
              CYCLE SAFETY: <span className="text-[#262523] font-medium">VISITED-SET $REF RESOLUTION</span> · RECURSIVE FOLDER TREE
            </span>
          </div>

          <div className="border border-[#262523] bg-[#EAE7E0] p-5 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D5D2C9] pb-3">
              <div>
                <div className="meta-label text-[#262523] font-semibold">
                  SPECIFICATION INGESTION & NORMALIZATION LAB
                </div>
                <p className="text-[11px] text-[#57554F] mt-0.5">
                  Inspect how CodeBrain resolves circular OpenAPI <code>$ref</code> pointers without infinite recursion and flattens nested Postman v2.1 folders.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setActiveParserTab('openapi')}
                  className={`btn-tech-outline text-[10px] py-1.5 px-3 ${
                    activeParserTab === 'openapi' ? 'active' : ''
                  }`}
                >
                  01 // OPENAPI 3.0 ($REF CYCLE)
                </button>
                <button
                  type="button"
                  onClick={() => setActiveParserTab('postman')}
                  className={`btn-tech-outline text-[10px] py-1.5 px-3 ${
                    activeParserTab === 'postman' ? 'active' : ''
                  }`}
                >
                  02 // POSTMAN V2.1 TREE
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="meta-label text-[#262523] font-semibold">
                    RAW UPLOADED SPEC ({PARSER_SAMPLES[activeParserTab].label})
                  </span>
                  <code className="text-[#625F58] text-[10px]">INPUT PAYLOAD</code>
                </div>
                <pre className="bg-[#F2F0EC] border border-[#D5D2C9] p-4 text-[11px] text-[#262523] overflow-x-auto max-h-[300px] leading-[1.55]">
                  {PARSER_SAMPLES[activeParserTab].raw}
                </pre>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="meta-label text-[#2A6F4E] font-semibold">
                    NORMALIZED CONTRACT OUTPUT
                  </span>
                  <code className="text-[#B33920] text-[10px]">
                    {PARSER_SAMPLES[activeParserTab].module}
                  </code>
                </div>
                <pre className="bg-[#F2F0EC] border border-[#D5D2C9] p-4 text-[11px] text-[#262523] overflow-x-auto max-h-[300px] leading-[1.55]">
                  {PARSER_SAMPLES[activeParserTab].normalized}
                </pre>
              </div>
            </div>
          </div>
        </div>

        {/* ====================================================================
            SUB-SHEET 04C: ZERO-DOCKER SQLITE VECTOR STORE VS MILVUS 2.X
            ==================================================================== */}
        <div className="pt-10">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="border border-[#262523] bg-[#EAE7E0] p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="meta-label text-[#2A6F4E] font-semibold">
                  DEFAULT // ZERO-DOCKER EMBEDDED ENGINE
                </span>
                <code className="text-[11px] text-[#262523]">chroma_store.py</code>
              </div>
              <div className="text-[15px] font-medium text-[#262523]">
                PersistentSQLiteVectorStore (384-Dim)
              </div>
              <p className="text-[12px] text-[#57554F] leading-[1.6]">
                Persists 384-dimensional embeddings (<code>all-MiniLM-L6-v2</code> with deterministic SHA-256 fallback) directly inside <code>chroma_db/chroma_vectors.sqlite3</code>. Requires zero Docker containers or external daemons.
              </p>
            </div>

            <div className="border border-[#D5D2C9] bg-[#EAE7E0]/60 p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="meta-label text-[#625F58]">
                  OPTIONAL // DISTRIBUTED CLUSTER ENGINE
                </span>
                <code className="text-[11px] text-[#57554F]">vector_store.py</code>
              </div>
              <div className="text-[15px] font-medium text-[#262523]">
                Milvus 2.x Vector Database (Port 19530)
              </div>
              <p className="text-[12px] text-[#57554F] leading-[1.6]">
                For multi-million chunk enterprise deployments, CodeBrain supports connecting to a distributed Milvus 2.x cluster via <code>MILVUS_HOST</code> and <code>MILVUS_PORT</code> while retaining the same <code>HybridRetriever</code> RRF interface.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
