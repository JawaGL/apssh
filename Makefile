########## for uploading onto pypi
# this assumes you have an entry 'pypi' in your .pypirc
# see pypi documentation on how to create .pypirc

LIBRARY = apssh

VERSION = $(shell python3 -c "from $(LIBRARY).version import version; print(version)")
VERSIONTAG = $(LIBRARY)-$(VERSION)
GIT-TAG-ALREADY-SET = $(shell git tag | grep '^$(VERSIONTAG)$$')
# to check for uncommitted changes
GIT-CHANGES = $(shell echo $$(git diff HEAD | wc -l))

# run this only once the sources are in on the right tag
pypi:
	@if [ $(GIT-CHANGES) != 0 ]; then echo "You have uncommitted changes - cannot publish"; false; fi
	@if [ -n "$(GIT-TAG-ALREADY-SET)" ] ; then echo "tag $(VERSIONTAG) already set"; false; fi
	@if ! grep -q ' $(VERSION)' CHANGELOG.md ; then echo no mention of $(VERSION) in CHANGELOG.md; false; fi
	@echo "You are about to release $(VERSION) - OK (Ctrl-c if not) ? " ; read _
	git tag $(VERSIONTAG)
	./setup.py sdist upload -r pypi

# it can be convenient to define a test entry, say testpypi, in your .pypirc
# that points at the testpypi public site
# no upload to build.onelab.eu is done in this case 
# try it out with
# pip install -i https://testpypi.python.org/pypi $(LIBRARY)
# dependencies need to be managed manually though
testpypi: 
	./setup.py sdist upload -r testpypi

##############################
tags:
	git ls-files | xargs etags

.PHONY: tags

##########
tests:
	python3 tests/tests.py

.PHONY: tests

# actually install
infra:
	apssh -t r2lab.infra pip3 install --upgrade apssh
check:
	apssh -t r2lab.infra apssh --version

.PHONY: infra check


########## sphinx
sphinx:
	$(MAKE) -C sphinx html

sphinx-clean:
	$(MAKE) -C sphinx clean

all-sphinx: readme-clean readme sphinx

.PHONY: sphinx sphinx-clean all-sphinx

########## on r2lab.inria.fr a.k.a. nepi-ng.inria.fr
INFRA-PATH = /root/apssh
PUBLISH-PATH = /var/www/nepi-ng/apssh
EXCLUDES = .git
RSYNC-EXCLUDES = $(foreach exc,$(EXCLUDES), --exclude $(exc))

# invoked by restart-website.sh on r2lab
publish: sphinx
	rsync -av $(RSYNC-EXCLUDES) --delete --delete-excluded ./ $(PUBLISH-PATH)/

infra-doc:
	ssh root@nepi-ng.inria.fr "(cd $(INFRA-PATH); git reset --hard HEAD; git pull; make publish)"

.PHONY: publish infra-doc
