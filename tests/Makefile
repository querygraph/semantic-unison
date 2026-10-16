# Invoke from the repository root. Values are read from the environment by
# Python, never expanded into recipe shell source.
.PHONY: shared-entrypoints shared-sync-controls inspect-stock inspect-ox inspect-file inspector-reuse-controls
.PHONY: help stock-make ox-make stock-dune ox-dune stock-build ox-build cache-storage cache-ownership cache-cli host-interface host-executor read-workers read-cli read-parser sync-functional helper-stock helper-ox validation-cli group-parser interrupted-receipts aggregate-lifecycle aggregate-preflight
help:
	python3 tests/manual.py help
shared-entrypoints:
	python3 tests/manual.py shared-entrypoints
shared-sync-controls:
	python3 tests/manual.py shared-sync-controls
inspect-stock inspect-ox:
	python3 tests/manual.py $@
inspect-file inspector-reuse-controls:
	python3 tests/manual.py $@
stock-make ox-make stock-dune ox-dune stock-build ox-build cache-storage cache-ownership cache-cli host-interface host-executor read-workers read-cli read-parser sync-functional helper-stock helper-ox validation-cli group-parser interrupted-receipts aggregate-lifecycle aggregate-preflight:
	python3 tests/manual.py $@
