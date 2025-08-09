DEFAULT_TAG = latest
TAG ?= $(DEFAULT_TAG)

FILE_WITH_VERSION = src/modules/constants.py
DOCKER_USER = alling
DOCKER_REPO = userscript-proxy
# Can be anything:
CA_VOLUME = mitmproxy-ca
# Needs to match where mitmproxy stores its CA:
CA_DIR = /root/.mitmproxy

.PHONY : all
all: image

image:
	docker build -t $(DOCKER_USER)/$(DOCKER_REPO):$(TAG) .

install: image
	docker image inspect $(DOCKER_USER)/$(DOCKER_REPO):$(TAG) > /dev/null

release:
ifneq "$(shell git status --porcelain)" ""
	$(error Working directory not clean)
endif
ifeq "$(TAG)" "$(DEFAULT_TAG)"
	$(error Please specify a version (e.g. TAG="1.2.3"))
endif
# Update in-app version:
	sed -i 's/^VERSION: str = "[^"]*"/VERSION: str = "$(TAG)"/' $(FILE_WITH_VERSION)
# Update readme version:
	sed -i 's#image: alling/userscript-proxy:.*#image: alling/userscript-proxy:$(TAG)#' README.md
	docker build -t $(DOCKER_USER)/$(DOCKER_REPO):$(TAG) .
	docker tag $(DOCKER_USER)/$(DOCKER_REPO):$(TAG) $(DOCKER_USER)/$(DOCKER_REPO):$(DEFAULT_TAG)
	git add $(FILE_WITH_VERSION) README.md
	git commit -m "v$(TAG)"
	git tag "v$(TAG)"
	echo "Run these commands to push to Docker Hub:\n\n    docker push alling/userscript-proxy:$(TAG)\n    docker push alling/userscript-proxy:$(DEFAULT_TAG)\n"

start: image
# The -t flag enables colored output:
	docker run -t --rm -p 8080:8080 --name $(DOCKER_REPO) -v "$(CA_VOLUME):$(CA_DIR)" $(DOCKER_USER)/$(DOCKER_REPO):$(TAG)
