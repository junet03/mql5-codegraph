"""Thread-safe graph snapshots and background analysis jobs."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock, Thread
from typing import Callable, Iterable
from uuid import uuid4

from ..analysis_budget import AnalysisBudget, AnalysisBudgetExceeded
from ..graph import CodeGraph
from ..indexer import analyze_repository
from ..intelligence import IntelligenceKernel


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class AnalysisJob:
    id: str
    root: str
    include_roots: list[str]
    max_work: int | None
    status: str = "queued"
    started_at: str | None = None
    finished_at: str | None = None
    summary: dict[str, object] | None = None
    error: str | None = None
    error_code: str | None = None
    error_details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "root": self.root,
            "include_roots": list(self.include_roots),
            "max_work": self.max_work,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "summary": self.summary,
            "error": self.error,
            "error_code": self.error_code,
            "error_details": self.error_details,
        }


class DashboardState:
    def __init__(
        self,
        analyzer: Callable[[str | Path, Iterable[str | Path]], CodeGraph] = analyze_repository,
        max_jobs: int = 20,
    ) -> None:
        self._lock = RLock()
        self._analyzer = analyzer
        self._max_jobs = max_jobs
        self._graph: CodeGraph | None = None
        self._kernel: IntelligenceKernel | None = None
        self._root: Path | None = None
        self._graph_version = 0
        self._active_job_id: str | None = None
        self._jobs: OrderedDict[str, AnalysisJob] = OrderedDict()
        self._last_error: str | None = None

    def load_graph(self, graph: CodeGraph, root: str | Path | None = None) -> None:
        resolved_root = Path(root).resolve() if root is not None else None
        with self._lock:
            revision = self._graph_version + 1
            kernel = IntelligenceKernel(graph, snapshot_revision=revision)
            self._graph = graph
            self._kernel = kernel
            self._root = resolved_root
            self._graph_version = revision
            self._last_error = None

    def start_analysis(
        self,
        root: str | Path,
        include_roots: Iterable[str | Path] = (),
        *,
        max_work: int | None = None,
    ) -> AnalysisJob:
        resolved_root = Path(root).resolve()
        if not resolved_root.is_dir():
            raise ValueError(f"Repository directory does not exist: {resolved_root}")
        AnalysisBudget(max_work)
        resolved_includes = [str(Path(path).resolve()) for path in include_roots]
        with self._lock:
            if self._active_job_id is not None:
                raise RuntimeError("An analysis job is already running")
            job = AnalysisJob(uuid4().hex, str(resolved_root), resolved_includes, max_work)
            self._jobs[job.id] = job
            while len(self._jobs) > self._max_jobs:
                self._jobs.popitem(last=False)
            self._active_job_id = job.id
        Thread(target=self._run_analysis, args=(job.id,), daemon=True,
               name=f"mql5-codegraph-{job.id[:8]}").start()
        return job

    def _run_analysis(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
            job.started_at = _utc_now()
        try:
            if job.max_work is None:
                graph = self._analyzer(job.root, job.include_roots)
            else:
                graph = self._analyzer(
                    job.root,
                    job.include_roots,
                    max_work=job.max_work,
                )
            summary = {
                "files": graph.metadata.get("file_count", 0),
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
                "diagnostics": len(graph.diagnostics),
                "source_fingerprint": graph.metadata.get("source_fingerprint"),
            }
            with self._lock:
                revision = self._graph_version + 1
                kernel = IntelligenceKernel(graph, snapshot_revision=revision)
                self._graph = graph
                self._kernel = kernel
                self._root = Path(job.root)
                self._graph_version = revision
                self._last_error = None
                job.status = "completed"
                job.summary = summary
                job.finished_at = _utc_now()
        except AnalysisBudgetExceeded as error:
            with self._lock:
                self._last_error = error.message
                job.status = "failed"
                job.error = error.message
                job.error_code = error.code
                job.error_details = error.to_dict()["details"]
                job.finished_at = _utc_now()
        except Exception as error:  # background boundary: retain last valid graph
            message = str(error) or error.__class__.__name__
            with self._lock:
                self._last_error = message
                job.status = "failed"
                job.error = message
                job.finished_at = _utc_now()
        finally:
            with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None

    def get_job(self, job_id: str) -> AnalysisJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return AnalysisJob(**job.to_dict()) if job else None

    def snapshot(self) -> tuple[CodeGraph | None, Path | None, int]:
        with self._lock:
            return self._graph, self._root, self._graph_version

    def intelligence_snapshot(
        self,
    ) -> tuple[
        CodeGraph | None,
        IntelligenceKernel | None,
        Path | None,
        int,
    ]:
        """Return one atomically published graph/kernel snapshot pair."""

        with self._lock:
            return (
                self._graph,
                self._kernel,
                self._root,
                self._graph_version,
            )

    def status(self) -> dict[str, object]:
        with self._lock:
            graph = self._graph
            diagnostic_counts: dict[str, int] = {}
            if graph:
                for diagnostic in graph.diagnostics:
                    diagnostic_counts[diagnostic.severity] = diagnostic_counts.get(diagnostic.severity, 0) + 1
            active = self._jobs.get(self._active_job_id) if self._active_job_id else None
            return {
                "ready": graph is not None,
                "root": str(self._root) if self._root else None,
                "graph_version": self._graph_version,
                "summary": {
                    "files": graph.metadata.get("file_count", 0),
                    "nodes": len(graph.nodes),
                    "edges": len(graph.edges),
                    "diagnostics": len(graph.diagnostics),
                    "diagnostic_counts": diagnostic_counts,
                    "source_fingerprint": graph.metadata.get("source_fingerprint"),
                } if graph else None,
                "active_job": active.to_dict() if active else None,
                "recent_jobs": [job.to_dict() for job in reversed(list(self._jobs.values()))],
                "last_error": self._last_error,
            }
