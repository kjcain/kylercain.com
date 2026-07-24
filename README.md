# kylercain.com

A small static publishing system for a personal blog written in LaTeX.
Each post is compiled into both an HTML page and a downloadable PDF, while
Python and Jinja generate the home page, tag archives, and shared navigation.
The finished site is made of static files that can be published directly to
GitHub Pages.

## Features

- Write posts as standalone LaTeX documents.
- Publish HTML through [LaTeXML](https://math.nist.gov/~BMiller/LaTeXML/).
- Publish a PDF from the same source with `pdflatex`.
- Extract each post's title, author, date, and abstract from LaTeXML output.
- Generate per-tag archives and a tag index from a simple LaTeX comment.
- Render post-body mathematics as native MathML.
- Support mathematics in listing titles and abstracts with MathJax.
- Build locally and in CI with the same Docker image.
- Follow the operating system's light or dark color scheme.

## Quick start

The build requires Docker and GNU Make. Serving the generated site with the
included Make target also requires Python 3 on the host.

```sh
make build
make serve
```

Then open <http://localhost:8000>. Stop the server with `Ctrl-C`.

The available Make targets are:

```sh
make image   # build or rebuild the latexml-blog Docker image
make build   # rebuild the image, then generate the complete site
make serve   # build and serve site/ on port 8000
make clean   # remove site/, build/, and logs/
```

Both `make build` and the builder's `build` command begin with a clean build:
existing `site/`, `build/`, and `logs/` directories are removed before new
output is created.

## Writing a post

Create a standalone `.tex` file directly inside `posts/`. Its filename stem is
used unchanged as the URL slug:

```text
posts/2026-07-24-example.tex -> site/posts/2026-07-24-example/
```

A minimal post looks like this:

```latex
\documentclass{article}
\usepackage{base}

\title{An Example Post}
\author{Kyler Cain}
\date{2026-07-24}
% tags: latex, web development

\begin{document}
\maketitle

\begin{abstract}
A short summary displayed on the home page and tag pages.
\end{abstract}

\section{Introduction}

Write the post here.

\end{document}
```

The standard LaTeX metadata commands drive the generated listing pages:

- `\title{}` becomes the linked post title.
- `\author{}` is shown beside the date.
- `\date{}` controls reverse-chronological ordering. ISO `YYYY-MM-DD` dates
  are recommended because the builder sorts date strings lexically.
- The `abstract` environment becomes the listing excerpt.

Missing metadata is allowed. A missing title falls back to the filename stem,
and posts without a date sort after dated posts.

The shared [`posts/base.sty`](posts/base.sty) package currently sets page
margins and configures unobtrusive hyperlinks for the PDF. Other packages can
be loaded normally as long as they are available in the Docker image.

### Tags

Add a comma-separated comment anywhere in the post:

```latex
% tags: security, information theory, math
```

Tag names are normalized into lowercase URL slugs, so `information theory`
becomes `information-theory`. The build adds tag links to each post and listing
card, then generates:

```text
site/tags/index.html
site/tags/information-theory/index.html
```

Empty tag entries are ignored, and duplicate tags within one post are removed
after slug normalization.

## Site configuration

Site-wide metadata lives in [`site.json`](site.json):

```json
{
  "title": "kylercain.com",
  "description": "My personal notes and projects.",
  "author": "Kyler Cain"
}
```

`title` appears in the site header, page titles, and post navigation.
`description` appears below the home-page heading and in its description meta
tag. The current renderer does not consume the `author` field; author names
come from each post's `\author{}` command.

If `site.json` is absent, the builder falls back to default labels. Malformed
JSON stops the build with an error.

## Customizing the site

- Edit [`static/style.css`](static/style.css) for typography, layout, colors,
  and rendered-post styling.
- Edit `templates/` to change the home page, tag pages, cards, navigation, or
  footer.
- Edit [`posts/base.sty`](posts/base.sty) to change shared PDF formatting.
- Add files under `static/` to publish them unchanged at the site root.
- Edit [`Dockerfile`](Dockerfile) when posts require additional TeX packages
  or build dependencies.

## Deploying to GitHub Pages

The included [GitHub Actions workflow](.github/workflows/deploy.yml) builds and
publishes the site on every push to `main`. It can also be run manually with
`workflow_dispatch`.

To enable it:

1. Push the repository to GitHub with `main` as the default branch.
2. Open **Settings → Pages** in the repository.
3. Set **Build and deployment → Source** to **GitHub Actions**.
4. Push a commit or run **Build & deploy blog** from the Actions tab.

The workflow builds the same Dockerfile used locally, uploads `site/` as the
Pages artifact, and deploys it through GitHub's Pages environment.
