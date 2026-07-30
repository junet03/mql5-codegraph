from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mql5_codegraph.reference.builder import build_reference_corpus
from mql5_codegraph.reference.corpus import ReferenceCorpus
from mql5_codegraph.reference.models import BuildRequest, ReferenceError

from .helpers import make_pdf


class ReferenceCorpusTests(unittest.TestCase):
    def _build(self, root: Path) -> tuple[Path, ReferenceCorpus]:
        inputs = root / "pdfs"
        output = root / "corpus"
        inputs.mkdir()
        make_pdf(
            inputs / "mql5.pdf",
            [
                "MQL5 Reference",
                "OrderSend sends a trade request. Exact platform contract.",
                "CTrade provides Buy and Sell methods.",
            ],
            [
                ("Language reference", 0, None),
                ("OrderSend", 1, 0),
                ("CTrade", 2, 0),
            ],
        )
        make_pdf(
            inputs / "mql5book.pdf",
            [
                "MQL5 Programming for Traders",
                "OrderSend sends a trade request. Tutorial example.",
                "Neural network optimization uses training samples.",
            ],
            [
                ("Programming", 0, None),
                ("OrderSend", 1, 0),
                ("Optimization", 2, 0),
            ],
        )
        build_reference_corpus(BuildRequest(inputs, output))
        return output, ReferenceCorpus.open(output)

    def test_search_is_deterministic_authority_aware_and_page_cited(self) -> None:
        with TemporaryDirectory() as directory:
            output, corpus = self._build(Path(directory))
            first = corpus.search("OrderSend", limit=10, max_excerpt_chars=120)
            second = ReferenceCorpus.open(output).search(
                "OrderSend", limit=10, max_excerpt_chars=120
            )
            self.assertEqual(first, second)
            self.assertEqual(2, first["completion"]["candidate_count"])
            self.assertFalse(first["completion"]["truncated"])
            self.assertEqual(
                ["normative", "explanatory"],
                [item["source"]["authority"] for item in first["results"]],
            )
            result = first["results"][0]
            self.assertEqual("reference_document", result["evidence_class"])
            self.assertEqual(2, result["citation"]["physical_page_start"])
            self.assertEqual(2, result["citation"]["physical_page_end"])
            self.assertIn("OrderSend", result["excerpt"])
            self.assertTrue(result["section"]["content_sha256"])
            self.assertEqual(corpus.corpus_fingerprint, result["corpus_fingerprint"])

    def test_no_match_and_limit_completion_are_explicit(self) -> None:
        with TemporaryDirectory() as directory:
            _, corpus = self._build(Path(directory))
            missing = corpus.search("term-that-is-not-present")
            self.assertEqual([], missing["results"])
            self.assertTrue(missing["completion"]["exhaustive"])
            self.assertTrue(missing["completion"]["no_match"])
            bounded = corpus.search("OrderSend", limit=1)
            self.assertEqual(1, bounded["completion"]["returned_count"])
            self.assertEqual(2, bounded["completion"]["candidate_count"])
            self.assertTrue(bounded["completion"]["truncated"])

    def test_excerpt_is_exact_bounded_and_reports_intersecting_pages(self) -> None:
        with TemporaryDirectory() as directory:
            _, corpus = self._build(Path(directory))
            match = corpus.search("CTrade")["results"][0]
            section_id = match["section"]["section_id"]
            full_text = corpus.sections_by_id[section_id]["text"]
            excerpt = corpus.excerpt(section_id, start=1, max_chars=80)
            self.assertEqual(full_text[1:81], excerpt["excerpt"])
            self.assertEqual(3, excerpt["citation"]["physical_page_start"])
            with self.assertRaises(ReferenceError) as missing:
                corpus.excerpt("not-a-section")
            self.assertEqual("reference_section_not_found", missing.exception.code)

    def test_corrupt_snapshot_and_escaping_pointer_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            output, corpus = self._build(Path(directory))
            section_path = (
                corpus.snapshot
                / str(next(iter(corpus.sections_by_id.values()))["markdown_path"])
            )
            section_path.write_text("tampered", encoding="utf-8")
            with self.assertRaises(ReferenceError) as corrupt:
                ReferenceCorpus.open(output)
            self.assertEqual("reference_integrity_failed", corrupt.exception.code)

        with TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "current.json").write_text(
                json.dumps(
                    {
                        "contract_version": "1.0.0",
                        "corpus_fingerprint": "a" * 64,
                        "manifest_sha256": "b" * 64,
                        "snapshot_path": "../outside",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ReferenceError) as escaped:
                ReferenceCorpus.open(output)
            self.assertEqual("invalid_reference_pointer", escaped.exception.code)

    def test_twenty_symbol_golden_queries_return_normative_page_citations(self) -> None:
        symbols = [
            "OnInit",
            "OnDeinit",
            "OnTick",
            "OnTimer",
            "OnTrade",
            "OnTradeTransaction",
            "OrderSend",
            "OrderCheck",
            "SymbolInfoDouble",
            "CopyBuffer",
            "CopyRates",
            "iMA",
            "iRSI",
            "PositionSelect",
            "HistorySelect",
            "MqlTradeRequest",
            "MqlTradeResult",
            "CTrade",
            "ArraySetAsSeries",
            "IndicatorRelease",
        ]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "pdfs"
            corpus_root = root / "corpus"
            inputs.mkdir()
            make_pdf(
                inputs / "mql5.pdf",
                [f"{symbol}\nNormative contract for {symbol}." for symbol in symbols],
                [
                    (symbol, page_number, None)
                    for page_number, symbol in enumerate(symbols)
                ],
            )
            build_reference_corpus(BuildRequest(inputs, corpus_root))
            corpus = ReferenceCorpus.open(corpus_root)
            for page_number, symbol in enumerate(symbols, start=1):
                with self.subTest(symbol=symbol):
                    result = corpus.search(symbol, limit=1)["results"][0]
                    self.assertEqual("normative", result["source"]["authority"])
                    self.assertEqual(
                        page_number,
                        result["citation"]["physical_page_start"],
                    )


if __name__ == "__main__":
    unittest.main()
