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


_MDX_EXPORT = re.compile(r"^export\s+const\s+(title|description)\s*=\s*([\"'`])(.*?)\2\s*;?\s*$")
_MDX_STMT = re.compile(r"^(import|export)\s")
_MDX_COMMENT = re.compile(r"\{/\*.*?\*/\}", re.S)
_OPEN, _CLOSE = "{[(", "}])"


def _tag_end(text: str, i: int) -> int:
    """Index just after the JSX tag starting at text[i] ('<'), or -1 if it is not a complete tag.
    Understands nested {}, [], () and quoted strings, so props like rows={[...]} spanning many lines are consumed whole."""
    n, depth, quote, j = len(text), 0, "", i + 1
    while j < n and j - i < 4000:
        ch = text[j]
        if quote:
            if ch == "\\":
                j += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'`":
            quote = ch
        elif ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        elif ch == ">" and depth <= 0:
            return j + 1
        elif ch == "\n" and depth <= 0 and text.startswith("\n", j + 1):
            return -1  # blank line outside any bracket: this was not a tag
        j += 1
    return -1


def _strip_jsx(text: str) -> str:
    """Removes MDX comments and PascalCase component tags (their text content stays); inline code and <div>-style HTML are kept."""
    text = _MDX_COMMENT.sub("", text)
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "`":  # inline code on one line: copy untouched (docs often mention `<Image>` as text)
            j, nl = text.find("`", i + 1), text.find("\n", i + 1)
            if j != -1 and (nl == -1 or j < nl):
                out.append(text[i : j + 1])
                i = j + 1
                continue
        elif c == "<" and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] in "_.")) and i + 1 < n:
            nxt = text[i + 1]
            if nxt.isupper() or (nxt == "/" and i + 2 < n and text[i + 2].isupper()):
                end = _tag_end(text, i)
                if end > 0:
                    i = end
                    continue
        out.append(c)
        i += 1
    return "".join(out)


def _bracket_delta(line: str) -> int:
    return sum(line.count(c) for c in _OPEN) - sum(line.count(c) for c in _CLOSE)


def clean_mdx(raw: str) -> str:
    """Turns an MDX page into plain Markdown: drops import/export statements (also multi-line ones), JSX comments and component
    tags (their text stays) and turns the page title/description (front matter or 'export const title') into a heading.
    Fenced code blocks are left untouched."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    meta, body = parse_front_matter(text)
    blocks: list[tuple[bool, list[str]]] = []  # (is_code, lines)
    cur: list[str] = []
    in_fence = False
    for ln in body.split("\n"):
        if _FENCE.match(ln):
            if not in_fence:
                blocks.append((False, cur))
                cur, in_fence = [ln], True
            else:
                cur.append(ln)
                blocks.append((True, cur))
                cur, in_fence = [], False
            continue
        cur.append(ln)
    if cur:
        blocks.append((in_fence, cur))  # an unterminated fence stays code
    title, description = meta.get("title", ""), meta.get("description", "")
    parts: list[str] = []
    for is_code, lines in blocks:
        if is_code:
            parts.append("\n".join(lines))
            continue
        kept: list[str] = []
        depth = 0  # >0 while inside a multi-line import/export statement
        for ln in lines:
            if depth > 0:
                depth += _bracket_delta(ln)
                continue
            m = _MDX_EXPORT.match(ln.strip())
            if m:
                if m.group(1) == "title":
                    title = title or m.group(3)
                else:
                    description = description or m.group(3)
                continue
            if _MDX_STMT.match(ln):
                depth = max(0, _bracket_delta(ln))
                continue
            kept.append(ln)
        parts.append(_strip_jsx("\n".join(kept)))
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()
    head = (f"# {title}\n\n" + (f"{description}\n\n" if description else "")) if title else ""
    return f"{head}{cleaned}\n"


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
