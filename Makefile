TOC_FILE = gh-md-toc
TOC_HASH = 042fc595336c3a39f82b1edbafdf2afd2503d9930d192fcfda757aa65522c14c
TOC_URL = https://raw.githubusercontent.com/ekalinin/github-markdown-toc/56f7c5939e2119bed86291ddba9fb6c2ee61fb09/gh-md-toc

DEFAULT_TAG = latest
TAG ?= $(DEFAULT_TAG)

FILE_WITH_VERSION = src/modules/constants.py
DOCKER_USER = alling
DOCKER_REPO = userscript-proxy
DOCKER_FULL = $(DOCKER_USER)/$(DOCKER_REPO):$(TAG)
# Can be anything:
CA_VOLUME = mitmproxy-ca
# Needs to match where mitmproxy stores its CA:
CA_DIR = /root/.mitmproxy

.DEFAULT_GOAL := image

docs:
	wget -O $(TOC_FILE) $(TOC_URL)
	# Check that the file hasn't been tampered with:
	echo "$(TOC_HASH) $(TOC_FILE)" | sha256sum -c
	chmod +x $(TOC_FILE)
	# Generate and insert TOC:
	./$(TOC_FILE) --insert README.md
	# Remove files created by gh-md-toc:
	rm README.md.orig.*
	rm README.md.toc.*

image:
	docker build -t $(DOCKER_FULL) .

release: image
ifneq "$(shell git status --porcelain)" ""
	$(error Working directory not clean)
endif
ifeq "$(TAG)" "$(DEFAULT_TAG)"
	$(error Please specify a version (e.g. TAG="1.2.3"))
endif
	# Update in-app version:
	sed -i 's/^VERSION: str = "[^"]*"/VERSION: str = "$(TAG)"/' $(FILE_WITH_VERSION)
	git add $(FILE_WITH_VERSION)
	git commit -m "v$(TAG)"
	git tag "v$(TAG)"

start: image
	docker run -t --rm -p 8080:8080 --name $(DOCKER_REPO) -v "$(CA_VOLUME):$(CA_DIR)" $(DOCKER_FULL)
# The -t flag enables colored output.
