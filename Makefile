# UMOS Makefile for macOS and Linux.
# Targets for development, building, testing, and installation.

UMOS_ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYTHON    ?= python3
PIP       ?= pip3

.PHONY: help install dev build test clean desktop demo mcp cluster

help:
	@echo "UMOS Makefile"
	@echo ""
	@echo "  make install    Install UMOS package (pip install -e .)"
	@echo "  make dev        Install with dev/hw extras"
	@echo "  make build      Build standalone binary (PyInstaller)"
	@echo "  make test       Run all pytest tests"
	@echo "  make desktop    Launch Desktop GUI"
	@echo "  make demo       Run CLI demo"
	@echo "  make mcp        Start MCP server (stdio)"
	@echo "  make cluster    Start distributed cluster node"
	@echo "  make clean      Remove build artifacts"

install:
	$(PIP) install -e .

dev:
	$(PIP) install -e ".[dev,hw]"

build:
	$(PYTHON) build_exe.py

test:
	$(PYTHON) -m pytest tests/ -v

desktop:
	$(PYTHON) gui/app.py

demo:
	$(PYTHON) -m umos_py.demo

mcp:
	$(PYTHON) -m bridge.hermes.mcp_server

cluster:
	$(PYTHON) -m bridge.distributed.node

clean:
	rm -rf build dist *.spec __pycache__ .pytest_cache
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
