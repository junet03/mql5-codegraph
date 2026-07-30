"""Verify that a release wheel contains only the expected bundled payload."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile


FORBIDDEN_SUFFIXES = {".env", ".key", ".pdf", ".pem"}
FORBIDDEN_PARTS = {"graphify-out", "reference-corpus", "reference-overlays"}


def verify_wheel(path: Path) -> None:
    with ZipFile(path) as archive:
        names = archive.namelist()
    lowered = [name.casefold() for name in names]
    forbidden = [
        name
        for name, normalized in zip(names, lowered, strict=True)
        if Path(normalized).name.startswith(".env")
        or Path(normalized).suffix in FORBIDDEN_SUFFIXES
        or any(part in FORBIDDEN_PARTS for part in normalized.split("/"))
    ]
    if forbidden:
        raise SystemExit(f"forbidden release members: {forbidden}")
    required = {"mql5_codegraph/web_static/index.html"}
    missing = sorted(required.difference(names))
    if missing:
        raise SystemExit(f"missing release members: {missing}")
    if not any(
        name.endswith(".dist-info/licenses/THIRD_PARTY_NOTICES.md")
        for name in names
    ):
        raise SystemExit("THIRD_PARTY_NOTICES.md is missing from wheel licenses")
    dashboard_assets = [
        name
        for name in names
        if name.startswith("mql5_codegraph/web_static/assets/")
        and Path(name).suffix in {".css", ".js"}
    ]
    if not dashboard_assets:
        raise SystemExit("bundled dashboard assets are missing")
    print(
        f"{path.name}: {len(names)} members, "
        f"{len(dashboard_assets)} dashboard assets, policy passed"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    arguments = parser.parse_args()
    verify_wheel(arguments.wheel)


if __name__ == "__main__":
    main()
