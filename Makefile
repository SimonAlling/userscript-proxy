TOC_FILE = gh-md-toc
TOC_HASH = 042fc595336c3a39f82b1edbafdf2afd2503d9930d192fcfda757aa65522c14c
TOC_URL = https://raw.githubusercontent.com/ekalinin/github-markdown-toc/56f7c5939e2119bed86291ddba9fb6c2ee61fb09/gh-md-toc

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
	docker build -t userscript-proxy .
