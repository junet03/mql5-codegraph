from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
from shutil import copy2, copytree
from tempfile import TemporaryDirectory
from unittest import TestCase

from mql5_codegraph.compiler_evidence import (
    MAX_LOG_BYTES,
    CompilerEvidenceError,
    correlate_compiler_log,
)
from mql5_codegraph.indexer import analyze_repository


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "basic_ea"
LOG_FIXTURES = Path(__file__).parent / "fixtures" / "compiler_logs"


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class CompilerEvidenceTests(TestCase):
    def _materialize(self, log_name: str) -> tuple[TemporaryDirectory[str], Path, Path]:
        temporary = TemporaryDirectory()
        root = Path(temporary.name) / "basic_ea"
        copytree(FIXTURE_ROOT, root)
        log_path = root / "compiler.log"
        copy2(LOG_FIXTURES / log_name, log_path)
        for source in root.rglob("*"):
            if source.suffix.lower() in {".mq5", ".mqh"}:
                os.utime(source, ns=(1_000_000_000, 1_000_000_000))
        os.utime(log_path, ns=(2_000_000_000, 2_000_000_000))
        return temporary, root, log_path

    def test_success_log_is_current_deterministic_and_read_only(self) -> None:
        temporary, root, log_path = self._materialize("basic-success.log")
        with temporary:
            graph = analyze_repository(root)
            before = _hashes(root)

            first = correlate_compiler_log(graph, root, log_path, "BasicEA.mq5")
            second = correlate_compiler_log(graph, root, log_path, "BasicEA.mq5")

            self.assertEqual(first.to_dict(), second.to_dict())
            self.assertEqual("current", first.evidence_state)
            self.assertEqual("success", first.outcome)
            self.assertTrue(first.complete)
            self.assertEqual([], list(first.diagnostics))
            self.assertEqual(before, _hashes(root))

    def test_warning_and_error_locations_remain_evidence_backed(self) -> None:
        temporary, root, log_path = self._materialize("basic-warnings.log")
        with temporary:
            report = correlate_compiler_log(
                analyze_repository(root), root, log_path, "BasicEA.mq5"
            )

            self.assertEqual("warnings", report.outcome)
            self.assertEqual("current", report.evidence_state)
            self.assertEqual(
                ["OnTick", "CRiskManager::CalculateLots"],
                [item.correlation.get("qualified_name") for item in report.diagnostics],
            )
            self.assertTrue(
                all(item.correlation["state"] == "exact" for item in report.diagnostics)
            )

        temporary, root, log_path = self._materialize("basic-errors.log")
        with temporary:
            report = correlate_compiler_log(
                analyze_repository(root), root, log_path, "BasicEA.mq5"
            )

            self.assertEqual("errors", report.outcome)
            self.assertEqual("current", report.evidence_state)
            states = [item.correlation["state"] for item in report.diagnostics]
            self.assertEqual(["no_declaration", "exact", "outside_project"], states)
            self.assertEqual(
                "SubmitOrder", report.diagnostics[1].correlation["qualified_name"]
            )

    def test_foreign_absolute_diagnostic_paths_are_outside_on_every_host(self) -> None:
        temporary, root, log_path = self._materialize("basic-success.log")
        with temporary:
            log_path.write_text(
                "\n".join(
                    [
                        r"C:\outside\WindowsSecret.mqh(1,1) : error 106: unavailable",
                        "/outside/PosixSecret.mqh(1,1) : error 107: unavailable",
                        "Result: 2 errors, 0 warnings, 20 msec elapsed",
                    ]
                ),
                encoding="utf-8",
            )
            os.utime(log_path, ns=(2_000_000_000, 2_000_000_000))

            report = correlate_compiler_log(
                analyze_repository(root), root, log_path, "BasicEA.mq5"
            )

            self.assertEqual(2, len(report.diagnostics))
            self.assertTrue(
                all(
                    item.correlation["state"] == "outside_project"
                    for item in report.diagnostics
                )
            )

    def test_utf16_bom_log_is_current_and_preserves_warning_evidence(self) -> None:
        temporary, root, log_path = self._materialize("basic-warnings.log")
        with temporary:
            log_path.write_bytes(log_path.read_text(encoding="utf-8").encode("utf-16"))

            report = correlate_compiler_log(
                analyze_repository(root), root, log_path, "BasicEA.mq5"
            )

            self.assertTrue(report.complete)
            self.assertEqual("current", report.evidence_state)
            self.assertEqual("warnings", report.outcome)
            self.assertEqual(
                ["OnTick", "CRiskManager::CalculateLots"],
                [item.correlation.get("qualified_name") for item in report.diagnostics],
            )

    def test_missing_summary_is_incomplete_not_success(self) -> None:
        temporary, root, log_path = self._materialize("missing-summary.log")
        with temporary:
            report = correlate_compiler_log(
                analyze_repository(root), root, log_path, "BasicEA.mq5"
            )

            self.assertFalse(report.complete)
            self.assertEqual("incomplete", report.evidence_state)
            self.assertEqual("unknown", report.outcome)

    def test_count_mismatch_is_incomplete_and_unlocated_messages_stay_unlinked(self) -> None:
        temporary, root, log_path = self._materialize("count-mismatch.log")
        with temporary:
            report = correlate_compiler_log(
                analyze_repository(root), root, log_path, "BasicEA.mq5"
            )

            self.assertFalse(report.complete)
            self.assertEqual("incomplete", report.evidence_state)
            self.assertEqual("unknown", report.outcome)

        temporary, root, log_path = self._materialize("unlocated.log")
        with temporary:
            report = correlate_compiler_log(
                analyze_repository(root), root, log_path, "BasicEA.mq5"
            )

            self.assertTrue(report.complete)
            self.assertEqual("errors", report.outcome)
            self.assertIsNone(report.diagnostics[0].location)
            self.assertEqual("unlocated", report.diagnostics[0].correlation["state"])
            self.assertNotIn("symbol_id", report.diagnostics[0].correlation)

    def test_changed_source_makes_prior_compiler_evidence_stale(self) -> None:
        temporary, root, log_path = self._materialize("basic-success.log")
        with temporary:
            graph = analyze_repository(root)
            source = root / "BasicEA.mq5"
            source.write_text(
                source.read_text(encoding="utf-8") + "\nvoid LaterChange() {}\n",
                encoding="utf-8",
            )
            os.utime(source, ns=(3_000_000_000, 3_000_000_000))

            report = correlate_compiler_log(graph, root, log_path, "BasicEA.mq5")

            self.assertEqual("stale", report.evidence_state)
            self.assertNotEqual(
                graph.metadata["source_fingerprint"], report.current_source_fingerprint
            )

    def test_outside_and_oversized_logs_are_rejected_without_reading_raw_contents(self) -> None:
        temporary, root, log_path = self._materialize("basic-success.log")
        with temporary:
            graph = analyze_repository(root)
            outside = root.parent / "outside.log"
            outside.write_text("Result: 0 errors, 0 warnings", encoding="utf-8")
            with self.assertRaises(CompilerEvidenceError) as outside_raised:
                correlate_compiler_log(graph, root, outside, "BasicEA.mq5")
            self.assertEqual("compiler_log_outside_root", outside_raised.exception.code)

            oversized = root / "oversized.log"
            oversized.write_bytes(b"x" * (MAX_LOG_BYTES + 1))
            with self.assertRaises(CompilerEvidenceError) as oversized_raised:
                correlate_compiler_log(graph, root, oversized, "BasicEA.mq5")
            self.assertEqual("compiler_log_too_large", oversized_raised.exception.code)
