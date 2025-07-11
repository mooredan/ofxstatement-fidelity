PROJ := ofxstatement_fidelity


# all: test mypy black

.PHONY: all


all : build install


.PHONY: build
build :
	python3 -m build > build.log


.PHONY: install
install :
	pip install . > install.log


.PHONY: test
test:
	pytest

.PHONY: coverage
coverage: bin/pytest
	pytest --cov src/ofxstatement

.PHONY: black
black:
	black setup.py src tests

.PHONY: mypy
mypy:
	mypy src tests



.PHONY : clean
clean :
	- @ rm -rf build
	- @ rm -rf dist
	rm -rf src/$(PROJ).egg-info
