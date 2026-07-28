# Alpine-based toolchain image for building the blog: LaTeXML + Python.
# Used both for local builds (via the Makefile) and in CI (see
# .github/workflows/deploy.yml) so the local and deployed output match.
FROM alpine:3.22

RUN apk add --no-cache \
    build-base \
    ca-certificates \
    db-dev \
    libxml2-dev \
    libxslt-dev \
    make \
    openssl-dev \
    perl \
    perl-app-cpanminus \
    perl-archive-zip \
    perl-clone \
    perl-db_file \
    perl-io-socket-ssl \
    perl-io-string \
    perl-json-xs \
    perl-libwww \
    perl-parse-recdescent \
    perl-pod-parser \
    perl-text-unidecode \
    perl-uri \
    perl-xml-libxml \
    perl-xml-libxslt \
    py3-jinja2 \
    python3 \
    texlive \
    texmf-dist-fontsrecommended \
    texmf-dist-latexextra \
    texmf-dist-latexrecommended \
    texmf-dist-plaingeneric \
    zlib-dev \
    && cpanm --notest --force LaTeXML

# LaTeXML wants a writable HOME for its font/cache scratch; /site is
# bind-mounted at run time and we usually run as the host user, so point
# HOME at a world-writable dir instead of root's home.
ENV HOME=/tmp
WORKDIR /site

CMD ["python3", "-m", "blog", "build"]
