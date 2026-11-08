.DEFAULT_GOAL := help
SHELL := bash
.SHELLFLAGS := -euo pipefail -c

.PHONY: help test up down verify evidence

help: ## Show targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

# Each target fails loudly until the project defines it: a silent pass would be a
# gate that checks nothing.
test: ## Project checks (CI's required gate)
	@echo "no tests yet — define 'test' in Makefile"; exit 1

up: ## Start paid resources (live workflow only)
	@echo "not defined for this project"; exit 1

down: ## Tear down and prove nothing tagged remains
	@echo "not defined for this project"; exit 1

verify: ## The runtime check from the idea's "How we'll know it works"
	@echo "not defined yet"; exit 1

evidence: ## Capture proof for the PR
	@echo "not defined yet"; exit 1
