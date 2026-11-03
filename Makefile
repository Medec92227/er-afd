PYTHON ?= python3
ER ?= (a|b)*abb
CADENA ?= aabb
export ER CADENA

.PHONY: config build run test metricas web clean

config:
	$(PYTHON) tools/build.py config

build:
	$(PYTHON) tools/build.py build

run: build
	$(PYTHON) tools/build.py run

test:
	$(PYTHON) -m unittest discover -s tests -v

metricas:
	$(PYTHON) -m tests.metricas --output doc/metricas.json

web:
	$(PYTHON) tools/build.py web

clean:
	$(PYTHON) tools/build.py clean
