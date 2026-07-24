"""Repository paths used by the static-site build."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
BUILD_DIR = ROOT / "build"
SITE_DIR = ROOT / "site"
SITE_POSTS_DIR = SITE_DIR / "posts"
LOGS_DIR = ROOT / "logs"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
CONFIG_FILE = ROOT / "site.json"
