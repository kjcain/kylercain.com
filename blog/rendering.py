"""Render posts and generated listing pages."""

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .metadata import extract_metadata, parse_tags
from .models import Post, Tag
from .paths import BUILD_DIR, LOGS_DIR, SITE_DIR, SITE_POSTS_DIR, TEMPLATES_DIR

logger = logging.getLogger(__name__)

HOME_URL = "../../index.html"
POST_BASE = "../../"
STYLE_URL = "../../style.css"
PDFLATEX_PASSES = 2

jinja = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
    trim_blocks=False,
    lstrip_blocks=False,
)
CHROME = jinja.get_template("post_chrome.html.j2").module
MACROS = jinja.get_template("_macros.html.j2").module


def run_command(cmd: list[str], log_path: Path, *, cwd: Path | None = None) -> None:
    """Run a compiler command and append its diagnostics to a log file."""
    logger.debug("Running: %s", " ".join(cmd))
    process = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    output = (process.stdout or "") + (process.stderr or "")
    if output.strip():
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"\n=== console output: {' '.join(cmd)} ===\n{output}\n")
    if process.returncode != 0:
        raise RuntimeError(
            f"command failed: {cmd[0]} (see {log_path.relative_to(SITE_DIR.parent)})"
        )


def render_post(tex_path: Path, site_title: str) -> Post:
    """Render a TeX source into a published HTML page and PDF."""
    slug = tex_path.stem
    tags = parse_tags(tex_path)
    xml_path = BUILD_DIR / f"{slug}.xml"
    pdf_build_dir = BUILD_DIR / "pdf" / slug
    output_dir = SITE_POSTS_DIR / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "index.html"
    pdf_path = output_dir / "post.pdf"

    pdf_build_dir.mkdir(parents=True, exist_ok=True)
    pdflatex_command = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={pdf_build_dir}",
        "-jobname=post",
        tex_path.name,
    ]
    for pass_number in range(1, PDFLATEX_PASSES + 1):
        logger.info(
            "pdflatex %s (pass %d/%d)",
            tex_path.relative_to(SITE_DIR.parent),
            pass_number,
            PDFLATEX_PASSES,
        )
        run_command(
            pdflatex_command,
            LOGS_DIR / f"{slug}.pdflatex.log",
            cwd=tex_path.parent,
        )
    shutil.copy(pdf_build_dir / "post.pdf", pdf_path)

    logger.info("latexml %s", tex_path.relative_to(SITE_DIR.parent))
    run_command(
        [
            "latexml",
            # Without this, LaTeXML only harvests \RequirePackage lines from our
            # own .sty theme files and discards the rest, so any macro they
            # define is undefined in the HTML build.
            "--includestyles",
            f"--dest={xml_path}",
            f"--log={LOGS_DIR / f'{slug}.latexml.log'}",
            str(tex_path),
        ],
        LOGS_DIR / f"{slug}.latexml.log",
    )

    logger.info("latexmlpost %s/index.html", slug)
    run_command(
        [
            "latexmlpost",
            "--format=html5",
            "--pmml",
            f"--dest={html_path}",
            f"--log={LOGS_DIR / f'{slug}.latexmlpost.log'}",
            str(xml_path),
        ],
        LOGS_DIR / f"{slug}.latexmlpost.log",
    )

    inject_chrome(html_path, site_title, tags)
    post = extract_metadata(xml_path, slug)
    post.tags = tags
    return post


def inject_chrome(html_path: Path, site_title: str, tags: list[Tag]) -> None:
    """Add the shared stylesheet, navigation, tag list, and footer."""
    document = html_path.read_text(encoding="utf-8")
    stylesheet = f'<link rel="stylesheet" href="{STYLE_URL}" type="text/css">\n'
    document = document.replace("</head>", stylesheet + "</head>", 1)

    navigation = str(CHROME.nav(HOME_URL, site_title, "post.pdf"))
    footer = str(CHROME.footer(HOME_URL))
    tail = footer
    if tags:
        tail = (
            '<div class="post-tags"><span class="post-tags-label">Tagged</span> '
            + str(MACROS.taglist(tags, POST_BASE))
            + "</div>\n"
            + footer
        )
    document = re.sub(
        r"(<body[^>]*>)",
        lambda match: match.group(1) + "\n" + navigation,
        document,
        count=1,
    )
    document = document.replace("</body>", tail + "\n</body>", 1)
    html_path.write_text(document, encoding="utf-8")


def render_page(template: str, output_path: Path, *, base: str, **context: Any) -> None:
    """Render a Jinja page template to the published site."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    context.setdefault("description", "")
    context.setdefault("needs_math", False)
    document = jinja.get_template(template).render(base=base, **context)
    output_path.write_text(document, encoding="utf-8")


def build_tag_pages(posts: list[Post], config: dict[str, Any]) -> None:
    """Emit one listing page per tag and the tags index."""
    grouped: dict[str, tuple[Tag, list[Post]]] = {}
    for post in posts:
        for tag in post.tags:
            grouped.setdefault(tag.slug, (tag, []))[1].append(post)
    if not grouped:
        return

    site_title = config.get("title", "Blog")
    for slug, (tag, tag_posts) in grouped.items():
        render_page(
            "tag.html.j2",
            SITE_DIR / "tags" / slug / "index.html",
            base="../../",
            site_title=site_title,
            tag=tag,
            posts=tag_posts,
            needs_math=any(post.has_math for post in tag_posts),
        )

    tags = sorted(
        (
            {"name": tag.name, "slug": slug, "count": len(tag_posts)}
            for slug, (tag, tag_posts) in grouped.items()
        ),
        key=lambda tag: tag["name"].lower(),
    )
    render_page(
        "tags_index.html.j2",
        SITE_DIR / "tags" / "index.html",
        base="../",
        site_title=site_title,
        tags=tags,
    )


def build_index(posts: list[Post], config: dict[str, Any], has_tags: bool) -> None:
    """Emit the homepage listing all posts newest first."""
    render_page(
        "index.html.j2",
        SITE_DIR / "index.html",
        base="",
        site_title=config.get("title", "Blog"),
        description=config.get("description", ""),
        posts=posts,
        needs_math=any(post.has_math for post in posts),
        has_tags=has_tags,
    )
