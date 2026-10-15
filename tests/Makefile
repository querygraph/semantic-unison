# Invoke from the repository root. Values are read from the environment by
# Python, never expanded into recipe shell source.
.PHONY: help stock-make ox-make stock-dune ox-dune cache-storage cache-ownership cache-cli host-interface host-executor read-workers read-cli read-parser
help:
	python3 tests/manual.py help
stock-make ox-make stock-dune ox-dune cache-storage cache-ownership cache-cli host-interface host-executor read-workers read-cli read-parser:
	python3 tests/manual.py $@
