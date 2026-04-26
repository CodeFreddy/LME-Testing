from __future__ import annotations

import argparse
import json
import re
import sys
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

# Ensure local src-layout packages and schemas are importable when run as a script.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from schemas import validate_atomic_rule, validate_artifact_list


HEADER_RE = re.compile(r"LME Matching Rules Version\s+[0-9.]+\s+Page\s+\d+")
PAGE_RE = re.compile(r"LME Matching Rules Version\s+[0-9.]+\s+Page\s+(\d+)")
CLAUSE_START_RE = re.compile(r"(?<![\d:?+\-])([1-9]\d{0,2})\.\s")
LINE_CLAUSE_RE = re.compile(r"^([1-9]\d{0,2})\.\s")
SUBCLAUSE_RE = re.compile(r"\(([a-e])\)\s*", re.IGNORECASE)
PAGE_HEADING_RE = re.compile(r"^##\s+Page\s+(\d+)\s*$", re.MULTILINE)
MD_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


@dataclass
class PageText:
    page_number: int
    text: str


@dataclass
class Clause:
    clause_id: str
    clause_number: str
    section: str | None
    start_page: int
    end_page: int
    raw_text: str


@dataclass
class AtomicRule:
    rule_id: str
    paragraph_id: str
    clause_id: str
    clause_number: str
    section: str | None
    start_page: int
    end_page: int
    rule_type: str
    testability: str
    split_basis: str
    raw_text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract pages, clauses, and atomic rules from LME rule documents."
    )
    parser.add_argument(
        "--document-class",
        choices=["rulebook", "api_spec", "policy", "workflow", "calculation_guide"],
        default="rulebook",
        help="Document class for extraction strategy and rule type inference.",
    )
    parser.add_argument("--input", required=True, help="Path to the source PDF or Markdown file.")
    parser.add_argument(
        "--input-format",
        choices=["auto", "pdf", "md"],
        default="auto",
        help="Explicitly select the input format. Defaults to auto-detection from file suffix.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/matching_rules",
        help="Directory used to store extracted JSON and text artifacts.",
    )
    parser.add_argument(
        "--doc-id",
        default="lme_matching_rules_v2_2",
        help="Stable identifier stored in output metadata.",
    )
    parser.add_argument(
        "--doc-title",
        default="LME Matching Rules",
        help="Document title stored in output metadata.",
    )
    parser.add_argument(
        "--doc-version",
        default="2.2",
        help="Document version stored in output metadata.",
    )
    parser.add_argument(
        "--write-page-text",
        action="store_true",
        help="Write one normalized text file per extracted page.",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip JSON Schema validation of atomic_rules.json after writing.",
    )
    return parser.parse_args()


def detect_input_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".md", ".markdown"}:
        return "md"
    raise ValueError(f"Unsupported input suffix: {suffix}")


def clean_unicode_noise(text: str) -> str:
    replacements = {
        "??ME Rulebook??": '"LME Rulebook"',
        "??ME??": '"LME"',
        "??ailed Checks??": '"Failed Checks"',
        "??rading": '"Trading',
        "Time and Dates??": 'Time and Dates"',
        "??": '"',
        "??": "'s",
        "??": '"a',
        "position??": 'position"',
        "??19:00": "- 19:00",
        "nonelectronically": "non-electronically",
        "nonelectronic": "non-electronic",
        "PostTrade": "Post-Trade",
        "?": "",
        "?": "",
        "?": "-",
        "?": "",
        "?": "",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def decode_pdf_literal(data: bytes) -> str:
    data = (
        data.replace(rb"\\(", b"(")
        .replace(rb"\\)", b")")
        .replace(rb"\\n", b"\n")
        .replace(rb"\\r", b"")
        .replace(rb"\\t", b"\t")
    )
    try:
        return data.decode("latin1")
    except UnicodeDecodeError:
        return data.decode("latin1", errors="ignore")


def normalize_text(text: str) -> str:
    text = clean_unicode_noise(text)
    text = re.sub(r"-\d+", "", text)
    text = re.sub(r"\[\[PAGE:\d+\]\]", " ", text)
    text = re.sub(r"(?<=\w)\s*\(\s*", "(", text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" .", ".").replace(" ,", ",")
    return text.strip()


def mask_times(text: str) -> str:
    return re.sub(r"(\d{1,2}):(\d{2})", r"\1?\2", text)


def unmask_times(text: str) -> str:
    return text.replace("?", ":")


def iter_decompressed_streams(pdf_bytes: bytes) -> Iterable[str]:
    """Yield decompressed text-bearing PDF streams using only the standard library."""
    for match in re.finditer(rb"stream\r?\n", pdf_bytes):
        start = match.end()
        end = pdf_bytes.find(b"endstream", start)
        if end == -1:
            continue
        compressed = pdf_bytes[start:end].strip(b"\r\n")
        try:
            decompressed = zlib.decompress(compressed)
        except zlib.error:
            continue
        chunks = [decode_pdf_literal(raw) for raw in re.findall(rb"\((.*?)\)", decompressed, re.S)]
        text = normalize_text("".join(chunks))
        if text:
            yield text


def extract_pages_from_pdf(pdf_path: Path) -> list[PageText]:
    pages: list[PageText] = []
    seen: set[int] = set()
    for text in iter_decompressed_streams(pdf_path.read_bytes()):
        page_match = PAGE_RE.search(text)
        if not page_match:
            continue
        page_number = int(page_match.group(1))
        if page_number in seen:
            continue
        seen.add(page_number)
        body = HEADER_RE.sub("", text, count=1).strip()
        pages.append(PageText(page_number=page_number, text=body))
    return sorted(pages, key=lambda item: item.page_number)


def normalize_markdown_page_lines(raw_text: str) -> list[str]:
    """Collapse wrapped Markdown lines while preserving headings, bullets, and clauses."""
    raw_text = clean_unicode_noise(raw_text)
    logical_lines: list[str] = []
    for original in raw_text.splitlines():
        line = original.strip()
        if not line or line == "---":
            continue
        if line.startswith("> Source PDF converted") or line.startswith("# LME Matching Rules - Markdown Conversion"):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if line.startswith("## "):
            logical_lines.append(line)
            continue
        if line.startswith("- ") or LINE_CLAUSE_RE.match(line) or re.match(r"^\([a-z]\)\s", line, re.I):
            logical_lines.extend(split_embedded_clause_lines(line))
            continue
        if logical_lines:
            logical_lines[-1] = f"{logical_lines[-1]} {line}".strip()
            expanded = split_embedded_clause_lines(logical_lines[-1])
            if len(expanded) > 1:
                logical_lines = logical_lines[:-1] + expanded
        else:
            logical_lines.extend(split_embedded_clause_lines(line))
    return logical_lines


def split_embedded_clause_lines(line: str) -> list[str]:
    if line.startswith("## "):
        return [line]
    masked = mask_times(line)
    matches = list(CLAUSE_START_RE.finditer(masked))
    if not matches:
        return [line]
    if matches[0].start() != 0:
        return [line]
    if len(matches) == 1:
        return [line]
    parts = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(masked)
        parts.append(unmask_times(masked[start:end].strip()))
    return parts


def extract_pages_from_markdown(md_path: Path) -> list[PageText]:
    text = md_path.read_text(encoding="utf-8")
    matches = list(PAGE_HEADING_RE.finditer(text))
    pages: list[PageText] = []
    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end]
        lines = normalize_markdown_page_lines(body)
        pages.append(PageText(page_number=page_number, text="\n".join(lines)))
    return pages


def build_combined_text(pages: list[PageText]) -> str:
    return " ".join(f"[[PAGE:{page.page_number}]] {page.text}" for page in pages)


def page_range_for_span(combined_text: str, start: int, end: int) -> tuple[int, int]:
    page_markers = list(re.finditer(r"\[\[PAGE:(\d+)\]\]", combined_text))
    start_page = end_page = 0
    for marker in page_markers:
        page_number = int(marker.group(1))
        if marker.start() <= start:
            start_page = page_number
        if marker.start() <= end:
            end_page = page_number
        else:
            break
    return start_page or 1, end_page or start_page or 1


def find_section(text_before_clause: str) -> str | None:
    heading_matches = re.findall(r"##\s+(.+?)\s*$", text_before_clause, re.MULTILINE)
    if heading_matches:
        candidate = heading_matches[-1].strip()
        if not candidate.lower().startswith("page "):
            return candidate
    candidates = re.findall(r"([A-Z][A-Za-z/&\- ]{3,100})\s*$", text_before_clause)
    return candidates[-1].strip() if candidates else None


def split_clauses_from_pdf(pages: list[PageText]) -> list[Clause]:
    combined = build_combined_text(pages)
    masked = mask_times(combined)
    matches = list(CLAUSE_START_RE.finditer(masked))
    clauses: list[Clause] = []
    for index, match in enumerate(matches):
        clause_number = match.group(1)
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(masked)
        raw_text = unmask_times(masked[start:end].strip())
        start_page, end_page = page_range_for_span(combined, start, end)
        section = find_section(combined[max(0, start - 300):start])
        normalized = normalize_text(raw_text)
        if len(normalized) <= len(f"{clause_number}."):
            continue
        clauses.append(
            Clause(
                clause_id=f"MR-{int(clause_number):03d}",
                clause_number=clause_number,
                section=section,
                start_page=start_page,
                end_page=end_page,
                raw_text=normalized,
            )
        )
    return clauses


def split_clauses_from_markdown(pages: list[PageText]) -> list[Clause]:
    """Use Markdown headings and line starts to build cleaner clause boundaries than PDF regex can."""
    clauses: list[Clause] = []
    current_section: str | None = None
    current_clause: dict | None = None

    def flush_current_clause() -> None:
        nonlocal current_clause
        if not current_clause:
            return
        raw_text = normalize_text(" ".join(current_clause["lines"]))
        if raw_text:
            clauses.append(
                Clause(
                    clause_id=f"MR-{int(current_clause['number']):03d}",
                    clause_number=current_clause["number"],
                    section=current_clause["section"],
                    start_page=current_clause["start_page"],
                    end_page=current_clause["end_page"],
                    raw_text=raw_text,
                )
            )
        current_clause = None

    for page in pages:
        for line in page.text.splitlines():
            if line.startswith("## "):
                heading = line[3:].strip()
                if not heading.lower().startswith("page "):
                    current_section = heading
                continue
            clause_match = LINE_CLAUSE_RE.match(line)
            if clause_match:
                flush_current_clause()
                clause_number = clause_match.group(1)
                current_clause = {
                    "number": clause_number,
                    "section": current_section,
                    "start_page": page.page_number,
                    "end_page": page.page_number,
                    "lines": [line],
                }
                continue
            if current_clause is not None:
                current_clause["lines"].append(line)
                current_clause["end_page"] = page.page_number
        if current_clause is not None:
            current_clause["end_page"] = page.page_number
    flush_current_clause()
    return clauses


def guess_rule_type(text: str, document_class: str = "rulebook") -> str:
    """Infer rule type from text content.

    Uses document-class-specific hints when available, otherwise falls back
    to the LME rulebook heuristic chain.
    """
    lowered = text.lower()
    lowered_clean = re.sub(r"^\([a-e]\)\s*", "", lowered, flags=re.IGNORECASE)

    # Import here to avoid circular import at module level
    from document_classes import DocumentClass, infer_rule_type as class_infer

    try:
        doc_cls = DocumentClass(document_class)
        if doc_cls != DocumentClass.RULEBOOK:
            return class_infer(text, doc_cls)
    except ValueError:
        pass  # Unknown class, fall through to rulebook heuristics
    if re.search(r"within\s+\d+\s+(seconds?|minutes?|hours?|days?)", lowered_clean) or "no later than" in lowered_clean or "deadline" in lowered_clean or re.search(r"by\s+\d{1,2}:\d{2}", lowered_clean):
        return "deadline"
    if "must not" in lowered_clean or "shall not" in lowered_clean or "may not" in lowered_clean or "not permitted" in lowered_clean:
        return "prohibition"
    if "will automatically" in lowered_clean or "will be created" in lowered_clean or "will be processed" in lowered_clean or "shall be treated" in lowered_clean:
        return "state_transition"
    if "mean of" in lowered_clean or "weighted average" in lowered_clean or "substitute the correct price" in lowered_clean or "calculate absolute values" in lowered_clean:
        return "calculation"
    if "must be entered as" in lowered_clean or "must include" in lowered_clean or "must contain" in lowered_clean or "may only be executed in" in lowered_clean:
        return "data_constraint"
    if any(marker in lowered_clean for marker in [" is used to ", " for all electronically ", " house, for ", " client, for "]):
        return "enum_definition"
    if lowered_clean.startswith(("cancel ", "reverse ", "submit ")) or "one of the following" in lowered_clean or "either of the following" in lowered_clean or ("(a)" in text and "(b)" in text):
        return "workflow"
    if lowered_clean.startswith(("have been ", "be booked", "be documented")):
        return "obligation"
    if "may only" in lowered_clean:
        return "prohibition"
    if " may " in f" {lowered_clean} " or "permitted" in lowered_clean:
        return "permission"
    if "must" in lowered_clean or "required to" in lowered_clean or "shall" in lowered_clean or "should be entered" in lowered_clean or "must comply" in lowered_clean or "be documented" in lowered_clean:
        return "obligation"
    return "reference_only"


def guess_testability(rule_type: str) -> str:
    if rule_type == "reference_only":
        return "non_testable"
    if rule_type == "enum_definition":
        return "partially_testable"
    return "testable"


def split_subclauses(text: str) -> list[tuple[str, str]]:
    matches = list(SUBCLAUSE_RE.finditer(text))
    if not matches:
        return []
    items: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        label = match.group(1).upper()
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        items.append((label, text[start:end].strip()))
    return items


def split_bullets(text: str) -> list[str]:
    if " - " not in text and "\n- " not in text:
        return []
    pieces = re.split(r"(?:\s|^)\-\s+", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z(\-])", text)
    return [part.strip() for part in parts if part.strip()]


def split_semicolon_items(text: str) -> list[str]:
    """Split long enumerations into smaller requirement-like items."""
    normalized = normalize_text(text)
    normalized = re.sub(r"^\([a-e]\)\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bi\.\s*ii\.\s*iii\.\s*", "", normalized, flags=re.IGNORECASE)
    parts = [part.strip(" ;") for part in re.split(r";\s+", normalized) if part.strip(" ;")]
    if len(parts) <= 1:
        return []
    useful = [part for part in parts if any(token in part.lower() for token in ("must", "may", "shall", "should", "be ", "have been", "will"))]
    return useful if useful else parts


def refine_chunks(chunks: list[str]) -> list[str]:
    refined: list[str] = []
    for chunk in chunks:
        semicolon_items = split_semicolon_items(chunk)
        if semicolon_items:
            refined.extend(semicolon_items)
        else:
            refined.append(chunk.strip())
    return [item for item in refined if item]


def expand_atomic_chunks(clause: Clause, chunks: list[str], split_basis: str, id_prefix: str, document_class: str = "rulebook") -> list[AtomicRule]:
    items: list[AtomicRule] = []
    counter = 1
    for chunk in chunks:
        lowered = chunk.lower()
        if len(chunk.split()) < 3:
            continue
        if not any(token in lowered for token in ("must", "may", "shall", "will", "deadline", "required", "should be", "is used to", "cancel", "reverse", "submit", "enter", "have been", "be booked", "be documented")):
            continue
        rule_id = f"{id_prefix}-{counter:02d}" if id_prefix == clause.clause_id else f"{id_prefix}-{counter}"
        rule_type = guess_rule_type(chunk, document_class=document_class)
        items.append(
            AtomicRule(
                rule_id=rule_id,
                paragraph_id=rule_id,
                clause_id=clause.clause_id,
                clause_number=clause.clause_number,
                section=clause.section,
                start_page=clause.start_page,
                end_page=clause.end_page,
                rule_type=rule_type,
                testability=guess_testability(rule_type),
                split_basis=split_basis,
                raw_text=normalize_text(chunk),
            )
        )
        counter += 1
    if items:
        return items
    fallback_type = guess_rule_type(clause.raw_text, document_class=document_class)
    fallback_rule_id = f"{id_prefix}-01" if id_prefix == clause.clause_id else f"{id_prefix}-1"
    return [
        AtomicRule(
            rule_id=fallback_rule_id,
            paragraph_id=fallback_rule_id,
            clause_id=clause.clause_id,
            clause_number=clause.clause_number,
            section=clause.section,
            start_page=clause.start_page,
            end_page=clause.end_page,
            rule_type=fallback_type,
            testability=guess_testability(fallback_type),
            split_basis=f"{split_basis}:fallback",
            raw_text=normalize_text(clause.raw_text),
        )
    ]


def split_atomic_rules(clause: Clause, document_class: str = "rulebook") -> list[AtomicRule]:
    """Split one clause into deterministic atomic-rule candidates using subclauses, bullets, semicolons, then sentences."""
    subclauses = split_subclauses(clause.raw_text)
    if len(subclauses) > 1:
        items: list[AtomicRule] = []
        for label, chunk in subclauses:
            chunks = refine_chunks(split_sentences(chunk))
            items.extend(
                expand_atomic_chunks(
                    clause=clause,
                    chunks=chunks,
                    split_basis=f"subclause:{label}",
                    id_prefix=f"{clause.clause_id}-{label}",
                    document_class=document_class,
                )
            )
        return items

    bullets = split_bullets(clause.raw_text)
    if len(bullets) > 1:
        items: list[AtomicRule] = []
        for index, bullet in enumerate(bullets, start=1):
            bullet_chunks = refine_chunks(split_sentences(bullet))
            items.extend(
                expand_atomic_chunks(
                    clause=clause,
                    chunks=bullet_chunks,
                    split_basis=f"bullet:{index}",
                    id_prefix=f"{clause.clause_id}-B{index}",
                    document_class=document_class,
                )
            )
        return items

    return expand_atomic_chunks(clause, refine_chunks(split_sentences(clause.raw_text)), "sentence", clause.clause_id, document_class=document_class)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_page_text_files(output_dir: Path, pages: list[PageText]) -> None:
    page_dir = output_dir / "pages"
    page_dir.mkdir(parents=True, exist_ok=True)
    for page in pages:
        filename = page_dir / f"page_{page.page_number:02d}.txt"
        filename.write_text(page.text + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    input_format = detect_input_format(input_path, args.input_format)

    if input_format == "pdf":
        pages = extract_pages_from_pdf(input_path)
        clauses = split_clauses_from_pdf(pages)
    else:
        pages = extract_pages_from_markdown(input_path)
        clauses = split_clauses_from_markdown(pages)
    for clause in clauses:
        if clause.section is None:
            clause.section = args.doc_title

    atomic_rules = [rule for clause in clauses for rule in split_atomic_rules(clause, document_class=args.document_class)]
    metadata = {
        "doc_id": args.doc_id,
        "doc_title": args.doc_title,
        "doc_version": args.doc_version,
        "source_path": str(input_path),
        "source_format": input_format,
        "document_class": args.document_class,
        "page_count": len(pages),
        "clause_count": len(clauses),
        "atomic_rule_count": len(atomic_rules),
    }

    write_json(output_dir / "metadata.json", metadata)
    write_json(output_dir / "pages.json", [asdict(page) for page in pages])
    write_json(output_dir / "clauses.json", [asdict(clause) for clause in clauses])
    atomic_rules_path = output_dir / "atomic_rules.json"
    write_json(atomic_rules_path, [asdict(rule) for rule in atomic_rules])
    if args.write_page_text:
        write_page_text_files(output_dir, pages)

    if not args.skip_validate:
        result = validate_artifact_list(atomic_rules_path, validate_atomic_rule)
        total = result["total"]
        valid = result["valid_count"]
        invalid = result["invalid_count"]
        errors = result.get("errors_by_index") or []
        status = "PASS" if invalid == 0 else "FAIL"
        print(f"[{status}] atomic_rules.json: {total} total, {valid} valid, {invalid} invalid")
        for err in errors[:5]:
            for msg in err["errors"][:2]:
                print(f"  [{err['index']}] {msg}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
        if invalid > 0:
            raise SystemExit(1)

    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

