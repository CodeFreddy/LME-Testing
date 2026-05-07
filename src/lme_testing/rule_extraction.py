from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree

from schemas import validate_artifact_list, validate_atomic_rule, validate_semantic_rule
from scripts.generate_semantic_rules import build_semantic_rule

from .storage import ensure_dir, write_json


DEFAULT_HKEX_SECTIONS = {"3.2.5.1", "3.2.5.3"}
SECTION_HEADING_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)\s+(.+?)\s*$")


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class SectionBlock:
    section_number: str
    title: str
    start_page: int
    end_page: int
    raw_text: str

    @property
    def section_label(self) -> str:
        return f"{self.section_number} {self.title}".strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_rule_artifacts(
    source_path: Path,
    output_dir: Path,
    doc_id: str,
    doc_title: str,
    doc_version: str,
    target_sections: set[str] | None = None,
) -> dict:
    """Extract first-pass rule artifacts for Rule Review.

    The current implementation keeps HKEX Initial Margin behavior deterministic:
    PDF/DOCX/Markdown are converted to page text, source sections are detected by
    numbered headings, and the demo section allow-list is emitted as governed
    atomic/semantic artifacts without adding an LLM extraction stage.
    """
    source_path = source_path.resolve()
    output_dir = ensure_dir(output_dir)
    target_sections = target_sections or DEFAULT_HKEX_SECTIONS
    pages = extract_pages(source_path)
    if not pages:
        raise ValueError(f"No text could be extracted from {source_path}")

    sections = select_hkex_sections(parse_numbered_sections(pages), target_sections)
    if not sections:
        raise ValueError(
            "No target HKEX sections were found. Expected one of: "
            + ", ".join(sorted(target_sections))
        )

    atomic_rules = [
        build_atomic_rule(section, index)
        for index, section in enumerate(sections, start=1)
    ]
    semantic_rules = [
        enrich_semantic_rule(build_semantic_rule(rule, doc_id, doc_title, doc_version), rule)
        for rule in atomic_rules
    ]
    metadata = {
        "doc_id": doc_id,
        "doc_title": doc_title,
        "doc_version": doc_version,
        "source_path": str(source_path),
        "source_filename": source_path.name,
        "source_format": source_path.suffix.lower().lstrip(".") or "unknown",
        "source_hash": sha256_file(source_path),
        "document_class": "calculation_guide",
        "page_count": len(pages),
        "clause_count": len(sections),
        "atomic_rule_count": len(atomic_rules),
        "semantic_rule_count": len(semantic_rules),
        "target_sections": sorted(target_sections),
        "extraction_mode": "deterministic_hkex_calculation_guide_v1",
    }

    write_json(output_dir / "metadata.json", metadata)
    write_json(output_dir / "pages.json", [asdict(page) for page in pages])
    write_json(output_dir / "clauses.json", [section_to_clause(section) for section in sections])
    write_json(output_dir / "atomic_rules.json", atomic_rules)
    write_json(output_dir / "semantic_rules.json", semantic_rules)
    write_source_markdown(output_dir / "source_text.md", pages)
    write_page_texts(output_dir / "pages", pages)

    atomic_validation = validate_artifact_list(output_dir / "atomic_rules.json", validate_atomic_rule)
    semantic_validation = validate_artifact_list(output_dir / "semantic_rules.json", validate_semantic_rule)
    if not atomic_validation["valid"] or not semantic_validation["valid"]:
        raise ValueError(
            "Extracted artifacts failed schema validation: "
            + json.dumps(
                {
                    "atomic": atomic_validation,
                    "semantic": semantic_validation,
                },
                ensure_ascii=False,
            )
        )

    return {
        "metadata": metadata,
        "pages_path": str(output_dir / "pages.json"),
        "atomic_rules_path": str(output_dir / "atomic_rules.json"),
        "semantic_rules_path": str(output_dir / "semantic_rules.json"),
        "atomic_rule_count": len(atomic_rules),
        "semantic_rule_count": len(semantic_rules),
        "sections": [section.section_label for section in sections],
    }


def extract_pages(path: Path) -> list[PageText]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pages_from_pdf(path)
    if suffix in {".md", ".markdown"}:
        return extract_pages_from_markdown(path)
    if suffix == ".docx":
        return extract_pages_from_docx(path)
    raise ValueError(f"Unsupported source format: {suffix}")


def extract_pages_from_pdf(path: Path) -> list[PageText]:
    pypdf_pages = extract_pages_from_pdf_with_pypdf(path)
    if pypdf_pages:
        return pypdf_pages

    executable = find_pdftotext()
    if not executable:
        raise ValueError(
            "PDF extraction requires pypdf or pdftotext. Install pypdf, or set PDFTOTEXT_PATH/install poppler/pdftotext."
        )
    output = run_pdftotext(executable, path)
    raw_pages = output.split("\f")
    pages: list[PageText] = []
    for index, text in enumerate(raw_pages, start=1):
        cleaned = clean_page_text(text)
        if cleaned:
            pages.append(PageText(page_number=index, text=cleaned))
    return pages


def extract_pages_from_pdf_with_pypdf(path: Path) -> list[PageText]:
    """Extract page text from a PDF with pypdf when available.

    The rule workflow GUI should not require a local Poppler installation for
    the committed HKv14 POC path. Keep pdftotext as a fallback for environments
    where it produces better layout-preserving text.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    reader = PdfReader(str(path))
    pages: list[PageText] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = clean_page_text(text.replace("\r\n", "\n").replace("\r", "\n"))
        if cleaned:
            pages.append(PageText(page_number=index, text=cleaned))
    return pages


def run_pdftotext(executable: Path, path: Path) -> str:
    """Run pdftotext and decode output without replacing source symbols.

    Poppler on Windows can emit CP1252 bytes for characters such as section
    signs when no explicit encoding is requested. Prefer UTF-8 output, then
    fall back to common single-byte encodings so source anchors remain readable.
    """
    commands = [
        [str(executable), "-enc", "UTF-8", "-layout", str(path), "-"],
        [str(executable), "-layout", str(path), "-"],
    ]
    last_error: Exception | None = None
    for command in commands:
        try:
            result = subprocess.run(command, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            last_error = exc
            continue
        return fix_pdf_text_artifacts(decode_pdf_text_output(result.stdout))
    if last_error:
        raise last_error
    raise ValueError("pdftotext did not produce output.")


def decode_pdf_text_output(raw: bytes) -> str:
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def fix_pdf_text_artifacts(text: str) -> str:
    return re.sub(r"[\ufffd\u222b](?=\d+(?:\.\d+)+)", "\u00a7", text)


def find_pdftotext() -> Path | None:
    env_path = os.environ.get("PDFTOTEXT_PATH")
    candidates = [
        Path(env_path) if env_path else None,
        Path(shutil.which("pdftotext")) if shutil.which("pdftotext") else None,
        Path(r"G:\Develop\Git\mingw64\bin\pdftotext.exe"),
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return None


def extract_pages_from_markdown(path: Path) -> list[PageText]:
    text = path.read_text(encoding="utf-8-sig")
    matches = list(re.finditer(r"^##\s+Page\s+(\d+)\s*$", text, flags=re.MULTILINE))
    if not matches:
        return [PageText(page_number=1, text=clean_page_text(text))]
    pages: list[PageText] = []
    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages.append(PageText(page_number=page_number, text=clean_page_text(text[start:end])))
    return [page for page in pages if page.text]


def extract_pages_from_docx(path: Path) -> list[PageText]:
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    blocks: list[str] = []

    for child in root.findall(".//w:body/*", ns):
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = "".join(node.text or "" for node in child.findall(".//w:t", ns)).strip()
            if text:
                blocks.append(text)
        elif tag == "tbl":
            rows = []
            for row in child.findall(".//w:tr", ns):
                cells = []
                for cell in row.findall("./w:tc", ns):
                    cell_text = " ".join(
                        (node.text or "").strip()
                        for node in cell.findall(".//w:t", ns)
                        if (node.text or "").strip()
                    )
                    cells.append(cell_text)
                if any(cells):
                    rows.append("| " + " | ".join(cells) + " |")
            if rows:
                blocks.extend(rows)
    return [PageText(page_number=1, text=clean_page_text("\n".join(blocks)))]


def clean_page_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped in {"HKSCC - VaR Platform", "Initial Margin Calculation Guide"}:
            continue
        if re.fullmatch(r"Page\s+\d+\s+of\s+\d+", stripped):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def parse_numbered_sections(pages: list[PageText]) -> list[SectionBlock]:
    blocks: list[SectionBlock] = []
    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if not current:
            return
        raw_text = "\n".join(current["lines"]).strip()
        if raw_text:
            blocks.append(
                SectionBlock(
                    section_number=current["section_number"],
                    title=current["title"],
                    start_page=current["start_page"],
                    end_page=current["end_page"],
                    raw_text=raw_text,
                )
            )
        current = None

    for page in pages:
        for line in page.text.splitlines():
            match = SECTION_HEADING_RE.match(line)
            if match and not is_table_of_contents_line(line):
                if page.page_number <= 3:
                    continue
                flush()
                current = {
                    "section_number": match.group(1),
                    "title": normalize_inline_text(match.group(2)),
                    "start_page": page.page_number,
                    "end_page": page.page_number,
                    "lines": [normalize_inline_text(line)],
                }
                continue
            if current:
                current["lines"].append(line.rstrip())
                current["end_page"] = page.page_number
    flush()
    return blocks


def is_table_of_contents_line(line: str) -> bool:
    return bool(re.search(r"\.{5,}\s*\d+\s*$", line))


def normalize_inline_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def select_hkex_sections(blocks: list[SectionBlock], target_sections: set[str]) -> list[SectionBlock]:
    selected = [block for block in blocks if block.section_number in target_sections]
    selected.sort(key=lambda item: [int(part) for part in item.section_number.split(".")])
    return selected


def build_atomic_rule(section: SectionBlock, index: int) -> dict:
    safe_number = section.section_number.replace(".", "_")
    rule_id = f"IMHK-{safe_number}-01"
    source_block_id = f"SRC-{safe_number}"
    return {
        "rule_id": rule_id,
        "paragraph_id": rule_id,
        "clause_id": f"IMHK-{safe_number}",
        "clause_number": section.section_number,
        "section": section.section_label,
        "start_page": section.start_page,
        "end_page": section.end_page,
        "rule_type": "calculation",
        "testability": "testable",
        "split_basis": "hkex_business_section",
        "raw_text": normalize_source_for_rule(section.raw_text),
        "source_block_id": source_block_id,
        "source_text": section.raw_text,
        "source_excerpt": normalize_inline_text(section.raw_text)[:500],
        "business_group": "core_initial_margin_calculation",
        "review_order": index,
    }


def normalize_source_for_rule(text: str) -> str:
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def section_to_clause(section: SectionBlock) -> dict:
    safe_number = section.section_number.replace(".", "_")
    return {
        "clause_id": f"IMHK-{safe_number}",
        "clause_number": section.section_number,
        "section": section.section_label,
        "start_page": section.start_page,
        "end_page": section.end_page,
        "raw_text": normalize_source_for_rule(section.raw_text),
        "source_block_id": f"SRC-{safe_number}",
    }


def enrich_semantic_rule(rule: dict, atomic_rule: dict) -> dict:
    rule["source"]["section"] = atomic_rule["section"]
    rule["source"]["source_block_id"] = atomic_rule["source_block_id"]
    rule["source"]["source_excerpt"] = atomic_rule["source_excerpt"]
    rule["source"]["paragraph_ids"] = [atomic_rule["paragraph_id"]]
    rule["classification"]["rule_tags"] = [
        "hkex",
        "initial_margin",
        "calculation_guide",
        "core_calculation",
    ]
    rule["statement"]["actor"] = {"value": "clearing_participant", "source_type": "normalized"}
    rule["statement"]["object"] = {"value": "initial_margin_requirement", "source_type": "normalized"}
    rule["type_payload"]["calculation"]["calculation_kind"] = "initial_margin_core_calculation"
    rule["type_payload"]["calculation"]["formula_description"] = atomic_rule["raw_text"]
    rule["type_payload"]["calculation"]["source_section"] = atomic_rule["section"]
    rule["evidence"][0]["quote"] = atomic_rule["raw_text"]
    rule["evidence"][0]["source_block_id"] = atomic_rule["source_block_id"]
    rule["review"]["confidence"] = 0.7
    rule["review"]["inference_flags"] = ["deterministic_hkex_section_extraction"]
    return rule


def write_source_markdown(path: Path, pages: list[PageText]) -> None:
    chunks = [f"## Page {page.page_number}\n\n{page.text}" for page in pages]
    path.write_text("\n\n".join(chunks), encoding="utf-8")


def write_page_texts(path: Path, pages: list[PageText]) -> None:
    ensure_dir(path)
    for page in pages:
        (path / f"page_{page.page_number:03d}.txt").write_text(page.text, encoding="utf-8")


def infer_default_metadata(filename: str) -> dict[str, str]:
    stem = Path(filename).stem
    lowered = stem.lower()
    if "initial margin calculation guide" in lowered and ("hkv14" in lowered or "hk v14" in lowered):
        return {
            "doc_id": "im_hk_v14",
            "doc_title": "Initial Margin Calculation Guide HKv14",
            "doc_version": "HKv14",
        }
    return {
        "doc_id": re.sub(r"[^a-z0-9_]+", "_", lowered).strip("_") or "uploaded_document",
        "doc_title": stem,
        "doc_version": "uploaded",
    }
