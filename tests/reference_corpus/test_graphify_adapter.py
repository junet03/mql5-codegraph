from __future__ import annotations

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from mql5_codegraph.reference import BuildRequest, ReferenceError, build_reference_corpus
from mql5_codegraph.reference.graphify_adapter import build_graphify_overlay
from mql5_codegraph.reference.models import GraphifyRequest

from .helpers import make_pdf


class _FakeGraphify:
    def __init__(
        self,
        *,
        version: str = "0.9.27",
        exit_code: int = 0,
        malformed: bool = False,
    ) -> None:
        self.version = version
        self.exit_code = exit_code
        self.malformed = malformed
        self.calls: list[list[str]] = []
        self.environments: list[dict[str, str]] = []

    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(command))
        self.assert_safe_kwargs(kwargs)
        self.environments.append(dict(kwargs["env"]))  # type: ignore[arg-type]
        if command[1:] == ["--version"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=f"graphify {self.version}\n",
                stderr="",
            )
        if self.exit_code:
            return subprocess.CompletedProcess(
                command,
                self.exit_code,
                stdout="",
                stderr="simulated failure",
            )
        output = Path(command[command.index("--out") + 1]) / "graphify-out"
        output.mkdir(parents=True)
        value: object = {"unexpected": True}
        if not self.malformed:
            value = {
                "directed": True,
                "multigraph": False,
                "graph": {},
                "nodes": [
                    {
                        "id": "ordersend",
                        "label": "OrderSend",
                        "source_file": "mql5-reference/sections/ordersend.md",
                    }
                ],
                "links": [],
            }
        (output / "graph.json").write_text(json.dumps(value), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    @staticmethod
    def assert_safe_kwargs(kwargs: object) -> None:
        values = dict(kwargs)  # type: ignore[arg-type]
        if values.get("shell") is not False:
            raise AssertionError("Graphify subprocess must use shell=False")
        if values.get("capture_output") is not True:
            raise AssertionError("Graphify subprocess must capture output")
        if not isinstance(values.get("env"), dict):
            raise AssertionError("Graphify subprocess must receive an explicit environment")


class GraphifyAdapterTests(unittest.TestCase):
    def _corpus(self, root: Path) -> Path:
        inputs = root / "pdfs"
        corpus = root / "corpus"
        inputs.mkdir()
        make_pdf(inputs / "mql5.pdf", ["OrderSend reference"])
        build_reference_corpus(BuildRequest(inputs, corpus))
        return corpus

    @patch.dict(
        "os.environ",
        {"OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1", "OLLAMA_HOST": ""},
    )
    def test_local_overlay_is_isolated_versioned_and_reusable(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = self._corpus(root)
            output = root / "overlay"
            fake = _FakeGraphify()
            request = GraphifyRequest(
                corpus_root=corpus,
                output_dir=output,
                executable="graphify",
                backend="ollama",
                processing_boundary="local",
            )

            first = build_graphify_overlay(request, runner=fake)
            before_corpus = {
                path.relative_to(corpus).as_posix(): path.read_bytes()
                for path in corpus.rglob("*")
                if path.is_file()
            }
            second = build_graphify_overlay(request, runner=fake)

            self.assertFalse(first["reused"])
            self.assertTrue(second["reused"])
            self.assertEqual(3, len(fake.calls))
            extract = fake.calls[1]
            self.assertEqual("extract", extract[1])
            self.assertIn("--backend", extract)
            self.assertEqual("ollama", extract[extract.index("--backend") + 1])
            self.assertEqual("semantic_overlay_inference", first["evidence_class"])
            self.assertEqual(
                before_corpus,
                {
                    path.relative_to(corpus).as_posix(): path.read_bytes()
                    for path in corpus.rglob("*")
                    if path.is_file()
                },
            )

    def test_remote_processing_requires_explicit_authority(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = self._corpus(root)
            fake = _FakeGraphify()
            request = GraphifyRequest(
                corpus_root=corpus,
                output_dir=root / "overlay",
                executable="graphify",
                backend="openai",
                processing_boundary="remote",
            )
            with self.assertRaises(ReferenceError) as raised:
                build_graphify_overlay(request, runner=fake)
            self.assertEqual("graphify_remote_not_authorized", raised.exception.code)
            self.assertEqual([], fake.calls)

    @patch.dict(
        "os.environ",
        {
            "ANTHROPIC_API_KEY": "unrelated-provider",
            "GITHUB_TOKEN": "unrelated-host-token",
            "OPENAI_API_KEY": "selected-provider",
            "PATH": "runtime-path",
        },
        clear=True,
    )
    def test_subprocess_environment_is_scoped_to_the_selected_backend(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            fake = _FakeGraphify()
            request = GraphifyRequest(
                corpus_root=self._corpus(root),
                output_dir=root / "overlay",
                executable="graphify",
                backend="openai",
                processing_boundary="remote",
                allow_remote=True,
            )

            build_graphify_overlay(request, runner=fake)

            version_environment, extract_environment = fake.environments
            self.assertEqual({"PATH": "runtime-path"}, version_environment)
            self.assertEqual("runtime-path", extract_environment["PATH"])
            self.assertEqual(
                "selected-provider",
                extract_environment["OPENAI_API_KEY"],
            )
            self.assertNotIn("ANTHROPIC_API_KEY", extract_environment)
            self.assertNotIn("GITHUB_TOKEN", extract_environment)

    @patch.dict(
        "os.environ",
        {"OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1", "OLLAMA_HOST": ""},
    )
    def test_unsupported_or_malformed_graphify_never_replaces_overlay(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = self._corpus(root)
            output = root / "overlay"
            valid = GraphifyRequest(
                corpus_root=corpus,
                output_dir=output,
                executable="graphify",
                backend="ollama",
                processing_boundary="local",
            )
            build_graphify_overlay(valid, runner=_FakeGraphify())
            prior = (output / "current.json").read_bytes()

            changed = GraphifyRequest(
                corpus_root=corpus,
                output_dir=output,
                executable="graphify",
                backend="ollama",
                processing_boundary="local",
                model="changed-model",
            )
            with self.assertRaises(ReferenceError) as malformed:
                build_graphify_overlay(changed, runner=_FakeGraphify(malformed=True))
            self.assertEqual("graphify_output_invalid", malformed.exception.code)
            self.assertEqual(prior, (output / "current.json").read_bytes())

            with self.assertRaises(ReferenceError) as unsupported:
                build_graphify_overlay(changed, runner=_FakeGraphify(version="1.0.0"))
            self.assertEqual("graphify_version_unsupported", unsupported.exception.code)
            self.assertEqual(prior, (output / "current.json").read_bytes())

    def test_local_boundary_rejects_a_remote_capable_backend(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            request = GraphifyRequest(
                corpus_root=self._corpus(root),
                output_dir=root / "overlay",
                executable="graphify",
                backend="openai",
                processing_boundary="local",
            )
            with self.assertRaises(ReferenceError) as raised:
                build_graphify_overlay(request, runner=_FakeGraphify())
            self.assertEqual("graphify_processing_boundary_invalid", raised.exception.code)

    @patch.dict(
        "os.environ",
        {"OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1", "OLLAMA_HOST": ""},
    )
    def test_timeout_and_nonzero_exit_preserve_the_prior_overlay(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = self._corpus(root)
            output = root / "overlay"
            valid = GraphifyRequest(
                corpus_root=corpus,
                output_dir=output,
                executable="graphify",
                backend="ollama",
                processing_boundary="local",
            )
            build_graphify_overlay(valid, runner=_FakeGraphify())
            prior = (output / "current.json").read_bytes()
            changed = GraphifyRequest(
                corpus_root=corpus,
                output_dir=output,
                executable="graphify",
                backend="ollama",
                processing_boundary="local",
                model="next-model",
            )

            def timeout(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if command[1:] == ["--version"]:
                    return _FakeGraphify()(command, **kwargs)
                raise subprocess.TimeoutExpired(command, 1)

            with self.assertRaises(ReferenceError) as timed_out:
                build_graphify_overlay(changed, runner=timeout)
            self.assertEqual("graphify_timeout", timed_out.exception.code)
            self.assertEqual(prior, (output / "current.json").read_bytes())

            with self.assertRaises(ReferenceError) as failed:
                build_graphify_overlay(changed, runner=_FakeGraphify(exit_code=2))
            self.assertEqual("graphify_execution_failed", failed.exception.code)
            self.assertEqual(prior, (output / "current.json").read_bytes())

    @patch.dict(
        "os.environ",
        {"OLLAMA_BASE_URL": "http://example.invalid:11434/v1", "OLLAMA_HOST": ""},
    )
    def test_local_boundary_rejects_non_loopback_ollama_configuration(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            request = GraphifyRequest(
                corpus_root=self._corpus(root),
                output_dir=root / "overlay",
                executable="graphify",
                backend="ollama",
                processing_boundary="local",
            )
            with self.assertRaises(ReferenceError) as raised:
                build_graphify_overlay(request, runner=_FakeGraphify())
            self.assertEqual("graphify_processing_boundary_invalid", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
