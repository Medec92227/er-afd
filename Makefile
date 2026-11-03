PYTHON ?= python3
ER ?= (a|b)*abb
CADENA ?= aabb
export ER CADENA

.PHONY: config build run clean test

config:
	$(PYTHON) tools/build.py config

build:
	$(PYTHON) tools/build.py build

run: build
	$(PYTHON) tools/build.py run

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	$(PYTHON) tools/build.py clean
