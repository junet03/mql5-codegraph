"""Runtime-generated PDF fixtures; no third-party document bytes are committed."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _base_pdf(path: Path, pages: Sequence[str | None]) -> None:
    """Write a small valid PDF with extractable Helvetica text."""

    objects: list[bytes] = []
    page_references = " ".join(f"{4 + index * 2} 0 R" for index in range(len(pages)))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(
        f"<< /Type /Pages /Kids [{page_references}] /Count {len(pages)} >>".encode()
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, page_text in enumerate(pages):
        page_object = 4 + index * 2
        content_object = page_object + 1
        objects.append(
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_object} 0 R >>"
            ).encode()
        )
        lines = [] if page_text is None else page_text.splitlines()
        commands = ["BT", "/F1 11 Tf", "72 740 Td"]
        for line_index, line in enumerate(lines):
            if line_index:
                commands.append("0 -16 Td")
            commands.append(f"({_escape_pdf_text(line)}) Tj")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        objects.append(
            f"<< /Length {len(stream)} >>\nstream\n".encode()
            + stream
            + b"\nendstream"
        )

    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, value in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode())
        data.extend(value)
        data.extend(b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    data.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode()
    )
    path.write_bytes(data)


def make_pdf(
    path: Path,
    pages: Sequence[str | None],
    outlines: Sequence[tuple[str, int, int | None]] = (),
    *,
    password: str | None = None,
) -> Path:
    """Create text pages plus nested outline entries.

    Outline tuples are ``(title, zero_based_page, parent_outline_index)``.
    """

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as error:  # pragma: no cover - CI installs the reference extra.
        raise RuntimeError("Tests require the reference extra") from error

    temporary = path.with_suffix(".base.pdf")
    _base_pdf(temporary, pages)
    reader = PdfReader(temporary)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    parents = []
    for title, page_number, parent_index in outlines:
        parent = None if parent_index is None else parents[parent_index]
        parents.append(
            writer.add_outline_item(title, page_number, parent=parent)
        )
    if password is not None:
        writer.encrypt(password)
    with path.open("wb") as stream:
        writer.write(stream)
    temporary.unlink()
    return path
