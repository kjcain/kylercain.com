# Local build via Docker (no LaTeXML needed on the host).
#
#   make build   render posts/*.tex -> site/
#   make serve   build, then serve site/ at http://localhost:8000
#   make image   (re)build the Docker toolchain image
#   make clean   remove generated site/ and build/

IMAGE := latexml-blog
UID    := $(shell id -u)
GID    := $(shell id -g)
DOCKER_RUN := docker run --rm \
	-v "$(CURDIR)":/site -w /site \
	--user $(UID):$(GID) -e HOME=/tmp \
	$(IMAGE)

.PHONY: build serve image clean

image:
	docker build -t $(IMAGE) .

build: image
	$(DOCKER_RUN) python3 -m blog build

serve: build
	@echo "Serving http://localhost:8000  (Ctrl-C to stop)"
	@cd site && python3 -m http.server 8000

clean:
	rm -rf site build logs
