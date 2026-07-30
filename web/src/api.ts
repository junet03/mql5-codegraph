export type Location = {
  file: string;
  line: number;
  column: number;
  end_line?: number;
  end_column?: number;
};

export type GraphNode = {
  id: string;
  kind: string;
  name: string;
  qualified_name: string;
  location?: Location;
  attributes: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  relationship: string;
  origin: string;
  confidence: number;
  location?: Location;
  attributes: Record<string, unknown>;
};

export type AnalysisJob = {
  id: string;
  root: string;
  include_roots: string[];
  status: "queued" | "running" | "completed" | "failed";
  started_at: string | null;
  finished_at: string | null;
  summary: Record<string, unknown> | null;
  error: string | null;
};

export type DashboardStatus = {
  ready: boolean;
  root: string | null;
  graph_version: number;
  summary: null | {
    files: number;
    nodes: number;
    edges: number;
    diagnostics: number;
    diagnostic_counts: Record<string, number>;
    source_fingerprint: string;
  };
  active_job: AnalysisJob | null;
  recent_jobs: AnalysisJob[];
  last_error: string | null;
};

export type Projection = {
  version: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
  visible_nodes: number;
  visible_edges: number;
  truncated: boolean;
  filters: { kinds: string[]; relationships: string[]; q: string; limit: number };
  available_kinds: Record<string, number>;
  available_relationships: Record<string, number>;
};

export type Diagnostic = {
  code: string;
  severity: string;
  message: string;
  location?: Location;
};

type ErrorEnvelope = { error?: { code?: string; message?: string } };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const payload = (await response.json()) as T & ErrorEnvelope;
  if (!response.ok) {
    throw new Error(payload.error?.message || `Request failed (${response.status})`);
  }
  return payload;
}

function params(values: Record<string, string | number | string[] | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (Array.isArray(value)) value.forEach((item) => query.append(key, item));
    else if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

export const api = {
  status: () => request<DashboardStatus>("/api/status"),
  analyze: () =>
    request<{ job: AnalysisJob }>("/api/analyze", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  job: (id: string) => request<{ job: AnalysisJob }>(`/api/jobs/${encodeURIComponent(id)}`),
  graph: (filters: { kinds?: string[]; relationships?: string[]; q?: string; limit?: number } = {}) =>
    request<Projection>(`/api/graph?${params({
      kind: filters.kinds,
      relationship: filters.relationships,
      q: filters.q,
      limit: filters.limit ?? 900,
    })}`),
  query: (q: string, kind?: string) =>
    request<{ results: GraphNode[] }>(`/api/query?${params({ q, kind, limit: 40 })}`),
  context: (symbol: string, depth = 1) =>
    request<{ nodes: GraphNode[]; edges: GraphEdge[] }>(
      `/api/context?${params({ symbol, depth })}`,
    ),
  impact: (symbol: string, depth = 3) =>
    request<{ results: Array<{ node: GraphNode; distance: number; edge_path: string[] }> }>(
      `/api/impact?${params({ symbol, depth })}`,
    ),
  diagnostics: (severity?: string, code?: string) =>
    request<{
      total: number;
      matched: number;
      truncated: boolean;
      items: Diagnostic[];
      by_severity: Record<string, number>;
      by_code: Record<string, number>;
    }>(`/api/diagnostics?${params({ severity, code, limit: 500 })}`),
  source: (file: string, line = 1) =>
    request<{ file: string; content: string; line_count: number; highlight_line: number }>(
      `/api/source?${params({ file, line })}`,
    ),
};
