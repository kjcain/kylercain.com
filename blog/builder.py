"""Build orchestration for the static blog."""

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from .paths import (
    BUILD_DIR,
    CONFIG_FILE,
    LOGS_DIR,
    POSTS_DIR,
    SITE_DIR,
    SITE_POSTS_DIR,
    STATIC_DIR,
)
from .rendering import build_index, build_tag_pages, render_post

logger = logging.getLogger(__name__)


def post_files() -> list[Path]:
    """Return all standalone TeX post sources in name order."""
    if not POSTS_DIR.is_dir():
        return []
    return sorted(path for path in POSTS_DIR.glob("*.tex") if path.is_file())


def clean_outputs() -> None:
    """Remove all generated build output."""
    for directory in (SITE_DIR, BUILD_DIR, LOGS_DIR):
        if directory.exists():
            logger.info("Removing %s", directory.name)
            shutil.rmtree(directory)


def load_config() -> dict[str, Any]:
    """Load site configuration, falling back to an empty configuration."""
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def build_site() -> None:
    """Render all posts and generated listing pages."""
    config = load_config()
    site_title = config.get("title", "Home")

    clean_outputs()
    BUILD_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    SITE_POSTS_DIR.mkdir(parents=True)

    tex_files = post_files()
    logger.info("Rendering %d post(s)", len(tex_files))
    posts = [render_post(tex_path, site_title) for tex_path in tex_files]
    posts.sort(key=lambda post: (post.date or "", post.slug), reverse=True)

    has_tags = any(post.tags for post in posts)
    build_index(posts, config, has_tags)
    build_tag_pages(posts, config)

    if STATIC_DIR.is_dir():
        logger.info("Copying static assets")
        shutil.copytree(STATIC_DIR, SITE_DIR, dirs_exist_ok=True)
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    logger.info("Wrote site/ with %d post(s); logs are in logs/", len(posts))
