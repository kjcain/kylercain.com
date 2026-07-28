"""Extract post metadata from TeX sources and LaTeXML XML."""

import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import Post, Tag

LTXML_NS = "http://dlmf.nist.gov/LaTeXML"
TAGS_RE = re.compile(r"^\s*%+\s*tags\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    return slug.strip("-") or "tag"


def parse_tags(tex_path: Path) -> list[Tag]:
    """Read tags from a `% tags: a, b, c` front-matter comment."""
    match = TAGS_RE.search(tex_path.read_text(encoding="utf-8", errors="replace"))
    if not match:
        return []

    tags: list[Tag] = []
    seen: set[str] = set()
    for name in (name.strip() for name in match.group(1).split(",")):
        if not name:
            continue
        slug = slugify(name)
        if slug not in seen:
            seen.add(slug)
            tags.append(Tag(name, slug))
    return tags


def _q(tag: str) -> str:
    return f"{{{LTXML_NS}}}{tag}"


def _node_to_index_html(node: ET.Element) -> tuple[str, bool]:
    """Serialize LaTeXML metadata, retaining inline math for MathJax."""
    parts: list[str] = []
    saw_math = False

    def walk(element: ET.Element) -> None:
        nonlocal saw_math
        for child in element:
            tag = child.tag.split("}")[-1]
            if tag == "Math":
                tex = (child.get("tex") or "").strip()
                if tex:
                    parts.append("\\(" + tex + "\\)")
                    saw_math = True
            elif tag != "tag":
                if child.text:
                    parts.append(html.escape(child.text))
                walk(child)
            if child.tail:
                parts.append(html.escape(child.tail))

    if node.text:
        parts.append(html.escape(node.text))
    walk(node)
    return re.sub(r"\s+", " ", "".join(parts)).strip(), saw_math


def _plain_text(node: ET.Element) -> str:
    """Flatten a LaTeXML node to text, retaining source TeX for math."""
    parts: list[str] = []
    if node.text:
        parts.append(node.text)
    for child in node:
        tag = child.tag.split("}")[-1]
        if tag == "Math":
            parts.append((child.get("tex") or "").strip())
        elif tag != "tag":
            parts.append(_plain_text(child))
        if child.tail:
            parts.append(child.tail)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def extract_metadata(xml_path: Path, slug: str) -> Post:
    """Build a post record from its LaTeXML intermediate XML."""
    root = ET.parse(xml_path).getroot()

    title_element = root.find(_q("title"))
    if title_element is not None:
        title_html, has_title_math = _node_to_index_html(title_element)
        title_text = _plain_text(title_element)
    else:
        title_html, title_text, has_title_math = slug, slug, False

    date_element = root.find(f'{_q("date")}[@role="creation"]')
    if date_element is None:
        date_element = root.find(_q("date"))
    # Not date_element.text: a themed post can wrap the date in a styling
    # element (e.g. a document-wide \color), leaving the text one level down.
    date = _plain_text(date_element) if date_element is not None else ""

    author_element = root.find(f'{_q("creator")}/{_q("personname")}')
    author = _plain_text(author_element) if author_element is not None else ""

    abstract_element = root.find(_q("abstract"))
    if abstract_element is not None:
        abstract_html, has_abstract_math = _node_to_index_html(abstract_element)
    else:
        abstract_html, has_abstract_math = "", False

    return Post(
        slug=slug,
        title_html=title_html or slug,
        title_text=title_text or slug,
        date=date,
        author=author,
        abstract_html=abstract_html,
        has_math=has_title_math or has_abstract_math,
    )
