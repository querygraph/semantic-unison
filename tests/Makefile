# Invoke from the repository root. Values are read from the environment by
# Python, never expanded into recipe shell source.
.PHONY: shared-entrypoints shared-sync-controls shared-io-controls inspect-stock inspect-ox inspect-file inspector-reuse-controls
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
shared-io-controls:
	python3 tests/manual.py shared-io-controls
stock-make ox-make stock-dune ox-dune stock-build ox-build cache-storage cache-ownership cache-cli host-interface host-executor read-workers read-cli read-parser sync-functional helper-stock helper-ox validation-cli group-parser interrupted-receipts aggregate-lifecycle aggregate-preflight:
	python3 tests/manual.py $@

.PHONY: dng-private-framing
dng-private-framing:
	python3 tests/manual.py dng-private-framing

.PHONY: private-dng-local-clone
private-dng-local-clone:
	python3 tests/manual.py private-dng-local-clone

.PHONY: dng-private-diagnostic
dng-private-diagnostic:
	python3 tests/manual.py dng-private-diagnostic

.PHONY: private-dng-framing-input
private-dng-framing-input:
	python3 tests/manual.py private-dng-framing-input

.PHONY: sde-conformance
sde-conformance:
	python3 tests/manual.py sde-conformance

.PHONY: stock-check ox-check
stock-check ox-check:
	python3 tests/manual.py $@

.PHONY: stock-dune-check ox-dune-check
stock-dune-check ox-dune-check:
	python3 tests/manual.py $@
