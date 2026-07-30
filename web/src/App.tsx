import {
  Activity, AlertTriangle, Binary, Boxes, Database, FolderGit2, GitFork,
  Layers3, LoaderCircle, Play, RefreshCw, ShieldCheck, Sparkles,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type DashboardStatus, type Diagnostic, type GraphEdge, type GraphNode, type Projection } from "./api";
import { DiagnosticsPanel } from "./components/DiagnosticsPanel";
import { GraphWorkspace } from "./components/GraphWorkspace";
import { Inspector } from "./components/Inspector";
import { SearchPalette } from "./components/SearchPalette";
import { SourceViewer } from "./components/SourceViewer";

function metric(value: number | undefined): string {
  return (value ?? 0).toLocaleString("en-US");
}

export default function App() {
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [projection, setProjection] = useState<Projection | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [diagnosticTotal, setDiagnosticTotal] = useState(0);
  const [severity, setSeverity] = useState("");
  const [root, setRoot] = useState("");
  const [includeRoot, setIncludeRoot] = useState("");
  const [selectedKinds, setSelectedKinds] = useState<string[]>([]);
  const [selectedRelationships, setSelectedRelationships] = useState<string[]>([]);
  const [focused, setFocused] = useState(false);
  const [source, setSource] = useState<{ file: string; content: string; highlight_line: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const initialized = useRef(false);

  const loadProjection = useCallback(async () => {
    setLoadingGraph(true);
    try {
      const next = await api.graph({ kinds: selectedKinds, relationships: selectedRelationships, limit: 900 });
      setProjection(next);
      setFocused(false);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setLoadingGraph(false);
    }
  }, [selectedKinds, selectedRelationships]);

  const loadDiagnostics = useCallback(async () => {
    try {
      const next = await api.diagnostics(severity || undefined);
      setDiagnostics(next.items);
      setDiagnosticTotal(next.total);
    } catch { setDiagnostics([]); setDiagnosticTotal(0); }
  }, [severity]);

  const refreshStatus = useCallback(async () => {
    try {
      const next = await api.status();
      setStatus(next);
      const job = next.active_job ?? next.recent_jobs[0];
      setRoot(next.root ?? job?.root ?? "");
      setIncludeRoot(job?.include_roots[0] ?? "");
      return next;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      return null;
    }
  }, []);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    void refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    if (!status?.active_job?.id) return;
    const timer = window.setInterval(async () => {
      await refreshStatus();
    }, 650);
    return () => window.clearInterval(timer);
  }, [status?.active_job?.id, refreshStatus]);

  useEffect(() => {
    if (status?.ready && !focused) void loadProjection();
  }, [status?.ready, status?.graph_version, focused, loadProjection]);

  useEffect(() => {
    if (status?.ready) void loadDiagnostics();
  }, [status?.ready, status?.graph_version, loadDiagnostics]);

  const analyze = async () => {
    setError(null);
    setSelected(null);
    try {
      const response = await api.analyze();
      setStatus((current) => current ? { ...current, active_job: response.job } : current);
      await refreshStatus();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  };

  const projectFocus = useCallback((nodes: GraphNode[], edges: GraphEdge[]) => {
    setProjection((current) => ({
      version: current?.version ?? status?.graph_version ?? 0,
      nodes, edges,
      total_nodes: current?.total_nodes ?? nodes.length,
      total_edges: current?.total_edges ?? edges.length,
      visible_nodes: nodes.length,
      visible_edges: edges.length,
      truncated: false,
      filters: { kinds: [], relationships: [], q: "focused context", limit: nodes.length },
      available_kinds: current?.available_kinds ?? {},
      available_relationships: current?.available_relationships ?? {},
    }));
    setFocused(true);
    if (nodes.length === 1) setSelected(nodes[0]);
  }, [status?.graph_version]);

  const focusNode = async (node: GraphNode) => {
    setSelected(node);
    try {
      const context = await api.context(node.id, 1);
      projectFocus(context.nodes, context.edges);
      setSelected(node);
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
  };

  const openSource = async (file: string, line: number) => {
    try { setSource(await api.source(file, line)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
  };

  const handleSelect = useCallback((node: GraphNode | null) => setSelected(node), []);
  const isAnalyzing = Boolean(status?.active_job);
  const graphHealth = useMemo(() => {
    const warnings = status?.summary?.diagnostic_counts.warning ?? 0;
    const errors = status?.summary?.diagnostic_counts.error ?? 0;
    if (errors) return { label: "needs attention", tone: "danger" };
    if (warnings) return { label: "review signals", tone: "warn" };
    return { label: "graph healthy", tone: "good" };
  }, [status]);

  const toggle = (value: string, current: string[], setter: (values: string[]) => void) =>
    setter(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark"><Binary size={20} /><span>MQ</span></div>
        <div className="brand-copy">
          <strong>MQL5 CODEGRAPH</strong>
          <span>Local structural intelligence</span>
        </div>
        <SearchPalette ready={Boolean(status?.ready)} onFocus={focusNode} />
        <div className={`runtime-status ${isAnalyzing ? "analyzing" : status?.ready ? "ready" : "idle"}`}>
          <span />
          {isAnalyzing ? "Indexing" : status?.ready ? "Local engine ready" : "Awaiting repository"}
        </div>
      </header>

      <div className="workspace">
        <aside className="left-rail">
          <section className="repo-card">
            <div className="section-kicker"><FolderGit2 size={15} /> Repository</div>
            <label>Authorized source root<input value={root} readOnly placeholder="Start with --root" /></label>
            <label>Authorized MT5 include root<input value={includeRoot} readOnly placeholder="Optional --include-root" /></label>
            <button className="analyze-button" onClick={analyze} disabled={isAnalyzing || !root.trim()}>
              {isAnalyzing ? <LoaderCircle className="spin" size={16} /> : <Play size={15} fill="currentColor" />}
              {isAnalyzing ? "Building intelligence…" : status?.ready ? "Re-index repository" : "Analyze repository"}
            </button>
            {status?.active_job && <div className="job-progress"><span /><small>{status.active_job.status} · source remains local</small></div>}
          </section>

          <section className="metric-grid">
            <div><FileMetric icon={<Database size={15} />} value={metric(status?.summary?.files)} label="files" /></div>
            <div><FileMetric icon={<Boxes size={15} />} value={metric(status?.summary?.nodes)} label="nodes" /></div>
            <div><FileMetric icon={<GitFork size={15} />} value={metric(status?.summary?.edges)} label="edges" /></div>
            <div><FileMetric icon={<AlertTriangle size={15} />} value={metric(status?.summary?.diagnostics)} label="signals" /></div>
          </section>

          <section className="health-card">
            <div className={`health-icon ${graphHealth.tone}`}><ShieldCheck size={18} /></div>
            <div><strong>{graphHealth.label}</strong><span>Evidence remains traceable</span></div>
            <Activity size={16} />
          </section>

          <section className="filter-section">
            <div className="section-kicker"><Layers3 size={15} /> Node types</div>
            <div className="filter-list">
              {Object.entries(projection?.available_kinds ?? {}).map(([kind, count]) => (
                <button key={kind} className={selectedKinds.includes(kind) ? "active" : ""}
                        onClick={() => toggle(kind, selectedKinds, setSelectedKinds)}>
                  <span className={`kind-dot kind-${kind}`} />
                  <span>{kind.replaceAll("_", " ")}</span><em>{count}</em>
                </button>
              ))}
            </div>
          </section>

          <section className="filter-section relationships">
            <div className="section-kicker"><GitFork size={15} /> Relationships</div>
            <div className="filter-list">
              {Object.entries(projection?.available_relationships ?? {}).map(([relationship, count]) => (
                <button key={relationship} className={selectedRelationships.includes(relationship) ? "active" : ""}
                        onClick={() => toggle(relationship, selectedRelationships, setSelectedRelationships)}>
                  <span className="edge-swatch" />
                  <span>{relationship.replaceAll("_", " ")}</span><em>{count}</em>
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="main-stage">
          <div className="stage-toolbar">
            <div>
              <span className="breadcrumb">GRAPH / {focused ? "FOCUSED CONTEXT" : "REPOSITORY MAP"}</span>
              <strong>{projection ? `${metric(projection.visible_nodes)} nodes · ${metric(projection.visible_edges)} relationships` : "No active graph"}</strong>
            </div>
            {focused && <button onClick={() => setFocused(false)}><RefreshCw size={14} /> Return to repository</button>}
            {loadingGraph && <span className="loading-label"><LoaderCircle className="spin" size={14} /> projecting</span>}
          </div>
          <GraphWorkspace projection={projection} selectedId={selected?.id ?? null} onSelect={handleSelect} />
          {error && <div className="error-banner"><AlertTriangle size={16} /><span>{error}</span><button onClick={() => setError(null)}>dismiss</button></div>}
          <DiagnosticsPanel items={diagnostics} total={diagnosticTotal} severity={severity}
                            onSeverity={setSeverity} onOpenSource={openSource} />
        </section>

        <Inspector node={selected} projection={projection} onFocusGraph={projectFocus} onOpenSource={openSource} />
      </div>

      <footer className="statusbar">
        <span><Sparkles size={13} /> MQL5-aware runtime model</span>
        <span>{status?.root ?? "No repository selected"}</span>
        <span>Graph v{status?.graph_version ?? 0} · offline</span>
      </footer>
      <SourceViewer source={source} onClose={() => setSource(null)} />
    </main>
  );
}

function FileMetric({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return <>{icon}<strong>{value}</strong><span>{label}</span></>;
}
