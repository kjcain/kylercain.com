"""Data structures shared by the site builder."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tag:
    name: str
    slug: str

    @property
    def url(self) -> str:
        return f"tags/{self.slug}/"


@dataclass
class Post:
    slug: str
    title_html: str
    title_text: str
    date: str
    author: str
    abstract_html: str
    has_math: bool
    tags: list[Tag] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"posts/{self.slug}/"

    @property
    def pdf_url(self) -> str:
        return f"posts/{self.slug}/post.pdf"

    @property
    def epub_url(self) -> str:
        return f"posts/{self.slug}/post.epub"
