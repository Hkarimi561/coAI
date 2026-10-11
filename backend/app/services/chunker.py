"""Markdown chunker: splits on headings, packs paragraphs up to a size budget and never splits fenced code blocks."""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


@dataclass
class Chunk:
    index: int
    heading: str  # "Title > Section > Subsection"
    text: str


@dataclass
class ParsedDoc:
    title: str
    body: str
    meta: dict[str, str]


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---"):
        return {}, raw
    lines = raw.split("\n")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            meta: dict[str, str] = {}
            for ln in lines[1:i]:
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip("\"'")
            return meta, "\n".join(lines[i + 1:]).lstrip("\n")
    return {}, raw


def parse_document(raw: str, fallback_title: str) -> ParsedDoc:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    meta, body = parse_front_matter(raw)
    title = meta.get("title", "")
    if not title:
        in_fence = False
        for ln in body.split("\n"):
            if _FENCE.match(ln):
                in_fence = not in_fence
            m = None if in_fence else _HEADING.match(ln)
            if m and len(m.group(1)) == 1:
                title = m.group(2).strip()
                break
    return ParsedDoc(title=title or fallback_title, body=body, meta=meta)


def _split_long_text(text: str, max_chars: int) -> list[str]:
    parts: list[str] = []
    cur = ""
    for line in text.split("\n"):
        if cur and len(cur) + len(line) + 1 > max_chars:
            parts.append(cur)
            cur = ""
        cur = f"{cur}\n{line}" if cur else line
    if cur:
        parts.append(cur)
    return parts


def chunk_markdown(body: str, doc_title: str, max_chars: int = 1400) -> list[Chunk]:
    # 1) tokenise into sections of atomic blocks
    sections: list[tuple[list[str], list[tuple[str, str]]]] = []  # (heading_path, [(kind, text)])
    stack: list[tuple[int, str]] = []
    blocks: list[tuple[str, str]] = []
    para: list[str] = []
    code: list[str] = []
    fence: str | None = None

    def current_path() -> list[str]:
        return [h for _, h in stack]

    def flush_para() -> None:
        if para:
            blocks.append(("text", "\n".join(para).strip("\n")))
            para.clear()

    def flush_section() -> None:
        flush_para()
        if blocks:
            sections.append((current_path(), list(blocks)))
            blocks.clear()

    for line in body.split("\n"):
        if fence is not None:
            code.append(line)
            m = _FENCE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and line.strip() == m.group(1):
                blocks.append(("code", "\n".join(code)))
                code.clear()
                fence = None
            continue
        m = _FENCE.match(line)
        if m:
            flush_para()
            fence = m.group(1)
            code.append(line)
            continue
        h = _HEADING.match(line)
        if h:
            flush_section()
            level = len(h.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, h.group(2).strip()))
            continue
        if not line.strip():
            flush_para()
        else:
            para.append(line)
    if fence is not None and code:  # unterminated fence: keep as a single code block
        blocks.append(("code", "\n".join(code)))
    flush_section()

    # 2) pack blocks of each section into chunks
    chunks: list[Chunk] = []

    def emit(path: list[str], text: str) -> None:
        text = text.strip()
        if not text:
            return
        heading = " > ".join([doc_title] + [p for p in path if p != doc_title]) if path else doc_title
        chunks.append(Chunk(index=len(chunks), heading=heading, text=text))

    for path, section_blocks in sections:
        cur = ""
        for kind, text in section_blocks:
            pieces = _split_long_text(text, max_chars) if kind == "text" and len(text) > max_chars else [text]
            for piece in pieces:
                if cur and len(cur) + len(piece) + 2 > max_chars:
                    emit(path, cur)
                    cur = ""
                cur = f"{cur}\n\n{piece}" if cur else piece
        emit(path, cur)
    return chunks
