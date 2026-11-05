# Thin front door to scripts/dev.sh so `make <task>` works on macOS, Linux and Git Bash.
# Pass extra arguments with ARGS, e.g. make eval ARGS=--answers.
# On Windows PowerShell use scripts/dev.ps1 instead; both implement the same tasks.

SHELL := bash
TASKS := setup backend frontend dev seed test lint eval clean

.DEFAULT_GOAL := help
.PHONY: help $(TASKS)

help:
	@./scripts/dev.sh help

$(TASKS):
	@./scripts/dev.sh $@ $(ARGS)
