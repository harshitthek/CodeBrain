export type Priority = 'p0' | 'p1' | 'p2' | 'p3';
export type ReviewStatus = 'pending' | 'approved' | 'rejected';

export interface TestCaseItem {
  id: string;
  title: string;
  description: string;
  requirements?: string;
  code_snippet?: string;
  test_steps: string[];
  expected_results: string[];
  actual_results?: string;
  status: ReviewStatus;
  priority: Priority;
  bu?: string;
  feature?: string;
  llm_provider?: string;
}

export interface ReviewRubric {
  score: number;
  completeness: number; // 0-100
  coverage: number;     // 0-100
  redundancy: number;   // 0-100 (lower redundancy is higher score)
  feasibility: number;  // 0-100
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  missing_scenarios: string[];
  recommendation: 'Pass' | 'Refine' | 'Reject';
  comments: string;
}

export interface ReflectionIteration {
  iteration: number;
  actor_model: string;
  critic_model: string;
  cases_generated: number;
  rubric: ReviewRubric;
  safeguard_triggered: boolean;
  timestamp: string;
  telemetry_logs: string[];
}

export interface ReflectionPipelineResult {
  success: boolean;
  converged: boolean;
  total_iterations: number;
  max_iterations: number;
  min_score: number;
  highest_score: number;
  iterations: ReflectionIteration[];
  best_test_cases: TestCaseItem[];
}

export interface APIEndpointDefinition {
  id: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  summary: string;
  description: string;
  parameters: Array<{ name: string; in: string; required: boolean; schema_type: string }>;
  request_body?: Record<string, any>;
  assertions: Array<{ type: 'status' | 'jsonpath' | 'regex'; expression: string; expected: any }>;
}

export interface APIRunResult {
  endpoint_id: string;
  method: string;
  url: string;
  status_code: number;
  latency_ms: number;
  tls_verified: boolean;
  ip_pinned: string;
  passed: boolean;
  assertions_results: Array<{ expression: string; passed: boolean; actual: any; expected: any }>;
  error_message?: string;
}

export interface AgentDescriptor {
  id: string;
  name: string;
  role: string;
  directory: string;
  responsibility: string;
  input_format: string;
  output_format: string;
  status: 'active' | 'ready';
  primary_methods: string[];
}
