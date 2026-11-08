.DEFAULT_GOAL := help
SHELL := bash
.SHELLFLAGS := -euo pipefail -c

.PHONY: help idea check-idea test lint

help: ## Show targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

idea: ## Start an idea: make idea NAME=spot-price-tracker
	@[[ -n "$(NAME)" ]] || { echo "usage: make idea NAME=<name>"; exit 2; }
	@[[ ! -e ideas/$(NAME).md ]] || { echo "ideas/$(NAME).md already exists"; exit 1; }
	@sed 's/^name: my-idea /name: $(NAME) /' ideas/_template.md > ideas/$(NAME).md
	@echo "wrote ideas/$(NAME).md — fill in the five sections, then: make check-idea NAME=$(NAME)"

check-idea: ## Check one idea the way CI will: make check-idea NAME=spot-price-tracker
	@[[ -n "$(NAME)" ]] || { echo "usage: make check-idea NAME=<name>"; exit 2; }
	@python3 scripts/idea.py validate ideas/$(NAME).md

test: ## Unit tests
	@python3 -m unittest discover -s tests

lint: ## Workflow policy + shellcheck (actionlint runs in CI)
	@python3 scripts/check_workflows.py .github/workflows template/.github/workflows
	@shellcheck scripts/*.sh
