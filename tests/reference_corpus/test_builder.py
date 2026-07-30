from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mql5_codegraph.reference.builder import build_reference_corpus
from mql5_codegraph.reference.models import BuildRequest, ReferenceError

from .helpers import make_pdf


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


class ReferenceBuilderTests(unittest.TestCase):
    def test_build_is_page_complete_deterministic_and_reusable(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "pdfs"
            output = root / "corpus"
            inputs.mkdir()
            make_pdf(
                inputs / "mql5.pdf",
                [
                    "MQL5 Reference\nContents",
                    "OrderSend\nSends a trade request.\nbool OrderSend(request,result);",
                    "Field | Type\nrequest | MqlTradeRequest",
                    None,
                    "Return Value\ntrue on successful request validation",
                ],
                [
                    ("Trading functions", 0, None),
                    ("OrderSend", 1, 0),
                    ("OrderSend", 1, 0),
                    ("Return value", 4, 1),
                ],
            )

            request = BuildRequest(inputs, output, max_pages_per_section=2)
            first = build_reference_corpus(request)
            pointer_bytes = (output / "current.json").read_bytes()
            snapshot = output / first["snapshot_path"]
            canonical = {
                path.relative_to(snapshot).as_posix(): path.read_bytes()
                for path in snapshot.rglob("*")
                if path.is_file()
            }

            repeated = [build_reference_corpus(request) for _ in range(99)]
            second = repeated[-1]
            self.assertTrue(second["reused"])
            self.assertEqual(first["corpus_fingerprint"], second["corpus_fingerprint"])
            self.assertEqual(pointer_bytes, (output / "current.json").read_bytes())
            self.assertEqual(
                canonical,
                {
                    path.relative_to(snapshot).as_posix(): path.read_bytes()
                    for path in snapshot.rglob("*")
                    if path.is_file()
                },
            )

            pages = _jsonl(snapshot / "records" / "pages.jsonl")
            sections = _jsonl(snapshot / "records" / "sections.jsonl")
            self.assertEqual([1, 2, 3, 4, 5], [page["physical_page"] for page in pages])
            self.assertEqual("empty", pages[3]["state"])
            covered = [
                page
                for section in sections
                for page in range(
                    int(section["physical_page_start"]),
                    int(section["physical_page_end"]) + 1,
                )
            ]
            self.assertEqual([1, 2, 3, 4, 5], covered)
            self.assertEqual(
                len(sections),
                len({section["section_id"] for section in sections}),
            )
            self.assertTrue(
                all(not Path(section["markdown_path"]).is_absolute() for section in sections)
            )
            markdown = "\n".join(
                (snapshot / str(section["markdown_path"])).read_text(encoding="utf-8")
                for section in sections
            )
            self.assertIn("Physical PDF page 3", markdown)
            self.assertIn("request | MqlTradeRequest", markdown)
            self.assertIn("empty_or_image_only", markdown)

    def test_failed_rebuild_preserves_the_last_valid_pointer(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "pdfs"
            output = root / "corpus"
            inputs.mkdir()
            make_pdf(inputs / "mql5.pdf", ["MQL5 Reference"])
            build_reference_corpus(BuildRequest(inputs, output))
            prior = (output / "current.json").read_bytes()

            make_pdf(
                inputs / "locked.pdf",
                ["secret"],
                password="not-the-empty-password",
            )
            with self.assertRaises(ReferenceError) as raised:
                build_reference_corpus(BuildRequest(inputs, output))
            self.assertEqual("invalid_reference_source", raised.exception.code)
            self.assertEqual(prior, (output / "current.json").read_bytes())

    def test_manifest_pins_declared_hash_and_rejects_duplicate_sources(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "pdfs"
            inputs.mkdir()
            make_pdf(inputs / "custom.pdf", ["Custom reference"])
            declarations = root / "sources.json"
            declarations.write_text(
                json.dumps(
                    {
                        "contract_version": "1.0.0",
                        "sources": [
                            {
                                "source_id": "custom",
                                "filename": "custom.pdf",
                                "title": "Custom",
                                "authority": "unclassified",
                                "role": "supplement",
                                "official_url": None,
                                "expected_sha256": "0" * 64,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ReferenceError) as raised:
                build_reference_corpus(
                    BuildRequest(inputs, root / "corpus", declarations)
                )
            self.assertEqual("invalid_reference_source", raised.exception.code)

            payload = json.loads(declarations.read_text(encoding="utf-8"))
            payload["sources"].append(dict(payload["sources"][0]))
            payload["sources"][0]["expected_sha256"] = None
            payload["sources"][1]["expected_sha256"] = None
            declarations.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ReferenceError) as duplicate:
                build_reference_corpus(
                    BuildRequest(inputs, root / "corpus", declarations)
                )
            self.assertEqual("invalid_source_manifest", duplicate.exception.code)


if __name__ == "__main__":
    unittest.main()
